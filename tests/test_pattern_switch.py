#!/usr/bin/env python3
"""
图案切换测试 - 连续显示不同图案以确认墨水屏正常工作
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import time

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.epaper_driver import create_driver
from utils.logger import get_logger

logger = get_logger(__name__)


def create_checkerboard(width, height, box_size=20):
    """创建棋盘格图案"""
    img = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(img)

    for y in range(0, height, box_size):
        for x in range(0, width, box_size):
            if ((x // box_size) + (y // box_size)) % 2 == 0:
                draw.rectangle([x, y, x + box_size, y + box_size], fill=0)

    return img


def create_stripes(width, height, stripe_width=10):
    """创建条纹图案"""
    img = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(img)

    for i in range(0, height, stripe_width * 2):
        draw.rectangle([0, i, width, i + stripe_width], fill=0)

    return img


def create_inverted(width, height):
    """创建反色图案（上半黑下白）"""
    img = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(img)

    mid_y = height // 2
    draw.rectangle([0, 0, width, mid_y], fill=0)

    return img


def main():
    cfg = Config("config.yml")
    setup_logging(cfg)

    logger.info("=" * 60)
    logger.info("图案切换测试")
    logger.info("=" * 60)

    driver = create_driver()
    driver.init_display()

    patterns = [
        ("全黑", Image.new('1', (240, 360), 0)),
        ("全白", Image.new('1', (240, 360), 255)),
        ("棋盘格", create_checkerboard(240, 360)),
        ("条纹", create_stripes(240, 360)),
        ("上下反色", create_inverted(240, 360)),
    ]

    for i, (name, img) in enumerate(patterns):
        logger.info(f"\n[{i+1}/{len(patterns)}] 显示: {name}")
        logger.info("观察墨水屏，按 Enter 继续下一个图案...")

        driver.display_image(img)

        # 保存调试图像
        debug_path = Path(f"data/debug_pattern_{i+1}_{name}.png")
        img.save(debug_path)

        # 等待用户确认
        input()

    driver.sleep()

    logger.info("\n" + "=" * 60)
    logger.info("测试完成！")
    logger.info("如果所有图案都能正确显示，说明墨水屏工作正常")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
