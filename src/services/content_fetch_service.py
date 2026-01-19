"""
Content Fetch Service for AI-RSS-Client
独立的内容获取守护进程
"""

import time
import signal
import logging
from typing import Optional

from ..config import Config
from .content_manager import ContentManager
from ..fetchers import create_client
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ContentFetchService:
    """
    Content Fetch Service - 独立的内容获取守护进程

    职责：
    - 定期检查是否需要获取新内容
    - 从API获取最新文章
    - 更新本地缓存
    - 独立运行，不影响显示服务

    使用场景：
    - 作为独立进程运行
    - 由systemd管理
    - 定期执行内容获取任务
    """

    def __init__(self, config: Config = None, base_url: str = None, api_token: str = None):
        """
        初始化内容获取服务

        Args:
            config: 配置对象（如果不提供，则创建默认配置）
            base_url: API基础URL（覆盖配置）
            api_token: API认证令牌（覆盖配置）
        """
        # 加载配置
        self.config = config or Config()

        # 覆盖配置（如果提供）
        if base_url:
            self.config.api_base_url = base_url

        # 创建API客户端
        self.api_client = create_client(
            base_url=base_url,
            api_token=api_token
        )

        # 创建内容管理器
        self.content_manager = ContentManager(
            api_client=self.api_client,
            max_cached_articles=self.config.services.max_cached_articles,
            batch_size=self.config.services.max_articles_per_fetch,
            fetch_interval_minutes=self.config.services.interval_minutes,
            display_days=self.config.display_scheduler.display_days
        )

        # 服务状态
        self.running = False
        self.shutdown_requested = False

        # 注册信号处理器
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(f"Content fetch service initialized (interval: {self.config.services.interval_minutes} min)")

    def _signal_handler(self, signum, frame):
        """
        处理系统信号

        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    def fetch_once(self) -> bool:
        """
        执行一次内容获取

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting content fetch cycle...")

            # 检查是否应该获取
            if not self.content_manager.should_fetch():
                logger.info("Not time to fetch yet, skipping")
                return True

            # 根据配置选择获取策略
            if self.config.services.incremental_fetch:
                # 增量获取模式
                success = self.content_manager.fetch_incremental()
            elif self.config.services.fetch_feed_ids:
                # 指定RSS源模式
                success = False
                for feed_id in self.config.services.fetch_feed_ids:
                    if self.content_manager.fetch_by_feed(feed_id):
                        success = True
            else:
                # 默认模式：获取近N天的文章
                success = self.content_manager.fetch_and_process_content(
                    days=self.config.services.fetch_days
                )

            if success:
                stats = self.content_manager.get_status()
                logger.info(f"✓ Content fetch completed: {stats.get('last_fetch_count')} new articles")
            else:
                logger.warning("Content fetch failed")

            return success

        except Exception as e:
            logger.error(f"Content fetch failed: {e}")
            return False

    def run_daemon(self, cycles: int = None):
        """
        运行内容获取守护进程

        Args:
            cycles: 最大运行周期数（None = 无限运行）
        """
        logger.info("Starting content fetch daemon...")
        logger.info(f"Fetch interval: {self.config.services.interval_minutes} minutes")
        logger.info(f"Fetch days: {self.config.services.fetch_days}")

        if cycles:
            logger.info(f"Will run for {cycles} fetch cycles")

        # 启动时执行一次获取
        if not self.shutdown_requested:
            logger.info("Performing initial fetch...")
            self.fetch_once()

        # 主循环
        cycle_count = 0
        self.running = True

        try:
            while self.running and not self.shutdown_requested:
                # 检查周期限制
                if cycles is not None and cycle_count >= cycles:
                    logger.info(f"Completed {cycles} cycles, stopping")
                    break

                # 计算下次获取的时间
                interval_seconds = self.config.services.interval_minutes * 60

                # 等待（使用可中断的sleep）
                logger.info(f"Next fetch in {self.config.services.interval_minutes} minutes...")
                self._interruptible_sleep(interval_seconds)

                # 检查是否收到关闭信号
                if self.shutdown_requested:
                    break

                # 执行获取
                cycle_count += 1
                logger.info(f"Fetch cycle #{cycle_count + 1}")
                self.fetch_once()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")

        except Exception as e:
            logger.error(f"Content fetch daemon crashed: {e}")
            raise

        finally:
            logger.info("Content fetch daemon stopped")
            self.close()

    def _interruptible_sleep(self, seconds: float):
        """
        可中断的睡眠

        Args:
            seconds: 睡眠秒数
        """
        end_time = time.time() + seconds

        while time.time() < end_time:
            if self.shutdown_requested:
                break
            time.sleep(1)  # 每秒检查一次

    def stop(self):
        """
        停止服务（优雅关闭）
        """
        logger.info("Stopping content fetch service...")
        self.running = False
        self.shutdown_requested = True

    def close(self):
        """关闭资源"""
        try:
            if self.content_manager:
                self.content_manager.close()
            logger.info("Content fetch service closed")
        except Exception as e:
            logger.error(f"Error closing service: {e}")

    def get_status(self) -> dict:
        """
        获取服务状态

        Returns:
            状态信息字典
        """
        cm_status = self.content_manager.get_status()

        return {
            'service': 'content_fetch',
            'running': self.running,
            'fetch_interval_minutes': self.config.services.interval_minutes,
            'fetch_days': self.config.services.fetch_days,
            'last_fetch_time': cm_status.get('last_fetch_time'),
            'last_fetch_count': cm_status.get('last_fetch_count'),
            'is_fetching': cm_status.get('is_fetching'),
            'api_connected': cm_status.get('api_connected')
        }

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
