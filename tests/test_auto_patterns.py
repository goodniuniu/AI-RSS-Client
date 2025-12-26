#!/usr/bin/env python3
"""
自动图案切换测试 - 每3秒自动切换一次图案
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


def main():
    cfg = Config("config.yml")
    setup_logging(cfg)

    logger.info("=" * 60)
    logger.info("自动图案切换测试")
    logger.info("=" * 60)

    driver = create_driver()
    driver.init_display()

    # 定义测试图案
    patterns = [
        ("全黑", Image.new('1', (240, 360), 0)),
        ("全白", Image.new('1', (240, 360), 255)),
    ]

    # 创建更多图案
    # 棋盘格
    img1 = Image.new('1', (240, 360), 255)
    draw1 = ImageDraw.Draw(img1)
    for y in range(0, 360, 20):
        for x in range(0, 240, 20):
            if ((x // 20) + (y // 20)) % 2 == 0:
                draw1.rectangle([x, y, x + 20, y + 20], fill=0)
    patterns.append(("棋盘格", img1))

    # 条纹
    img2 = Image.new('1', (240, 360), 255)
    draw2 = ImageDraw.Draw(img2)
    for i in range(0, 360, 20):
        if (i // 20) % 2 == 0:
            draw2.rectangle([0, i, 240, i + 20], fill=0)
    patterns.append(("条纹", img2))

    # 上下反色
    img3 = Image.new('1', (240, 360), 255)
    draw3 = ImageDraw.Draw(img3)
    draw3.rectangle([0, 0, 240, 180], fill=0)
    patterns.append(("上下反色", img3))

    # 左右反色
    img4 = Image.new('1', (240, 360), 255)
    draw4 = ImageDraw.Draw(img4)
    draw4.rectangle([0, 0, 120, 360], fill=0)
    patterns.append(("左右反色", img4))

    logger.info(f"将显示 {len(patterns)} 个图案，每个图案显示3秒")
    logger.info("请观察墨水屏变化...")

    for i, (name, img) in enumerate(patterns):
        logger.info(f"\n[{i+1}/{len(patterns)}] 显示: {name}")

        driver.display_image(img)

        # 保存调试图像
        debug_path = Path(f"data/debug_auto_{i+1}_{name}.png")
        img.save(debug_path)
        logger.info(f"调试图像: {debug_path}")

        logger.info("等待3秒...")
        time.sleep(3)

    driver.sleep()

    logger.info("\n" + "=" * 60)
    logger.info("测试完成！")
    logger.info(f"共显示 {len(patterns)} 个图案")
    logger.info("调试图像保存在 data/ 目录")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
