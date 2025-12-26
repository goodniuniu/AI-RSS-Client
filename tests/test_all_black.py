#!/usr/bin/env python3
"""
全黑屏幕测试
用于确认墨水屏基本显示功能
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.epaper_driver import create_driver
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    cfg = Config("config.yml")
    setup_logging(cfg)

    logger.info("=" * 60)
    logger.info("全黑屏幕测试")
    logger.info("=" * 60)

    driver = create_driver()
    driver.init_display()

    # 创建全黑图像
    logger.info("创建全黑图像...")
    img = Image.new('1', (240, 360), 0)  # 0 = 黑色
    draw = ImageDraw.Draw(img)

    # 加载字体
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()

    # 在黑屏上显示白色大字
    text = "BLACK"
    bbox = font.getbbox(text)
    text_x = (240 - (bbox[2] - bbox[0])) // 2
    text_y = (360 - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), text, font=font, fill=255)  # 白色文字

    logger.info("显示全黑屏幕...")
    driver.display_image(img)
    logger.info("✅ 显示完成")

    # 保存调试副本
    debug_path = Path("data/debug_all_black.png")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(debug_path)
    logger.info(f"调试图像: {debug_path}")

    driver.sleep()

    logger.info("=" * 60)
    logger.info("如果看到黑底白字的'BLACK'，说明显示正常")
    logger.info("如果还是白屏，说明可能有硬件问题")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
