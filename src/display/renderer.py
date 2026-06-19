#!/usr/bin/env python3
"""
内容渲染器
将文章数据转换为墨水屏图像

功能：
- 新闻卡片渲染
- 智能布局计算
- 自动空间分配
- 支持多种内容类型
- 天气信息显示
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
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

        # 天气缓存
        self.weather_data = {}
        self.weather_last_update = None
        self.weather_cache_minutes = 10  # 缓存10分钟

        # 初始化时获取天气
        self._update_weather()

        logger.debug(f"渲染器初始化: {width}×{height}, 内容宽度: {self.content_width}px")

    def render_news_card(self, article: Dict[str, Any],
                         index: int = 1, total: int = 1,
                         ip_address: str = None,
                         bilingual: bool = True) -> Image.Image:
        """
        渲染新闻卡片

        布局结构（双语模式）：
        ┌─────────────────────────┐
        │ Header (黑底白字)        │
        ├─────────────────────────┤
        │ Title (标题)             │
        ├─────────────────────────┤
        │ 中文摘要 (主要内容)       │
        │                         │
        ├─────────────────────────┤
        │ 英文摘要 (学习区域)       │
        │ 1-2行小字               │
        ├─────────────────────────┤
        │ Footer (元数据 + IP)    │
        └─────────────────────────┘

        Args:
            article: 文章数据字典，包含:
                - title: 标题
                - summary: 中文摘要
                - summary_en: 英文摘要（可选）
                - source: 来源
                - published: 发布时间
            index: 当前文章索引
            total: 文章总数
            ip_address: IP地址（显示在右下角）
            bilingual: 是否显示双语（默认True）

        Returns:
            Image.Image: 渲染后的图像
        """
        # 1. 创建画布（1位模式，1=白，0=黑）
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)

        # 2. 绘制 Header（黑底白字）
        self._draw_header(draw, index, total)

        # 3. 绘制标题
        cursor_y = self._draw_title(draw, article, self.title_height + self.margin + 5)

        # 4. 绘制摘要区域
        cursor_y = self._draw_summary_bilingual(draw, article, cursor_y + 10, bilingual=bilingual)

        # 5. 绘制 Footer（包含IP地址）
        self._draw_footer(draw, article, ip_address)

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

    def _update_weather(self) -> bool:
        """
        更新天气信息（带缓存）

        Returns:
            bool: 是否更新成功
        """
        # 检查是否需要更新（缓存有效期）
        if self.weather_last_update:
            elapsed = (datetime.now() - self.weather_last_update).total_seconds() / 60
            if elapsed < self.weather_cache_minutes:
                return True  # 使用缓存

        try:
            # 使用wttr.in API（免费，无需API key）
            url = "https://wttr.in/Guangzhou?format=j1"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # 解析天气数据
            current = data['current_condition'][0]
            self.weather_data = {
                'temp': current['temp_C'],  # 温度
                'desc': current['weatherDesc'][0]['value'],  # 天气描述
                'feels_like': current['FeelsLikeC']  # 体感温度
            }
            self.weather_last_update = datetime.now()

            logger.info(f"天气更新: {self.weather_data['temp']}°C, {self.weather_data['desc']}")
            return True

        except Exception as e:
            logger.warning(f"获取天气失败: {e}")
            # 失败时保持旧数据或返回空
            if not self.weather_data:
                self.weather_data = {'temp': '--', 'desc': '未知', 'feels_like': '--'}
            return False

    def _get_weather_display(self) -> str:
        """
        获取天气显示文本

        Returns:
            str: 格式化的天气信息，如 "16°C 多云"
        """
        # 自动更新天气（如果缓存过期）
        self._update_weather()

        if self.weather_data:
            temp = self.weather_data.get('temp', '--')
            desc = self.weather_data.get('desc', '未知')
            # 简化天气描述
            desc_short = desc.split()[0] if desc else '未知'
            return f"{temp}°C {desc_short}"
        return "--°C 未知"

    def _draw_header(self, draw: ImageDraw.Draw,
                    index: int = 0, total: int = 0,
                    title_text: Optional[str] = None) -> int:
        """
        绘制页眉

        显示实用信息：时间、星期、日期、天气

        Args:
            draw: ImageDraw 对象
            index: 当前索引（已废弃，保留兼容性）
            total: 总数（已废弃，保留兼容性）
            title_text: 自定义标题（如果提供，忽略其他参数）

        Returns:
            int: 页眉高度
        """
        # 黑色背景
        draw.rectangle([(0, 0), (self.width, self.title_height)], fill=0)

        # 白色文字
        font = self.fonts.get_font_by_name('headline', 16)

        # 获取当前时间信息
        now = datetime.now()
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday = weekday_names[now.weekday()]
        time_str = now.strftime('%H:%M')

        # 获取天气信息
        weather_str = self._get_weather_display()

        # 显示格式: "11:30 周一  16°C 多云"
        # 注意：去掉日期以节省空间，显示天气
        header_text = f"{time_str} {weekday}  {weather_str}"

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

        # 降低标题字号到14pt，节省空间
        font = self.fonts.get_font(14)

        # 自动换行，最多2行（降低后可以显示更多字）
        lines = self.layout.wrap_text(title, font, self.content_width)
        lines = lines[:2]  # 限制最多2行

        cursor_y = start_y
        line_height = self.fonts.get_text_height(font)

        for line in lines:
            draw.text((self.margin, cursor_y), line, font=font, fill=0)
            cursor_y += int(line_height * self.layout.line_spacing)

        # 如果标题被截断，添加省略提示
        if len(lines) == 2 and len(self.layout.wrap_text(title, font, self.content_width)) > 2:
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

    def _draw_summary_bilingual(self, draw: ImageDraw.Draw,
                               article: Dict[str, Any],
                               start_y: int,
                               bilingual: bool = True) -> int:
        """
        绘制双语摘要（中文 + 英文）

        最终优化布局：
        - 中文摘要：主要内容，14pt字体，精简显示
        - 分隔线
        - 英文摘要：学习区域，13pt字体，10行（最大化）

        Args:
            draw: ImageDraw 对象
            article: 文章数据
            start_y: 起始 Y 坐标
            bilingual: 是否启用双语模式

        Returns:
            int: 绘制后的 Y 坐标
        """
        # 如果不启用双语，回退到单语模式
        if not bilingual:
            return self._draw_summary(draw, article, start_y)

        cursor_y = start_y

        # 1. 绘制中文摘要（主要内容，精简显示）
        summary_zh = article.get('summary', '')
        if not summary_zh:
            summary_zh = article.get('content', '暂无摘要')

        # 中文字号14pt
        font_zh = self.fonts.get_font(14)

        # 计算中文摘要可用空间（预留大量空间给10行英文）
        # 预留: 分隔线(5px) + 英文区域(130px) + footer
        reserved_space = 5 + 130 + self.footer_height + self.margin
        available_height_zh = self.height - cursor_y - reserved_space
        max_lines_zh = self.layout.calculate_max_lines(available_height_zh, font_zh)

        # 绘制中文摘要
        truncated_zh = self.layout.truncate_text(
            summary_zh, font_zh, self.content_width, max_lines_zh, add_ellipsis=True
        )

        lines_zh = truncated_zh.split('\n')
        line_height_zh = self.fonts.get_text_height(font_zh)

        for line in lines_zh:
            draw.text((self.margin, cursor_y), line, font=font_zh, fill=0)
            cursor_y += int(line_height_zh * self.layout.line_spacing)

        # 2. 绘制分隔线（如果空间足够）
        if cursor_y < self.height - self.footer_height - 130:
            # 增加一点间距
            cursor_y += 3
            draw.line([
                (self.margin, cursor_y),
                (self.width - self.margin, cursor_y)
            ], fill=0, width=1)
            cursor_y += 5

            # 3. 绘制英文摘要（学习区域，16pt，6行）
            summary_en = article.get('summary_en', '')
            if summary_en:
                # 英文字号提升到16pt（更易读）
                font_en = self.fonts.get_font(16)

                # 英文摘要最多显示6行（适应16pt字体）
                available_height_en = self.height - cursor_y - self.footer_height - self.margin
                max_lines_en = min(6, self.layout.calculate_max_lines(available_height_en, font_en))

                truncated_en = self.layout.truncate_text(
                    summary_en, font_en, self.content_width, max_lines_en, add_ellipsis=True
                )

                lines_en = truncated_en.split('\n')
                line_height_en = self.fonts.get_text_height(font_en)

                for line in lines_en:
                    draw.text((self.margin, cursor_y), line, font=font_en, fill=0)
                    cursor_y += int(line_height_en * self.layout.line_spacing)

        return cursor_y

    def _draw_footer(self, draw: ImageDraw.Draw,
                    article: Dict[str, Any],
                    ip_address: str = None) -> None:
        """
        绘制页脚（分割线 + 元数据 + 发布时间 + IP地址）

        Args:
            draw: ImageDraw 对象
            article: 文章数据
            ip_address: IP地址（显示在右下角）
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
            # 优先使用 feed_category（来源分类），其次使用 source
            source_category = article.get('feed_category', '')
            feed_name = article.get('feed_name', '')
            published = article.get('published', '')

            # 格式化日期 - 显示完整时间以便区分新旧
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    # 显示月-日 时:分，更清晰
                    date_str = dt.strftime('%m-%d %H:%M')
                except:
                    date_str = str(published)[:16]  # 截取前16个字符
            else:
                date_str = ''

            # 优先显示时间，其次显示来源分类
            if date_str:
                footer_text = f"{date_str}"
                if source_category:
                    footer_text += f" |{source_category}"
            elif feed_name:
                footer_text += f" |{feed_name}"
            else:
                footer_text = source_category or feed_name or 'AI-NEWS'

        # 左对齐：显示发布时间（主要）和来源（次要）
        text_y = footer_y + 4
        draw.text((self.margin, text_y), footer_text, font=font, fill=0)

        # 右对齐：显示IP地址
        if ip_address:
            # 获取IP地址文本的宽度
            ip_text = f"IP: {ip_address}"
            ip_width = font.getlength(ip_text)

            # 在右下角显示
            x = self.width - self.margin - int(ip_width)
            draw.text((x, text_y), ip_text, font=font, fill=0)


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
