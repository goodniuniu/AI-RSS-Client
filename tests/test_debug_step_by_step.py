#!/usr/bin/env python3
"""
分步调试墨水屏显示
用于定位墨水屏显示问题的具体环节
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from waveshare_epd import epd3in52
from PIL import Image
import time

print("=" * 60)
print("墨水屏分步调试")
print("=" * 60)

print("\n步骤1: 创建驱动实例")
try:
    epd = epd3in52.EPD()
    print("✅ 驱动创建成功")
except Exception as e:
    print(f"❌ 驱动创建失败: {e}")
    sys.exit(1)

print("\n步骤2: 初始化 (init)")
try:
    epd.init()
    print("✅ init() 完成")
except Exception as e:
    print(f"❌ init() 失败: {e}")
    sys.exit(1)

print("\n步骤3: 清屏 (display_NUM)")
try:
    epd.display_NUM(epd.WHITE)
    print("✅ display_NUM(WHITE) 完成")
except Exception as e:
    print(f"❌ display_NUM() 失败: {e}")
    sys.exit(1)

print("\n步骤4: 加载查找表 (lut_GC)")
try:
    epd.lut_GC()
    print("✅ lut_GC() 完成")
except Exception as e:
    print(f"❌ lut_GC() 失败: {e}")
    sys.exit(1)

print("\n步骤5: 刷新 (refresh)")
try:
    epd.refresh()
    print("✅ refresh() 完成")
except Exception as e:
    print(f"❌ refresh() 失败: {e}")
    sys.exit(1)

print("\n等待2秒...")
time.sleep(2)
print("✅ 初始化序列完成")

print("\n步骤6: 创建测试图像")
try:
    img = Image.new('1', (240, 360), 0)  # 全黑
    print("✅ 图像创建完成（全黑 240x360）")
except Exception as e:
    print(f"❌ 图像创建失败: {e}")
    sys.exit(1)

print("\n步骤7: 转换为缓冲区")
try:
    buffer = epd.getbuffer(img)
    print(f"✅ 缓冲区创建成功（大小: {len(buffer)} 字节）")
except Exception as e:
    print(f"❌ 缓冲区创建失败: {e}")
    sys.exit(1)

print("\n步骤8: 发送到屏幕 (display)")
try:
    epd.display(buffer)
    print("✅ display() 完成 - 数据已发送到墨水屏")
except Exception as e:
    print(f"❌ display() 失败: {e}")
    sys.exit(1)

print("\n步骤9: 刷新屏幕 (refresh)")
try:
    epd.refresh()
    print("✅ refresh() 完成 - 屏幕应该开始刷新")
except Exception as e:
    print(f"❌ refresh() 失败: {e}")
    print("⚠️  这就是屏幕不更新的原因！必须调用 refresh()！")
    sys.exit(1)

print("\n等待3秒观察刷新...")
time.sleep(3)

print("\n步骤10: 清理资源 (sleep)")
try:
    epd.sleep()
    print("✅ sleep() 完成 - 墨水屏进入睡眠模式")
except Exception as e:
    print(f"❌ sleep() 失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 所有步骤完成！")
print("=" * 60)
print("\n预期结果：")
print("- 屏幕应该从白色变成全黑")
print("- 如果看到全黑屏幕，说明硬件驱动工作正常")
print("=" * 60)
