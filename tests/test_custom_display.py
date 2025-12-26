#!/usr/bin/env python3
"""
自定义内容显示测试
显示当前项目信息和状态
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.epaper_driver import EpaperDriver

logger = logging.getLogger(__name__)


def create_project_info_image(width: int = 240, height: int = 360) -> 'Image':
    """
    创建项目信息显示图像

    Args:
        width: 图像宽度
        height: 图像高度

    Returns:
        Image: PIL Image 对象
    """
    # 创建单色图像（白色背景）
    img = Image.new('1', (width, height), 255)  # 255 = 白色
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            22
        )
        font_text = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            14
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            11
        )
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 绘制顶部装饰线
    draw.line([(10, 40), (230, 40)], fill=0, width=2)

    # 标题
    title = "AI-RSS Client"
    bbox = font_title.getbbox(title)
    title_width = bbox[2] - bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 10), title, font=font_title, fill=0)

    # 分隔线
    draw.line([(10, 70), (230, 70)], fill=0, width=1)

    # 信息内容
    info_lines = [
        "Project Status:",
        "",
        "✓ Config module",
        "✓ Logger utility",
        "✓ E-Paper driver",
        "✓ Hardware working",
        "",
        "Display: Custom Test",
        "Mode: Hardware",
        f"Size: {width}x{height}",
        "",
        "Ready for next phase!"
    ]

    y = 85
    for line in info_lines:
        if line.startswith("✓"):
            # 成功标记用加粗
            draw.text((20, y), line, font=font_text, fill=0)
        elif line.endswith(":"):
            # 标题行
            draw.text((20, y), line, font=font_text, fill=0)
        else:
            # 普通文本
            draw.text((20, y), line, font=font_small, fill=0)
        y += 18

    # 底部信息
    draw.line([(10, height - 50), (230, height - 50)], fill=0, width=1)

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((20, height - 40), f"Updated:", font=font_small, fill=0)
    draw.text((20, height - 25), time_str, font=font_small, fill=0)

    return img


def main():
    """主函数"""
    # 加载配置
    cfg = Config("config.yml")
    setup_logging(cfg)

    logger.info("=" * 60)
    logger.info("自定义内容显示")
    logger.info("=" * 60)

    # 创建驱动
    driver = EpaperDriver()
    driver.init_display()

    # 创建项目信息图像
    logger.info("创建项目信息图像...")
    img = create_project_info_image(driver.width, driver.height)

    # 保存调试副本
    debug_path = Path("data/project_info_view.png")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(debug_path)
    logger.info(f"调试图像保存至: {debug_path}")

    # 显示到墨水屏
    logger.info("发送到墨水屏...")
    driver.display_image(img)
    logger.info("✅ 显示成功")

    # 清理
    driver.sleep()

    logger.info("=" * 60)
    logger.info("显示完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    import logging
    main()
