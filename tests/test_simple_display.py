#!/usr/bin/env python3
"""简单墨水屏更换测试"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.epaper_driver import create_driver
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    # 配置
    cfg = Config("config.yml")
    setup_logging(cfg)

    # 创建驱动
    driver = create_driver()
    driver.init_display()

    # 创建图像
    img = Image.new('1', (240, 360), 255)
    draw = ImageDraw.Draw(img)

    # 加载字体
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 绘制内容
    draw.rectangle([10, 10, 230, 350], outline=0, width=2)

    title = "AI-RSS Client"
    bbox = font_large.getbbox(title)
    title_x = (240 - (bbox[2] - bbox[0])) // 2
    draw.text((title_x, 50), title, font=font_large, fill=0)

    info = [
        "✓ Project Ready",
        "✓ Driver Working",
        "✓ GPIO Controlled",
        "",
        "Phase 1 Complete",
        "Ready for Phase 2"
    ]

    y = 100
    for line in info:
        draw.text((20, y), line, font=font_small, fill=0)
        y += 20

    time_str = datetime.now().strftime("%H:%M")
    draw.text((20, 320), f"Updated: {time_str}", font=font_small, fill=0)

    # 显示
    logger.info("显示新内容...")
    driver.display_image(img)
    logger.info("✅ 显示完成")

    driver.sleep()


if __name__ == "__main__":
    main()
