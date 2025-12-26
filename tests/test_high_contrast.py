#!/usr/bin/env python3
"""
高对比度测试图案
用于确认墨水屏正常更新
"""

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
    cfg = Config("config.yml")
    setup_logging(cfg)

    driver = create_driver()
    driver.init_display()

    # 创建图像 - 使用高对比度设计
    img = Image.new('1', (240, 360), 255)  # 白色背景
    draw = ImageDraw.Draw(img)

    # 加载字体
    try:
        font_xlarge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_xlarge = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 1. 顶部黑色区域
    draw.rectangle([0, 0, 240, 80], fill=0)  # 黑色

    # 2. 白色大标题
    title = "TEST"
    bbox = font_xlarge.getbbox(title)
    title_x = (240 - (bbox[2] - bbox[0])) // 2
    title_y = (80 - (bbox[3] - bbox[1])) // 2
    draw.text((title_x, title_y), title, font=font_xlarge, fill=255)

    # 3. 中间的大黑框
    draw.rectangle([20, 100, 220, 260], outline=0, width=5)

    # 4. 大字体时间
    time_str = datetime.now().strftime("%H:%M:%S")
    bbox = font_large.getbbox(time_str)
    time_x = (240 - (bbox[2] - bbox[0])) // 2
    draw.text((time_x, 120), time_str, font=font_large, fill=0)

    # 5. 日期
    date_str = datetime.now().strftime("%Y-%m-%d")
    bbox = font_small.getbbox(date_str)
    date_x = (240 - (bbox[2] - bbox[0])) // 2
    draw.text((date_x, 160), date_str, font=font_small, fill=0)

    # 6. 测试标志
    draw.text((time_x, 200), "HIGH CONTRAST", font=font_small, fill=0)

    # 7. 底部条纹图案
    for i in range(5):
        y = 280 + i * 15
        if i % 2 == 0:
            draw.rectangle([0, y, 240, y + 15], fill=0)
        else:
            draw.rectangle([0, y, 240, y + 15], fill=255)

    # 8. 底部文字
    draw.text((20, 340), f"Driver Test", font=font_small, fill=0)

    logger.info("显示高对比度测试图案...")
    driver.display_image(img)
    logger.info("✅ 显示完成")

    # 保存调试副本
    debug_path = Path("data/debug_high_contrast.png")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(debug_path)
    logger.info(f"调试图像: {debug_path}")

    driver.sleep()


if __name__ == "__main__":
    main()
