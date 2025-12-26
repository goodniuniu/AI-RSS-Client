#!/usr/bin/env python3
"""
字体管理器
统一管理墨水屏显示所需的各种字体资源

功能：
- 支持中英文字体
- 字体回退机制
- 字体缓存优化
- 文本测量辅助方法
"""

import logging
from typing import Optional, Tuple
from PIL import ImageFont
from pathlib import Path

logger = logging.getLogger(__name__)


class FontManager:
    """
    字体资源管理器

    基于 DEVELOPMENT_GUIDE.md 第6.2节实现
    支持中英文字体，自动回退，智能缓存
    """

    def __init__(self, font_file: str, font_file_fallback: str):
        """
        初始化字体管理器

        Args:
            font_file: 主字体文件路径（推荐支持中文的 TTF/TTC 字体）
            font_file_fallback: 回退字体路径
        """
        self.font_file = font_file
        self.font_file_fallback = font_file_fallback

        # 字体缓存: {(font_path, size): font_object}
        self._cache = {}

        # 验证字体文件是否存在
        self._validate_fonts()

    def _validate_fonts(self):
        """验证字体文件是否存在"""
        if not Path(self.font_file).exists():
            logger.warning(f"⚠️  主字体文件不存在: {self.font_file}")
            logger.info(f"📝 将使用回退字体: {self.font_file_fallback}")

        if not Path(self.font_file_fallback).exists():
            logger.warning(f"⚠️  回退字体文件不存在: {self.font_file_fallback}")
            logger.warning("📝 如果字体加载失败，将使用 PIL 默认字体")

    def get_font(self, size: int, prefer_fallback: bool = False) -> ImageFont.FreeTypeFont:
        """
        获取指定大小的字体对象

        Args:
            size: 字体大小（像素）
            prefer_fallback: 是否优先使用回退字体（默认 False）

        Returns:
            ImageFont.FreeTypeFont: 字体对象
        """
        # 选择字体文件
        font_path = self.font_file_fallback if prefer_fallback else self.font_file

        # 检查缓存
        cache_key = (font_path, size)
        if cache_key in self._cache:
            logger.debug(f"从缓存获取字体: {Path(font_path).name} {size}px")
            return self._cache[cache_key]

        # 加载字体
        font = self._load_font(font_path, size)

        # 存入缓存
        if font is not None:
            self._cache[cache_key] = font

        return font

    def get_font_by_name(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """
        根据预设名称获取字体（便捷方法）

        Args:
            font_name: 字体名称 ('title', 'headline', 'summary', 'meta')
            size: 字体大小

        Returns:
            ImageFont.FreeTypeFont: 字体对象
        """
        # 根据名称调整大小
        size_map = {
            'title': int(size * 1.2),
            'headline': int(size * 1.1),
            'summary': size,
            'meta': int(size * 0.8)
        }

        adjusted_size = size_map.get(font_name, size)
        return self.get_font(adjusted_size)

    def _load_font(self, font_path: str, size: int) -> Optional[ImageFont.FreeTypeFont]:
        """
        加载字体文件，支持多级回退

        Args:
            font_path: 字体文件路径
            size: 字体大小

        Returns:
            字体对象，失败返回 None
        """
        # 尝试加载指定字体
        try:
            font = ImageFont.truetype(font_path, size)
            logger.debug(f"✅ 字体加载成功: {Path(font_path).name} {size}px")
            return font
        except OSError as e:
            logger.warning(f"⚠️  字体加载失败: {font_path} - {e}")

            # 如果不是默认字体，尝试加载回退字体
            if font_path != self.font_file_fallback:
                logger.info(f"📝 尝试回退字体: {self.font_file_fallback}")
                try:
                    font = ImageFont.truetype(self.font_file_fallback, size)
                    logger.info(f"✅ 回退字体加载成功: {Path(self.font_file_fallback).name}")
                    return font
                except OSError as e2:
                    logger.warning(f"⚠️  回退字体也失败: {e2}")

            # 最后尝试 PIL 默认字体
            logger.warning("📝 使用 PIL 默认字体（不支持中文）")
            return ImageFont.load_default()

    def measure_text(self, text: str, font: Optional[ImageFont.FreeTypeFont] = None,
                    size: Optional[int] = None) -> Tuple[int, int]:
        """
        测量文本尺寸

        Args:
            text: 要测量的文本
            font: 字体对象（如果为 None，使用 size 参数）
            size: 字体大小（如果 font 为 None）

        Returns:
            (width, height): 文本宽度和高度
        """
        if font is None:
            if size is None:
                size = 16
            font = self.get_font(size)

        # 获取文本边界框
        try:
            # 新版 PIL (>= 10.0.0)
            bbox = font.getbbox(text)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
        except AttributeError:
            # 旧版 PIL
            width, height = font.getsize(text)

        return width, height

    def get_text_width(self, text: str, font: ImageFont.FreeTypeFont) -> int:
        """
        获取文本宽度（便捷方法）

        Args:
            text: 文本内容
            font: 字体对象

        Returns:
            int: 文本宽度（像素）
        """
        return self.measure_text(text, font)[0]

    def get_text_height(self, font: ImageFont.FreeTypeFont) -> int:
        """
        获取字体高度（便捷方法）

        Args:
            font: 字体对象

        Returns:
            int: 字体高度（像素）
        """
        # 使用标准字符测量高度
        _, height = self.measure_text("测试ABC", font)
        return height

    def clear_cache(self):
        """清空字体缓存"""
        self._cache.clear()
        logger.debug("字体缓存已清空")

    def get_cache_info(self) -> dict:
        """获取缓存信息（调试用）"""
        return {
            'cached_fonts': len(self._cache),
            'font_sizes': [size for (_, size) in self._cache.keys()]
        }


def create_font_manager(config) -> FontManager:
    """
    创建字体管理器实例（工厂函数）

    Args:
        config: 配置对象 (Config.display)

    Returns:
        FontManager: 字体管理器实例
    """
    return FontManager(
        font_file=config.font_file,
        font_file_fallback=config.font_file_fallback
    )
