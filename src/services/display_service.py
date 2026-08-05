"""
Display Service for AI-RSS-Client
独立的显示守护进程
"""

import signal
import logging
import time
from typing import Optional

from ..config import Config
from .display_scheduler import DisplayScheduler
from .content_manager import ContentManager
from .health_monitor import BackendHealthMonitor
from ..fetchers import create_client
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DisplayService:
    """
    Display Service - 独立的显示守护进程

    职责：
    - 定期从缓存选择文章
    - 渲染文章到墨水屏
    - 更新硬件显示
    - 独立运行，不负责内容获取

    使用场景：
    - 作为独立进程运行
    - 由systemd管理
    - 定期更新墨水屏显示
    """

    def __init__(self, config: Config = None, base_url: str = None,
                 api_token: str = None, display_interval_minutes: float = 0.5):
        """
        初始化显示服务

        Args:
            config: 配置对象（如果不提供，则创建默认配置）
            base_url: API基础URL（覆盖配置）
            api_token: API认证令牌（覆盖配置）
            display_interval_minutes: 显示更新间隔（分钟）
        """
        # 加载配置
        self.config = config or Config()

        # 覆盖配置（如果提供）
        if base_url:
            self.config.api_base_url = base_url
        if display_interval_minutes:
            self.display_interval_minutes = display_interval_minutes
        else:
            self.display_interval_minutes = self.config.display_scheduler.interval_minutes

        # 创建API客户端（用于访问缓存）
        self.api_client = create_client(
            base_url=base_url,
            api_token=api_token
        )

        # 创建后端健康探针（周期性探测后端可达性，离线时在屏幕角标提示）
        hm_cfg = self.config.health_monitor
        if hm_cfg.enabled:
            self.health_monitor = BackendHealthMonitor(
                base_url=self.api_client.base_url,
                check_interval_seconds=hm_cfg.check_interval_seconds,
                request_timeout_seconds=hm_cfg.request_timeout_seconds,
                failure_threshold=hm_cfg.failure_threshold,
            )
        else:
            self.health_monitor = None

        # 创建内容管理器（只读，用于获取缓存文章）
        self.content_manager = ContentManager(
            api_client=self.api_client,
            max_cached_articles=self.config.services.max_cached_articles,
            batch_size=self.config.services.max_articles_per_fetch,
            fetch_interval_minutes=self.config.services.interval_minutes,
            display_days=self.config.display_scheduler.display_days
        )

        # 创建显示调度器
        self.scheduler = DisplayScheduler(
            content_manager=self.content_manager,
            display_interval_minutes=self.display_interval_minutes,
            random_on_empty=self.config.display_scheduler.random_on_empty,
            mark_as_read_after_display=self.config.display_scheduler.mark_as_read_after_display,
            health_monitor=self.health_monitor
        )

        # 服务状态
        self.running = False
        self.shutdown_requested = False

        # 注册信号处理器
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(f"Display service initialized (interval: {self.display_interval_minutes} min)")

    def _signal_handler(self, signum, frame):
        """
        处理系统信号

        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        # 同时停止调度器
        if self.scheduler:
            self.scheduler.is_displaying = False

    def run_daemon(self, cycles: int = None):
        """
        运行显示守护进程

        Args:
            cycles: 最大显示周期数（None = 无限运行）
        """
        logger.info("Starting display service daemon...")
        logger.info(f"Display interval: {self.display_interval_minutes} minutes")

        if cycles:
            logger.info(f"Will run for {cycles} display cycles")

        # 初始化显示硬件
        try:
            self.scheduler._init_display()
            logger.info("Display hardware initialized")
        except Exception as e:
            logger.error(f"Failed to initialize display hardware: {e}")
            logger.error("Display service will run in headless mode (no hardware updates)")
            # 继续运行，但不更新硬件

        # 启动后端健康监控（后台线程）
        if self.health_monitor:
            self.health_monitor.start()

        # 使用现有的 DisplayScheduler.run_daemon() 逻辑
        # 这里我们重新实现以支持优雅关闭
        cycle_count = 0
        self.running = True

        try:
            while self.running and not self.shutdown_requested:
                # 检查周期限制
                if cycles is not None and cycle_count >= cycles:
                    logger.info(f"Completed {cycles} cycles, stopping")
                    break

                # 执行显示更新
                start_time = time.time()

                try:
                    self.scheduler.update_display()
                    cycle_count += 1
                except Exception as e:
                    logger.error(f"Display update failed: {e}")

                # 检查周期限制
                if cycles and cycle_count >= cycles:
                    logger.info(f"Completed {cycles} cycles, stopping")
                    break

                # 检查关闭信号
                if self.shutdown_requested:
                    break

                # 计算睡眠时间
                cycle_duration = time.time() - start_time
                sleep_time = max(5, (self.display_interval_minutes * 60) - cycle_duration)

                logger.info(f"Next display update in {int(sleep_time)} seconds")

                # 可中断的睡眠
                self._interruptible_sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")

        except Exception as e:
            logger.error(f"Display service crashed: {e}")
            raise

        finally:
            logger.info("Display service daemon stopped")
            self.close()

    def _interruptible_sleep(self, seconds: float):
        """
        可中断的睡眠

        Args:
            seconds: 睡眠秒数
        """
        import time
        end_time = time.time() + seconds

        while time.time() < end_time:
            if self.shutdown_requested:
                break
            time.sleep(1)  # 每秒检查一次

    def run_test_display(self) -> bool:
        """
        运行一次测试显示

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Running test display...")
            self.scheduler._init_display()
            self.scheduler.test_display()
            logger.info("Test display completed")
            return True
        except Exception as e:
            logger.error(f"Test display failed: {e}")
            return False

    def stop(self):
        """
        停止服务（优雅关闭）
        """
        logger.info("Stopping display service...")
        self.running = False
        self.shutdown_requested = True

    def close(self):
        """关闭资源"""
        try:
            if self.health_monitor:
                self.health_monitor.stop()
            if self.scheduler:
                self.scheduler.close()
            if self.content_manager:
                self.content_manager.close()
            logger.info("Display service closed")
        except Exception as e:
            logger.error(f"Error closing service: {e}")

    def get_status(self) -> dict:
        """
        获取服务状态

        Returns:
            状态信息字典
        """
        scheduler_status = self.scheduler.get_status()

        return {
            'service': 'display',
            'running': self.running,
            'display_interval_minutes': self.display_interval_minutes,
            'display_cycles': scheduler_status.get('display_cycles', 0),
            'last_display_time': scheduler_status.get('last_display_time'),
            'current_article': scheduler_status.get('current_article'),
            'hardware_initialized': scheduler_status.get('hardware_initialized', False),
            'backend_health': self.health_monitor.get_status() if self.health_monitor else None,
        }

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
