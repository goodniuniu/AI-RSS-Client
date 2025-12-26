#!/usr/bin/env python3
"""
简化的墨水屏硬件测试程序
直接测试硬件初始化和显示
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from PIL import Image, ImageDraw, ImageFont

def test_hardware_only():
    """仅测试硬件初始化和显示"""
    print("=" * 50)
    print("墨水屏硬件测试")
    print("=" * 50)

    try:
        print("导入墨水屏库...")
        from waveshare_epd import epd3in52
        print("✅ 库导入成功")

        print("\n初始化墨水屏...")
        epd = epd3in52.EPD()
        print("✅ EPD 对象创建成功")

        print("\n准备测试图像...")
        # 创建简单的测试图像
        image = Image.new('1', (240, 360), 1)  # 白色背景
        draw = ImageDraw.Draw(image)

        # 绘制边框
        draw.rectangle([5, 5, 235, 355], outline=0, width=2)

        # 加载字体
        try:
            font_large = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24
            )
            font_small = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16
            )
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # 绘制文本
        draw.text((120, 50), "HARDWARE TEST", font=font_large, fill=0, anchor="mm")
        draw.text((120, 100), "E-Paper 3.52\"", font=font_small, fill=0, anchor="mm")
        draw.text((120, 130), "240 x 360", font=font_small, fill=0, anchor="mm")

        # 绘制测试区域
        draw.rectangle([30, 160, 210, 200], outline=0, width=2)
        draw.text((120, 180), "If you can see this", font=font_small, fill=0, anchor="mm")

        # 底部时间
        from datetime import datetime
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        draw.text((120, 320), time_str, font=font_small, fill=0, anchor="mm")

        # 保存调试图像
        os.makedirs('output', exist_ok=True)
        image.save('output/test_hardware.png')
        print("✅ 测试图像已生成: output/test_hardware.png")

        print("\n初始化硬件...")
        epd.init()
        print("✅ 硬件初始化成功")

        print("\n发送数据到墨水屏...")
        epd.display(epd.getbuffer(image))
        print("✅ 数据发送成功")

        print("\n进入睡眠模式...")
        epd.sleep()
        print("✅ 睡眠模式设置成功")

        print("\n" + "=" * 50)
        print("✅ 墨水屏显示完成！")
        print("如果看到屏幕变化，说明硬件正常工作")
        print("=" * 50)

        image.close()
        return True

    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("请确保墨水屏库文件在 lib/waveshare_epd/ 目录")
        return False

    except PermissionError as e:
        print(f"\n❌ 权限错误: {e}")
        print("请使用 sudo 运行此程序:")
        print("  sudo venv/bin/python test_epaper_hardware.py")
        return False

    except OSError as e:
        print(f"\n❌ 硬件访问错误: {e}")
        print("可能原因:")
        print("  1. 墨水屏未正确连接")
        print("  2. SPI 未启用 (运行 raspi-config)")
        print("  3. GPIO 被其他程序占用")
        return False

    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_hardware_only()
    sys.exit(0 if success else 1)
