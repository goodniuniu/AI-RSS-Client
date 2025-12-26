#!/usr/bin/env python3
"""
排版引擎
处理墨水屏文本布局、自动换行、截断等

功能：
- 智能自动换行（支持中英文）
- 文本截断和省略
- 布局计算
- 文本块高度计算
"""

import logging
from typing import List, Tuple, Optional
from PIL import ImageFont

logger = logging.getLogger(__name__)


class LayoutEngine:
    """
    布局计算引擎

    基于 DEVELOPMENT_GUIDE.md 第6.3节实现
    专为墨水屏优化，支持中英文混排
    """

    # 省略号符号
    ELLIPSIS = "..."

    def __init__(self, line_spacing: float = 1.2):
        """
        初始化排版引擎

        Args:
            line_spacing: 行距倍数（默认 1.2）
        """
        self.line_spacing = line_spacing

    def wrap_text(self, text: str, font: ImageFont.FreeTypeFont,
                  max_width: int) -> List[str]:
        """
        智能自动换行（支持中英文）

        中文特点：每个字符都是独立的单位，不需要空格分隔
        英文特点：单词为单位，尽量不在单词中间换行

        Args:
            text: 要换行的文本
            font: 字体对象
            max_width: 最大宽度（像素）

        Returns:
            List[str]: 换行后的文本列表
        """
        if not text:
            return []

        # 如果文本很短，不需要换行
        if self._get_text_width(text, font) <= max_width:
            return [text]

        lines = []
        current_line = ""
        current_word = ""  # 用于英文单词累积

        for char in text:
            # 判断字符类型
            if self._is_cjk(char):
                # 中文字符：直接处理
                # 如果有未完成的英文单词，先添加
                if current_word:
                    test_line = current_line + current_word
                    if self._get_text_width(test_line, font) <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = current_word
                    current_word = ""

                # 处理中文字符
                test_line = current_line + char
                if self._get_text_width(test_line, font) <= max_width:
                    current_line = test_line
                else:
                    # 当前行已满，换行
                    if current_line:
                        lines.append(current_line)
                    current_line = char

            elif char.isspace():
                # 空格：作为单词分隔符
                test_line = current_line + current_word + char
                if self._get_text_width(test_line, font) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = current_word + char
                current_word = ""

            else:
                # 英文字符：累积成单词
                current_word += char

        # 处理剩余内容
        if current_word:
            test_line = current_line + current_word
            if self._get_text_width(test_line, font) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = current_word

        if current_line:
            lines.append(current_line)

        return lines

    def truncate_text(self, text: str, font: ImageFont.FreeTypeFont,
                     max_width: int, max_lines: int,
                     add_ellipsis: bool = True) -> str:
        """
        截断文本以适应指定区域

        Args:
            text: 原始文本
            font: 字体对象
            max_width: 最大宽度（像素）
            max_lines: 最大行数
            add_ellipsis: 是否添加省略号

        Returns:
            str: 截断后的文本
        """
        if not text:
            return ""

        # 先换行
        lines = self.wrap_text(text, font, max_width)

        # 如果行数未超限，直接返回
        if len(lines) <= max_lines:
            return "\n".join(lines)

        # 需要截断
        visible_lines = lines[:max_lines]

        if add_ellipsis and max_lines > 0:
            # 处理最后一行，添加省略号
            last_line = visible_lines[-1]

            # 逐步缩短最后一行，直到省略号能放下
            while self._get_text_width(last_line + self.ELLIPSIS, font) > max_width and len(last_line) > 0:
                last_line = last_line[:-1]

            visible_lines[-1] = last_line + self.ELLIPSIS

        return "\n".join(visible_lines)

    def calculate_text_height(self, text: str, font: ImageFont.FreeTypeFont,
                             max_width: int) -> int:
        """
        计算文本块的总高度

        Args:
            text: 文本内容
            font: 字体对象
            max_width: 最大宽度

        Returns:
            int: 文本块总高度（像素）
        """
        if not text:
            return 0

        lines = self.wrap_text(text, font, max_width)
        if not lines:
            return 0

        # 单行高度
        line_height = self._get_font_height(font)

        # 总高度 = 行数 × 行高 × 行距
        total_height = len(lines) * line_height * self.line_spacing

        return int(total_height)

    def calculate_max_lines(self, available_height: int,
                           font: ImageFont.FreeTypeFont) -> int:
        """
        根据可用高度计算最大行数

        Args:
            available_height: 可用高度（像素）
            font: 字体对象

        Returns:
            int: 最大行数
        """
        if available_height <= 0:
            return 0

        line_height = self._get_font_height(font)
        adjusted_line_height = line_height * self.line_spacing

        max_lines = int(available_height / adjusted_line_height)
        return max(1, max_lines)  # 至少1行

    def center_text(self, text: str, font: ImageFont.FreeTypeFont,
                   container_width: int, container_height: int,
                   max_width: Optional[int] = None) -> Tuple[int, int]:
        """
        计算文本居中位置

        Args:
            text: 文本内容
            font: 字体对象
            container_width: 容器宽度
            container_height: 容器高度
            max_width: 文本最大宽度（如果为 None，使用 container_width）

        Returns:
            (x, y): 居中坐标
        """
        if max_width is None:
            max_width = container_width

        # 换行
        lines = self.wrap_text(text, font, max_width)

        # 计算文本块尺寸
        text_width = max(self._get_text_width(line, font) for line in lines) if lines else 0
        text_height = self.calculate_text_height(text, font, max_width)

        # 计算居中位置
        x = int((container_width - text_width) / 2)
        y = int((container_height - text_height) / 2)

        return x, y

    def fit_text_in_area(self, text: str, font: ImageFont.FreeTypeFont,
                        area_width: int, area_height: int,
                        add_ellipsis: bool = True) -> str:
        """
        将文本适配到指定区域（自动截断）

        Args:
            text: 原始文本
            font: 字体对象
            area_width: 区域宽度
            area_height: 区域高度
            add_ellipsis: 是否添加省略号

        Returns:
            str: 适配后的文本
        """
        if not text:
            return ""

        # 计算最大行数
        max_lines = self.calculate_max_lines(area_height, font)

        # 截断文本
        return self.truncate_text(text, font, area_width, max_lines, add_ellipsis)

    # ========== 私有辅助方法 ==========

    @staticmethod
    def _is_cjk(char: str) -> bool:
        """
        判断字符是否为中日韩（CJK）字符

        Args:
            char: 单个字符

        Returns:
            bool: 是否为 CJK 字符
        """
        # CJK 统一表意文字范围
        code = ord(char)

        # CJK Unified Ideographs
        if 0x4E00 <= code <= 0x9FFF:
            return True

        # CJK Extension A
        if 0x3400 <= code <= 0x4DBF:
            return True

        # CJK Extension B-F
        if 0x20000 <= code <= 0x2EBEF:
            return True

        # 全角标点
        if 0xFF00 <= code <= 0xFFEF:
            return True

        return False

    @staticmethod
    def _get_text_width(text: str, font: ImageFont.FreeTypeFont) -> float:
        """
        获取文本宽度（兼容不同 PIL 版本）

        Args:
            text: 文本内容
            font: 字体对象

        Returns:
            float: 文本宽度
        """
        try:
            # 新版 PIL (>= 10.0.0) 推荐使用
            return font.getlength(text)
        except AttributeError:
            # 旧版 PIL
            width, _ = font.getsize(text)
            return float(width)

    @staticmethod
    def _get_font_height(font: ImageFont.FreeTypeFont) -> int:
        """
        获取字体高度（兼容不同 PIL 版本）

        Args:
            font: 字体对象

        Returns:
            int: 字体高度
        """
        try:
            # 新版 PIL
            bbox = font.getbbox("测试ABC")
            return bbox[3] - bbox[1]
        except AttributeError:
            # 旧版 PIL
            _, height = font.getsize("测试ABC")
            return height


def create_layout_engine(line_spacing: float = 1.2) -> LayoutEngine:
    """
    创建排版引擎实例（工厂函数）

    Args:
        line_spacing: 行距倍数

    Returns:
        LayoutEngine: 排版引擎实例
    """
    return LayoutEngine(line_spacing=line_spacing)
