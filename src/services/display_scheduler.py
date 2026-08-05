"""
Display Scheduler for AI-RSS-Client
Handles periodic e-paper display updates
"""

import time
import socket
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ..services.content_manager import ContentManager
from ..display.epaper_driver import EpaperDriver
from ..display.renderer import ContentRenderer
from ..display.fonts import FontManager
from ..display.layout_engine import LayoutEngine
from ..models import Article
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DisplayScheduler:
    """
    Display Scheduler - Manages e-paper display updates

    Responsibilities:
    - Select articles for display
    - Render articles to e-paper format
    - Update e-paper hardware
    - Track display state
    - Handle display errors
    """

    def __init__(self,
                 content_manager: ContentManager = None,
                 display_interval_minutes: float = 0.5,
                 random_on_empty: bool = True,
                 mark_as_read_after_display: bool = False,  # 改为False，支持循环播放
                 health_monitor=None):  # type: ignore
        """
        Initialize display scheduler

        Args:
            content_manager: Content manager instance
            display_interval_minutes: Minutes between display updates
            random_on_empty: Show random articles when all read
            mark_as_read_after_display: Mark articles as read after display
            health_monitor: 后端健康探针（可选），用于在屏幕角标提示后端离线
        """
        self.content_manager = content_manager or ContentManager()
        self.display_interval_minutes = display_interval_minutes
        self.random_on_empty = random_on_empty
        self.mark_as_read_after_display = mark_as_read_after_display
        self.health_monitor = health_monitor

        # Display components
        self.epaper_driver: Optional[EpaperDriver] = None
        self.renderer: Optional[ContentRenderer] = None

        # State tracking
        self.current_article: Optional[Article] = None
        self.display_cycles: int = 0
        self.last_display_time: Optional[datetime] = None
        self.is_displaying: bool = False

        # Get local IP address
        self.ip_address = self._get_local_ip()

        logger.info(f"Display scheduler initialized (interval: {display_interval_minutes} min, IP: {self.ip_address})")

    def _get_local_ip(self) -> Optional[str]:
        """
        获取本地IP地址

        优先获取无线网卡IP（wlan0），如果不存在则获取第一个非本地环回IP

        Returns:
            IP地址字符串，失败返回None
        """
        try:
            # 尝试连接外部地址以获取实际使用的IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                # 连接到不存在的地址，不发送实际数据
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
            except Exception:
                ip = None
            finally:
                s.close()

            if ip:
                logger.debug(f"Detected local IP: {ip}")
                return ip

        except Exception as e:
            logger.warning(f"Failed to detect IP address: {e}")

        # 备用方法：使用hostname命令
        try:
            import subprocess
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                if ips:
                    ip = ips[0]  # 取第一个IP
                    logger.debug(f"Got IP from hostname: {ip}")
                    return ip
        except Exception as e:
            logger.warning(f"Failed to get IP from hostname: {e}")

        logger.warning("Could not determine IP address")
        return None

    def _init_display(self):
        """Initialize display hardware and renderer"""
        if self.epaper_driver is None:
            logger.info("Initializing e-paper driver...")
            self.epaper_driver = EpaperDriver()
            self.epaper_driver.init_display()
            logger.info("E-paper driver initialized")

        if self.renderer is None:
            logger.info("Initializing article renderer...")
            # Create renderer components
            config = Config()
            font_manager = FontManager(
                font_file=config.display.font_file,
                font_file_fallback=config.display.font_file_fallback
            )
            layout_engine = LayoutEngine(line_spacing=1.0)
            self.renderer = ContentRenderer(
                font_manager=font_manager,
                layout_engine=layout_engine,
                width=config.display.width,
                height=config.display.height,
                margin=config.display.margin,
                title_height=config.display.title_height,
                footer_height=config.display.footer_height
            )
            logger.info("Article renderer initialized")

    def update_display(self, save_debug: bool = False) -> bool:
        """
        Update e-paper display with new article

        Args:
            save_debug: Save debug image

        Returns:
            True if display updated successfully
        """
        if self.is_displaying:
            logger.warning("Already displaying, skipping")
            return False

        self.is_displaying = True
        try:
            logger.info("Starting display update cycle")

            # Initialize display if needed
            self._init_display()

            # Get article for display
            article = self.content_manager.get_article_for_display()

            if article is None:
                logger.warning("No articles available for display")
                return False

            # Render article
            logger.info(f"Rendering article: {article.display_title}")
            # Prepare article dict for renderer
            # 使用 feed_name 和 feed_category 构建来源信息
            source_info = article.feed_name if article.feed_name else 'AI-RSS'
            if article.feed_category:
                source_info = f"{article.feed_category}"
            article_dict = {
                'title': article.display_title,
                'summary': article.display_content,
                'summary_en': article.display_content_en,  # English summary for bilingual display
                'source': source_info,
                'published': article.raw_publish_timestamp,
                'feed_name': article.feed_name,  # 额外传递原始 feed 名称
                'feed_category': article.feed_category,  # 额外传递分类
                'qr_code_url': article.qr_code_url,  # 二维码URL
            }
            # 查询后端健康状态（用于在屏幕角标提示离线）
            backend_online = self.health_monitor.is_online if self.health_monitor else True

            # Enable bilingual mode by default to help users learn English
            image = self.renderer.render_news_card(article_dict, index=1, total=1,
                                                   ip_address=self.ip_address, bilingual=True,
                                                   backend_online=backend_online)

            if save_debug:
                debug_path = Path("data") / f"debug_display_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(debug_path)
                logger.info(f"Debug image saved: {debug_path}")

            # Display on e-paper
            logger.info("Sending to e-paper display...")
            self.epaper_driver.display_image(image)
            logger.info("Image displayed successfully")

            # 更新显示时间（始终更新，用于循环播放调度）
            # 即使mark_as_read_after_display=False，也要更新displayed_at以实现轮询
            self.content_manager.mark_as_displayed(article.id)

            # Update state
            self.current_article = article
            self.display_cycles += 1
            self.last_display_time = datetime.now()

            logger.info(f"Display updated successfully (cycle #{self.display_cycles})")
            return True

        except Exception as e:
            logger.error(f"Display update failed: {e}")
            return False

        finally:
            self.is_displaying = False

    def run_once(self) -> bool:
        """
        Run single display update cycle

        Returns:
            True if successful
        """
        return self.update_display()

    def run_daemon(self, cycles: int = None):
        """
        Run display scheduler as daemon

        Args:
            cycles: Maximum number of cycles (None = infinite)
        """
        logger.info("Starting display scheduler daemon")
        logger.info(f"Display interval: {self.display_interval_minutes} minutes")

        if cycles:
            logger.info(f"Will run for {cycles} cycles")

        cycle_count = 0
        try:
            while cycles is None or cycle_count < cycles:
                start_time = time.time()

                # Run display cycle
                self.update_display()

                # Check cycle limit
                cycle_count += 1
                if cycles and cycle_count >= cycles:
                    logger.info(f"Completed {cycles} cycles, stopping")
                    break

                # Calculate sleep time
                cycle_duration = time.time() - start_time
                # 计算下次更新的等待时间（最小5秒，避免过快刷新）
                sleep_time = max(5, (self.display_interval_minutes * 60) - cycle_duration)

                logger.info(f"Next display update in {int(sleep_time)} seconds")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Display scheduler stopped by user")

        except Exception as e:
            logger.error(f"Display scheduler crashed: {e}")
            raise

        finally:
            logger.info("Display scheduler daemon stopped")

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status

        Returns:
            Dict with status information
        """
        content_status = self.content_manager.get_status()

        status = {
            'display_cycles': self.display_cycles,
            'last_display_time': self.last_display_time.isoformat() if self.last_display_time else None,
            'current_article': {
                'id': self.current_article.id,
                'title': self.current_article.display_title,
            } if self.current_article else None,
            'is_displaying': self.is_displaying,
            'display_interval_minutes': self.display_interval_minutes,
            'random_on_empty': self.random_on_empty,
            'mark_as_read_after_display': self.mark_as_read_after_display,
            'hardware_initialized': self.epaper_driver is not None,
            'network_status': 'online' if content_status.get('api_connected') else 'offline',
            'backend_online': self.health_monitor.is_online if self.health_monitor else None,
            'content': {
                'total_summaries': content_status.get('total_summaries', 0),
                'undisplayed_count': content_status.get('undisplayed_count', 0),
            }
        }

        return status

    def test_display(self):
        """Run a display test with sample content"""
        logger.info("Running display test...")

        try:
            # Initialize display
            self._init_display()

            # Create test article
            from ..models import Article
            test_article = Article(
                id=0,
                feed_id=0,
                title="测试显示 - Test Display",
                link="https://example.com/test",
                summary="这是一个测试文章，用于验证墨水屏显示功能。支持中英双语摘要显示。",
                summary_en="This is a test article to verify e-paper display functionality. Supports bilingual summary display.",
                created_at=datetime.now().isoformat()
            )

            # Render and display
            logger.info("Rendering test article...")
            test_article_dict = {
                'title': test_article.display_title,
                'summary': test_article.display_content,
                'summary_en': test_article.display_content_en,
                'source': 'Test',
                'published': test_article.raw_publish_timestamp,
            }
            image = self.renderer.render_news_card(test_article_dict, index=1, total=1,
                                                   ip_address=self.ip_address, bilingual=True,
                                                   backend_online=True)

            logger.info("Displaying on e-paper...")
            self.epaper_driver.display_image(image)

            logger.info("Test display completed successfully")

        except Exception as e:
            logger.error(f"Test display failed: {e}")
            raise

    def close(self):
        """Close and cleanup"""
        if self.epaper_driver:
            try:
                self.epaper_driver.sleep()
                logger.info("E-paper put to sleep")
            except Exception as e:
                logger.warning(f"Failed to sleep e-paper: {e}")

        if self.content_manager:
            self.content_manager.close()

        logger.info("Display scheduler closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
