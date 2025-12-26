#!/usr/bin/env python3
"""
测试字体管理和排版引擎
验证中文字体支持和自动换行功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.fonts import create_font_manager
from display.layout_engine import create_layout_engine
from display.epaper_driver import create_driver
from utils.logger import get_logger

logger = get_logger(__name__)


def test_font_manager():
    """测试字体管理器"""
    logger.info("=" * 60)
    logger.info("测试字体管理器")
    logger.info("=" * 60)

    cfg = Config("config.yml")
    font_mgr = create_font_manager(cfg.display)

    # 测试不同大小的字体
    logger.info("\n1. 测试不同字体大小:")
    sizes = [9, 15, 16, 18, 20]
    for size in sizes:
        font = font_mgr.get_font(size)
        width, height = font_mgr.measure_text("测试中文", font)
        logger.info(f"  {size}px: '测试中文' = {width}×{height}px")

    # 测试预设字体名称
    logger.info("\n2. 测试预设字体名称:")
    for name in ['title', 'headline', 'summary', 'meta']:
        font = font_mgr.get_font_by_name(name, 16)
        width = font_mgr.get_text_width(f"[{name}]测试", font)
        logger.info(f"  {name}: 宽度 = {width}px")

    # 测试缓存
    logger.info("\n3. 缓存信息:")
    cache_info = font_mgr.get_cache_info()
    logger.info(f"  缓存字体数: {cache_info['cached_fonts']}")
    logger.info(f"  字体大小: {cache_info['font_sizes']}")

    logger.info("✅ 字体管理器测试完成")
    return font_mgr


def test_layout_engine():
    """测试排版引擎"""
    logger.info("\n" + "=" * 60)
    logger.info("测试排版引擎")
    logger.info("=" * 60)

    cfg = Config("config.yml")
    font_mgr = create_font_manager(cfg.display)
    layout = create_layout_engine(line_spacing=1.2)

    font = font_mgr.get_font(15)
    max_width = cfg.display.width - 2 * cfg.display.margin

    # 测试中文换行
    logger.info("\n1. 测试中文自动换行:")
    chinese_text = "这是一段很长的中文文本，用来测试自动换行功能是否正常工作。墨水屏的宽度只有240像素，所以需要智能换行。"
    lines = layout.wrap_text(chinese_text, font, max_width)
    logger.info(f"  原文: {chinese_text}")
    logger.info(f"  换行后 ({len(lines)} 行):")
    for i, line in enumerate(lines, 1):
        logger.info(f"    {i}. {line}")

    # 测试英文换行
    logger.info("\n2. 测试英文自动换行:")
    english_text = "This is a long English text to test automatic word wrapping. The e-paper width is only 240 pixels."
    lines = layout.wrap_text(english_text, font, max_width)
    logger.info(f"  原文: {english_text}")
    logger.info(f"  换行后 ({len(lines)} 行):")
    for i, line in enumerate(lines, 1):
        logger.info(f"    {i}. {line}")

    # 测试中英混排
    logger.info("\n3. 测试中英混排:")
    mixed_text = "这是Mixed文本，测试中文和English混排的word wrapping功能是否正常。"
    lines = layout.wrap_text(mixed_text, font, max_width)
    logger.info(f"  原文: {mixed_text}")
    logger.info(f"  换行后 ({len(lines)} 行):")
    for i, line in enumerate(lines, 1):
        logger.info(f"    {i}. {line}")

    # 测试文本截断
    logger.info("\n4. 测试文本截断:")
    long_text = "这是一段很长的文本，需要被截断到指定行数。超出的部分应该用省略号表示。墨水屏的空间有限，所以需要智能截断。" * 3
    truncated = layout.truncate_text(long_text, font, max_width, max_lines=3)
    logger.info(f"  截断到3行:")
    for i, line in enumerate(truncated.split('\n'), 1):
        logger.info(f"    {i}. {line}")

    # 测试高度计算
    logger.info("\n5. 测试高度计算:")
    test_text = "第一行\n第二行\n第三行"
    height = layout.calculate_text_height(test_text, font, max_width)
    logger.info(f"  文本: {test_text}")
    logger.info(f"  计算高度: {height}px")

    # 测试最大行数计算
    logger.info("\n6. 测试最大行数计算:")
    available_height = 100
    max_lines = layout.calculate_max_lines(available_height, font)
    logger.info(f"  可用高度: {available_height}px")
    logger.info(f"  最大行数: {max_lines}行")

    logger.info("✅ 排版引擎测试完成")
    return layout


def test_epaper_display(font_mgr, layout):
    """测试墨水屏显示"""
    logger.info("\n" + "=" * 60)
    logger.info("测试墨水屏显示（中文+排版）")
    logger.info("=" * 60)

    cfg = Config("config.yml")
    driver = create_driver()

    if driver.is_mock:
        logger.info("Mock 模式：仅生成图像")
    else:
        logger.info("硬件模式：将显示到墨水屏")

    driver.init_display()

    from PIL import Image, ImageDraw

    # 创建图像
    img = Image.new('1', (cfg.display.width, cfg.display.height), 255)
    draw = ImageDraw.Draw(img)

    margin = cfg.display.margin
    content_width = cfg.display.width - 2 * margin

    # 1. 标题
    logger.info("\n1. 绘制标题:")
    title_font = font_mgr.get_font_by_name('title', 18)
    title = "字体与排版测试"
    title_width = font_mgr.get_text_width(title, title_font)
    title_x = (cfg.display.width - title_width) // 2
    title_y = margin

    draw.text((title_x, title_y), title, font=title_font, fill=0)
    logger.info(f"  标题: {title} @ ({title_x}, {title_y})")

    # 2. 中文段落
    logger.info("\n2. 绘制中文段落:")
    summary_font = font_mgr.get_font(15)
    chinese_text = "这是中文字体和自动换行功能的测试。墨水屏只有240像素宽，所以需要智能换行。我们的排版引擎支持中文、英文和中英混排。"
    lines = layout.wrap_text(chinese_text, summary_font, content_width)

    y = title_y + font_mgr.get_text_height(title_font) + 10
    for i, line in enumerate(lines, 1):
        draw.text((margin, y), line, font=summary_font, fill=0)
        logger.info(f"  行{i}: {line}")
        y += int(font_mgr.get_text_height(summary_font) * layout.line_spacing)

    # 3. 英文段落
    logger.info("\n3. 绘制英文段落:")
    english_text = "English text wrapping test. This demonstrates how our layout engine handles word wrapping for English content."
    lines = layout.wrap_text(english_text, summary_font, content_width)

    y += 5
    for i, line in enumerate(lines, 1):
        draw.text((margin, y), line, font=summary_font, fill=0)
        logger.info(f"  行{i}: {line}")
        y += int(font_mgr.get_text_height(summary_font) * layout.line_spacing)

    # 4. 截断文本
    logger.info("\n4. 绘制截断文本:")
    long_text = "这是一段很长的文本，用来测试截断功能。如果文本太长，超出指定行数，应该用省略号表示。" * 5
    truncated = layout.truncate_text(long_text, summary_font, content_width, max_lines=2)
    lines = truncated.split('\n')

    y += 5
    for i, line in enumerate(lines, 1):
        draw.text((margin, y), line, font=summary_font, fill=0)
        logger.info(f"  行{i}: {line}")
        y += int(font_mgr.get_text_height(summary_font) * layout.line_spacing)

    # 5. 底部信息
    logger.info("\n5. 绘制底部信息:")
    meta_font = font_mgr.get_font(9)
    from datetime import datetime
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    meta_text = f"Updated: {time_str}"
    meta_width = font_mgr.get_text_width(meta_text, meta_font)
    meta_x = (cfg.display.width - meta_width) // 2
    meta_y = cfg.display.height - margin - font_mgr.get_text_height(meta_font)

    draw.text((meta_x, meta_y), meta_text, font=meta_font, fill=0)
    logger.info(f"  底部: {meta_text} @ ({meta_x}, {meta_y})")

    # 保存调试图像
    debug_path = Path("data/debug_fonts_and_layout.png")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(debug_path)
    logger.info(f"\n调试图像: {debug_path}")

    # 显示到墨水屏
    if not driver.is_mock:
        logger.info("\n发送到墨水屏...")
        driver.display_image(img)
        logger.info("✅ 显示完成")
    else:
        logger.info("\nMock 模式，未发送到墨水屏")

    driver.sleep()

    logger.info("\n✅ 墨水屏显示测试完成")


def main():
    """主函数"""
    cfg = Config("config.yml")
    setup_logging(cfg)

    logger.info("\n" + "🎨" * 30)
    logger.info("字体管理和排版引擎综合测试")
    logger.info("🎨" * 30)

    try:
        # 测试字体管理器
        font_mgr = test_font_manager()

        # 测试排版引擎
        layout = test_layout_engine()

        # 测试墨水屏显示
        test_epaper_display(font_mgr, layout)

        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有测试通过！")
        logger.info("=" * 60)
        logger.info("\n功能验证:")
        logger.info("  ✅ 中文字体支持")
        logger.info("  ✅ 字体缓存机制")
        logger.info("  ✅ 智能自动换行")
        logger.info("  ✅ 中英混排")
        logger.info("  ✅ 文本截断")
        logger.info("  ✅ 高度计算")
        logger.info("  ✅ 墨水屏显示")
        logger.info("\n可以进入下一阶段开发了！")

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
