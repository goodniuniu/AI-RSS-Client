#!/usr/bin/env python3
"""使用原有程序的初始化方式测试"""

import sys
from pathlib import Path
import time

sys.path.insert(0, 'lib')

from waveshare_epd import epd3in52
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

print("=" * 60)
print("墨水屏刷新测试（使用原有程序的初始化方式）")
print("=" * 60)

print("\n初始化...")
epd = epd3in52.EPD()

print("执行 init()...")
epd.init()

print("\n执行原始清屏序列...")
print("1. display_NUM(WHITE)...")
epd.display_NUM(epd.WHITE)

print("2. lut_GC()...")
epd.lut_GC()

print("3. refresh()...")
epd.refresh()

print("4. 等待2秒...")
time.sleep(2)

print("\n✅ 初始化序列完成")

print("\n创建测试图像...")
img = Image.new('1', (240, 360), 255)
draw = ImageDraw.Draw(img)

# 加载字体
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
except:
    font = ImageFont.load_default()
    font_small = ImageFont.load_default()

# 绘制边框
draw.rectangle([10, 10, 230, 350], outline=0, width=3)

# 绘制标题
title = "TEST DISPLAY"
bbox = font.getbbox(title)
title_x = (240 - (bbox[2] - bbox[0])) // 2
draw.text((title_x, 50), title, font=font, fill=0)

# 绘制信息
info = [
    "Full Refresh",
    "Test Mode",
    f"Time: {datetime.now().strftime('%H:%M')}",
    "",
    "Check if screen",
    "shows this"
]

y = 100
for line in info:
    draw.text((20, y), line, font=font_small, fill=0)
    y += 20

print("✅ 图像创建完成")

print("\n显示图像...")
epd.display(epd.getbuffer(img))

print("✅ 图像已发送")

print("\n等待3秒观察...")
time.sleep(3)

print("\n进入睡眠模式...")
epd.sleep()

print("\n✅ 测试完成")
print("=" * 60)
print("请检查墨水屏是否更新！")
print("=" * 60)
