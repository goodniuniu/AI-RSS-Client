#!/usr/bin/env python3
"""
E-Paper Display Driver
墨水屏驱动封装模块

基于 DEVELOPMENT_GUIDE.md 第3.2节实现
参考项目: epaper-with-ai-news/src/epaper_driver.py

支持功能:
- 硬件驱动和软件模拟(Mock)自动切换
- 硬件冲突检测
- 优雅的错误处理
- 资源自动清理
"""

import sys
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class EpaperDriverError(Exception):
    """墨水屏驱动错误"""
    pass


class EpaperDriver:
    """
    墨水屏驱动封装类

    封装 Waveshare 3.52 英寸墨水屏的硬件操作
    支持硬件模式和软件模拟模式自动切换
    """

    # 默认屏幕分辨率（3.52寸）
    DEFAULT_WIDTH = 240
    DEFAULT_HEIGHT = 360

    def __init__(self, lib_path: Optional[str] = None):
        """
        初始化墨水屏驱动

        Args:
            lib_path: 墨水屏库路径，默认为 "lib/waveshare_epd"
        """
        self.lib_path = Path(lib_path or "lib/waveshare_epd")
        self.epd = None
        self.is_mock = False
        self.is_initialized = False
        self.width = self.DEFAULT_WIDTH
        self.height = self.DEFAULT_HEIGHT

        # 尝试加载硬件驱动
        self._load_hardware_driver()

    def _load_hardware_driver(self):
        """
        加载硬件驱动

        自动检测硬件可用性并切换到 Mock 模式
        """
        try:
            # 添加库路径到 Python 路径
            # 注意：需要添加 lib/ 目录，而不是 lib/waveshare_epd/
            lib_abs_path = self.lib_path.parent.resolve()
            if lib_abs_path.exists():
                sys.path.insert(0, str(lib_abs_path))
                logger.debug(f"添加库路径: {lib_abs_path}")
            else:
                logger.warning(f"库路径不存在: {lib_abs_path}")

            # 导入硬件驱动
            from waveshare_epd import epd3in52

            # 创建驱动实例
            self.epd = epd3in52.EPD()
            self.width = self.epd.width
            self.height = self.epd.height
            self.is_mock = False

            logger.info(f"✅ 硬件驱动加载成功 (Waveshare 3.52\" {self.width}x{self.height})")

        except ImportError as e:
            self.is_mock = True
            logger.warning(f"⚠️  无法导入墨水屏库: {e}")
            logger.info("📝 切换到 Mock 模拟模式（仅生成调试图像）")

        except Exception as e:
            self.is_mock = True
            logger.error(f"❌ 硬件初始化异常: {e}")
            logger.info("📝 切换到 Mock 模拟模式")

    def _check_hardware_conflicts(self) -> bool:
        """
        检查硬件冲突

        基于 DEVELOPMENT_GUIDE.md 实现
        检查是否有其他进程占用 GPIO/SPI 资源

        Returns:
            bool: True 表示无冲突，False 表示有冲突
        """
        if self.is_mock:
            return True  # Mock 模式不需要检查

        try:
            # 检查是否有其他墨水屏服务在运行
            services = [
                "ai-news-content-fetch.service",
                "ai-news-display-scheduler.service",
                "weather-poetry-display.service"
            ]

            for service in services:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout.strip() == "active":
                    logger.warning(f"⚠️  检测到运行中的服务: {service}")
                    logger.warning("⚠️  可能存在 GPIO/SPI 资源冲突")
                    return False

            logger.debug("✅ 硬件冲突检查通过")
            return True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("⚠️  无法检查服务状态（systemctl 不可用）")
            return True
        except Exception as e:
            logger.debug(f"⚠️  硬件冲突检查失败: {e}")
            return True

    def init_display(self) -> bool:
        """
        初始化墨水屏显示器

        重要: Waveshare 3.52寸墨水屏需要完整的初始化序列才能正常显示:
        1. init() - 基本初始化
        2. display_NUM(WHITE) - 清屏到白色
        3. lut_GC() - 加载全刷新查找表
        4. refresh() - 执行刷新
        5. sleep(2) - 等待刷新完成

        参考: test_original_init.py (原有天气诗词程序的初始化方式)
        该序列经过实际硬件验证，缺少任何一步都会导致显示不更新。

        Returns:
            bool: 初始化成功返回 True，失败返回 False

        Raises:
            EpaperDriverError: 如果硬件初始化失败且不在 Mock 模式
        """
        if self.is_mock:
            logger.info("📝 [Mock] 屏幕初始化完成（模拟模式）")
            self.is_initialized = True
            return True

        # 检查硬件冲突
        if not self._check_hardware_conflicts():
            logger.warning("⚠️  检测到硬件冲突，切换到 Mock 模式")
            self.is_mock = True
            self.is_initialized = True
            return True

        try:
            # 完整的初始化序列（基于原有程序验证）
            self.epd.init()
            logger.debug("执行 display_NUM(WHITE) 清屏...")
            self.epd.display_NUM(self.epd.WHITE)
            logger.debug("执行 lut_GC() 加载刷新查找表...")
            self.epd.lut_GC()
            logger.debug("执行 refresh() 强制刷新...")
            self.epd.refresh()
            logger.debug("等待刷新完成（2秒）...")
            time.sleep(2)

            self.is_initialized = True
            logger.info("✅ 硬件屏幕初始化完成（包含完整刷新序列）")
            return True

        except Exception as e:
            logger.error(f"❌ 硬件屏幕初始化失败: {e}")
            self.is_initialized = False
            raise EpaperDriverError(f"墨水屏初始化失败: {e}")

    def display_image(self, image: Image.Image) -> bool:
        """
        显示图像到墨水屏

        Args:
            image: PIL Image 对象（推荐使用 '1' 模式，单色）

        Returns:
            bool: 显示成功返回 True，失败返回 False
        """
        if not self.is_initialized:
            logger.error("❌ 显示器未初始化，请先调用 init_display()")
            return False

        if self.is_mock:
            # Mock 模式：保存图像到本地
            return self._mock_display(image)
        else:
            # 硬件模式：发送到墨水屏
            return self._hardware_display(image)

    def _mock_display(self, image: Image.Image) -> bool:
        """
        Mock 模式显示（保存图像到文件）

        Args:
            image: PIL Image 对象

        Returns:
            bool: 成功返回 True
        """
        try:
            debug_path = Path("data/debug_current_view.png")
            debug_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存为 PNG（无损）
            image.save(debug_path)
            logger.info(f"📝 [Mock] 图像已保存至: {debug_path.absolute()}")
            logger.info("💡 提示: 下载此文件查看显示效果")

            return True

        except Exception as e:
            logger.error(f"❌ [Mock] 保存图像失败: {e}")
            return False

    def _hardware_display(self, image: Image.Image) -> bool:
        """
        硬件模式显示（发送到墨水屏）

        重要：墨水屏需要调用 refresh() 才能真正显示图像
        流程：display() 发送数据 -> refresh() 触发刷新

        Args:
            image: PIL Image 对象

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        try:
            # 转换为墨水屏缓冲区
            buffer = self.epd.getbuffer(image)

            # 发送到屏幕
            self.epd.display(buffer)
            logger.debug("图像数据已发送")

            # 关键：必须调用 refresh() 才能真正显示图像
            self.epd.refresh()
            logger.debug("刷新命令已发送")

            # 等待刷新完成（墨水屏刷新需要时间）
            time.sleep(2)

            logger.info("✅ 图像已显示至墨水屏")
            return True

        except Exception as e:
            logger.error(f"❌ 硬件显示失败: {e}")
            return False

    def clear(self) -> bool:
        """
        清屏（全白）

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        if self.is_mock:
            logger.info("📝 [Mock] 执行清屏")
            return True

        if not self.is_initialized:
            logger.warning("⚠️  显示器未初始化")
            return False

        try:
            self.epd.init()  # 重新初始化以清屏
            # 墨水屏通常有专门的 Clear 方法，但具体看驱动实现
            # 这里我们通过发送全白图像来清屏
            from PIL import Image
            white_image = Image.new('1', (self.width, self.height), 255)
            self.display_image(white_image)

            logger.info("✅ 屏幕已清屏")
            return True

        except Exception as e:
            logger.error(f"❌ 清屏失败: {e}")
            return False

    def sleep(self):
        """
        进入睡眠模式

        重要：墨水屏不使用时应进入睡眠模式以节省功耗
        """
        if self.is_mock:
            logger.info("📝 [Mock] 屏幕进入睡眠模式")
            return

        if self.epd:
            try:
                self.epd.sleep()
                self.is_initialized = False
                logger.info("✅ 硬件屏幕已进入睡眠模式")
            except Exception as e:
                logger.error(f"❌ 睡眠模式设置失败: {e}")

    def __del__(self):
        """
        析构函数 - 确保资源清理

        注意：Python 不保证 __del__ 会被调用
        建议显式调用 sleep() 方法
        """
        try:
            if self.epd and self.is_initialized and not self.is_mock:
                self.sleep()
        except:
            pass  # 析构中忽略所有错误

    def __enter__(self):
        """
        上下文管理器入口
        """
        self.init_display()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口 - 自动清理资源
        """
        self.sleep()
        return False


# 便捷函数
def create_driver(lib_path: Optional[str] = None) -> EpaperDriver:
    """
    创建墨水屏驱动实例

    Args:
        lib_path: 可选的库路径

    Returns:
        EpaperDriver: 驱动实例
    """
    return EpaperDriver(lib_path)
