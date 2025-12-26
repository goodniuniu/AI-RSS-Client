#!/usr/bin/env python3
"""
内容渲染器
将文章数据转换为墨水屏图像

功能：
- 新闻卡片渲染
- 智能布局计算
- 自动空间分配
- 支持多种内容类型
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from PIL import Image, ImageDraw

from .fonts import FontManager
from .layout_engine import LayoutEngine

logger = logging.getLogger(__name__)


class ContentRenderer:
    """
    内容渲染器

    基于 DEVELOPMENT_GUIDE.md 第6.4节实现
    将结构化数据转换为墨水屏可显示的图像
    """

    def __init__(self, font_manager: FontManager, layout_engine: LayoutEngine,
                 width: int, height: int, margin: int = 6,
                 title_height: int = 35, footer_height: int = 20):
        """
        初始化渲染器

        Args:
            font_manager: 字体管理器
            layout_engine: 排版引擎
            width: 屏幕宽度
            height: 屏幕高度
            margin: 页边距
            title_height: 标题区域高度
            footer_height: 底部区域高度
        """
        self.fonts = font_manager
        self.layout = layout_engine
        self.width = width
        self.height = height
        self.margin = margin
        self.title_height = title_height
        self.footer_height = footer_height

        # 计算内容区域宽度
        self.content_width = width - (margin * 2)

        logger.debug(f"渲染器初始化: {width}×{height}, 内容宽度: {self.content_width}px")

    def render_news_card(self, article: Dict[str, Any],
                         index: int = 1, total: int = 1) -> Image.Image:
        """
        渲染新闻卡片

        布局结构：
        ┌─────────────────────────┐
        │ Header (黑底白字)        │
        ├─────────────────────────┤
        │                         │
        │ Title (标题)             │
        │                         │
        │ Summary (摘要)           │
        │                         │
        ├─────────────────────────┤
        │ Footer (元数据)          │
        └─────────────────────────┘

        Args:
            article: 文章数据字典，包含:
                - title: 标题
                - summary: 摘要
                - source: 来源
                - published: 发布时间
                - author: 作者（可选）
            index: 当前文章索引
            total: 文章总数

        Returns:
            Image.Image: 渲染后的图像
        """
        # 1. 创建画布（1位模式，1=白，0=黑）
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)

        # 2. 绘制 Header（黑底白字）
        self._draw_header(draw, index, total)

        # 3. 绘制内容区域
        cursor_y = self._draw_title(draw, article, self.title_height + self.margin + 5)

        # 4. 绘制摘要
        self._draw_summary(draw, article, cursor_y + 10)

        # 5. 绘制 Footer
        self._draw_footer(draw, article)

        return image

    def render_simple_page(self, title: str, content: str,
                          footer: Optional[str] = None) -> Image.Image:
        """
        渲染简单页面（用于错误信息、帮助页面等）

        Args:
            title: 页面标题
            content: 页面内容
            footer: 底部文字（可选）

        Returns:
            Image.Image: 渲染后的图像
        """
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)

        # Header
        self._draw_header(draw, title_text=title)

        # 内容
        cursor_y = self.title_height + self.margin + 5
        font = self.fonts.get_font(15)

        lines = self.layout.wrap_text(content, font, self.content_width)
        for line in lines:
            if cursor_y > self.height - self.footer_height - 20:
                break
            draw.text((self.margin, cursor_y), line, font=font, fill=0)
            cursor_y += int(self.layout._get_font_height(font) * self.layout.line_spacing)

        # Footer
        if footer:
            self._draw_footer(draw, {'custom_footer': footer})

        return image

    def _draw_header(self, draw: ImageDraw.Draw,
                    index: int = 0, total: int = 0,
                    title_text: Optional[str] = None) -> int:
        """
        绘制页眉

        Args:
            draw: ImageDraw 对象
            index: 当前索引
            total: 总数
            title_text: 自定义标题（如果提供，忽略 index/total）

        Returns:
            int: 页眉高度
        """
        # 黑色背景
        draw.rectangle([(0, 0), (self.width, self.title_height)], fill=0)

        # 白色文字
        font = self.fonts.get_font_by_name('headline', 16)

        if title_text:
            header_text = title_text
        else:
            header_text = f"AI-RSS | {index}/{total}" if total > 0 else "AI-RSS"

        # 垂直居中
        text_width = self.fonts.get_text_width(header_text, font)
        text_height = self.fonts.get_text_height(font)
        text_x = (self.width - text_width) // 2
        text_y = (self.title_height - text_height) // 2

        draw.text((text_x, text_y), header_text, font=font, fill=255)

        return self.title_height

    def _draw_title(self, draw: ImageDraw.Draw,
                   article: Dict[str, Any], start_y: int) -> int:
        """
        绘制文章标题

        Args:
            draw: ImageDraw 对象
            article: 文章数据
            start_y: 起始 Y 坐标

        Returns:
            int: 绘制后的 Y 坐标
        """
        title = article.get('title', '无标题')
        if not title:
            title = '无标题'

        font = self.fonts.get_font_by_name('title', 18)

        # 自动换行，最多3行
        lines = self.layout.wrap_text(title, font, self.content_width)
        lines = lines[:3]  # 限制最多3行

        cursor_y = start_y
        line_height = self.fonts.get_text_height(font)

        for line in lines:
            draw.text((self.margin, cursor_y), line, font=font, fill=0)
            cursor_y += int(line_height * self.layout.line_spacing)

        # 如果标题被截断，添加省略提示
        if len(lines) == 3 and len(self.layout.wrap_text(title, font, self.content_width)) > 3:
            # 绘制省略号
            draw.text((self.margin, cursor_y), "...", font=font, fill=0)
            cursor_y += int(line_height * self.layout.line_spacing)

        return cursor_y

    def _draw_summary(self, draw: ImageDraw.Draw,
                     article: Dict[str, Any], start_y: int) -> int:
        """
        绘制文章摘要

        Args:
            draw: ImageDraw 对象
            article: 文章数据
            start_y: 起始 Y 坐标

        Returns:
            int: 绘制后的 Y 坐标
        """
        summary = article.get('summary', '')
        if not summary:
            # 如果没有摘要，尝试用其他字段
            summary = article.get('content', '')
            if not summary:
                summary = '暂无摘要'

        font = self.fonts.get_font(15)

        # 计算可用空间
        available_height = self.height - start_y - self.footer_height - self.margin
        max_lines = self.layout.calculate_max_lines(available_height, font)

        # 截断文本以适应空间
        truncated_text = self.layout.truncate_text(
            summary, font, self.content_width, max_lines, add_ellipsis=True
        )

        # 绘制多行文本
        lines = truncated_text.split('\n')
        cursor_y = start_y
        line_height = self.fonts.get_text_height(font)

        for line in lines:
            draw.text((self.margin, cursor_y), line, font=font, fill=0)
            cursor_y += int(line_height * self.layout.line_spacing)

        return cursor_y

    def _draw_footer(self, draw: ImageDraw.Draw,
                    article: Dict[str, Any]) -> None:
        """
        绘制页脚（分割线 + 元数据）

        Args:
            draw: ImageDraw 对象
            article: 文章数据
        """
        footer_y = self.height - self.footer_height

        # 分割线
        draw.line([
            (self.margin, footer_y),
            (self.width - self.margin, footer_y)
        ], fill=0, width=1)

        # 元数据文字
        font = self.fonts.get_font_by_name('meta', 9)

        # 检查是否有自定义 footer
        if 'custom_footer' in article:
            footer_text = article['custom_footer']
        else:
            source = article.get('source', '未知来源')
            published = article.get('published', '')

            # 格式化日期
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    date_str = dt.strftime('%m-%d %H:%M')
                except:
                    date_str = str(published)[:16]  # 截取前16个字符
            else:
                date_str = ''

            footer_text = f"{source}"
            if date_str:
                footer_text += f" • {date_str}"

        # 左对齐
        text_y = footer_y + 4
        draw.text((self.margin, text_y), footer_text, font=font, fill=0)


def create_renderer(config, font_manager: FontManager,
                   layout_engine: LayoutEngine) -> ContentRenderer:
    """
    创建内容渲染器（工厂函数）

    Args:
        config: 配置对象
        font_manager: 字体管理器
        layout_engine: 排版引擎

    Returns:
        ContentRenderer: 渲染器实例
    """
    return ContentRenderer(
        font_manager=font_manager,
        layout_engine=layout_engine,
        width=config.display.width,
        height=config.display.height,
        margin=config.display.margin,
        title_height=config.display.title_height,
        footer_height=config.display.footer_height
    )
