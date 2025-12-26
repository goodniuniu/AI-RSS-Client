#!/usr/bin/env python3
"""
墨水屏测试程序
基于 docs/EPAPER_QUICK_GUIDE.md 中的指引
测试 3.52 英寸墨水屏 (240x360)
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

try:
    from waveshare_epd import epd3in52
    HAS_HARDWARE = True
    HARDWARE_AVAILABLE = True
except (ImportError, OSError, IOError) as e:
    print(f"⚠️  无法导入墨水屏库: {e}")
    print("将以软件模式运行（仅生成图像）")
    HAS_HARDWARE = False
    HARDWARE_AVAILABLE = False


class TextRenderer:
    """文本渲染器 - 实现自动换行和文本测量"""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.margin = 8

        # 字号选择（基于指南）
        if width <= 250:
            self.title_size = 16
            self.body_size = 14
            self.meta_size = 10
        else:
            self.title_size = 18
            self.body_size = 16
            self.meta_size = 12

        # 加载字体
        try:
            self.title_font = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                self.title_size
            )
            self.body_font = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                self.body_size
            )
            self.meta_font = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                self.meta_size
            )
        except:
            print("⚠️  无法加载 TrueType 字体，使用默认字体")
            self.title_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.meta_font = ImageFont.load_default()

    def wrap_text(self, text, font, max_width):
        """智能换行算法"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test = ' '.join(current_line + [word])
            if font.getlength(test) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def truncate_text(self, text, font, max_width, suffix="..."):
        """截断超长文本"""
        if font.getlength(text) <= max_width:
            return text

        # 逐步减少字符直到适合
        while text and font.getlength(text + suffix) > max_width:
            text = text[:-1]

        return text + suffix

    def render(self, title, content, footer=None):
        """渲染完整页面"""
        # 创建图像（1位模式，白色背景）
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)

        # 计算布局
        header_height = self.title_size + 10
        footer_height = self.meta_size + 8
        content_y = header_height + 5
        max_content_height = self.height - footer_height - 10

        # 绘制标题
        draw.text((self.margin, 5), title, font=self.title_font, fill=0)

        # 绘制分隔线
        draw.line([
            (self.margin, header_height),
            (self.width - self.margin, header_height)
        ], fill=0, width=1)

        # 绘制内容（自动换行）
        max_text_width = self.width - 2 * self.margin
        lines = self.wrap_text(content, self.body_font, max_text_width)

        y = content_y
        line_height = self.body_size + 2

        for line in lines[:15]:  # 最多显示15行
            if y + line_height > max_content_height:
                break

            draw.text((self.margin, y), line, font=self.body_font, fill=0)
            y += line_height

        # 绘制页脚
        if footer:
            draw.text(
                (self.margin, self.height - footer_height),
                footer,
                font=self.meta_font,
                fill=0
            )

        return image


def test_basic_display():
    """测试1：基本显示功能"""
    print("\n=== 测试1：基本文本显示 ===")

    # 创建渲染器
    renderer = TextRenderer(240, 360)

    # 准备测试内容
    title = "E-Paper Test"
    content = (
        "This is a test of the 3.52 inch e-paper display. "
        "It has a resolution of 240x360 pixels. "
        "The screen supports monochrome display with high contrast. "
        "Text wrapping is working correctly for long content."
    )
    footer = f"Updated: {datetime.now().strftime('%H:%M')}"

    # 渲染图像
    image = renderer.render(title, content, footer)

    # 保存为PNG文件（用于调试）
    os.makedirs('output', exist_ok=True)
    output_path = 'output/test_basic.png'
    image.save(output_path)
    print(f"✅ 图像已保存: {output_path}")

    # 如果有硬件，尝试显示
    if HAS_HARDWARE:
        try:
            epd = epd3in52.EPD()
            print("初始化墨水屏...")
            epd.init()
            print("墨水屏初始化成功")

            epd.display(epd.getbuffer(image))
            epd.sleep()

            print("✅ 墨水屏显示成功")

        except PermissionError:
            print("⚠️  需要 root 权限访问 GPIO")
            print("   提示: 使用 sudo 运行此程序以启用硬件显示")
            HARDWARE_AVAILABLE = False
        except OSError as e:
            print(f"⚠️  硬件访问失败: {e}")
            print("   提示: 请确保墨水屏正确连接")
            HARDWARE_AVAILABLE = False
        except Exception as e:
            print(f"⚠️  硬件显示失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            HARDWARE_AVAILABLE = False
        finally:
            image.close()
    else:
        image.close()
        print("ℹ️  硬件库未加载，仅生成图像文件")

    return True


def test_long_text():
    """测试2：长文本换行"""
    print("\n=== 测试2：长文本换行 ===")

    renderer = TextRenderer(240, 360)

    title = "Long Text Test"
    content = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco."
    )
    footer = "Page 1/1"

    image = renderer.render(title, content, footer)
    output_path = 'output/test_long_text.png'
    image.save(output_path)
    print(f"✅ 长文本测试图像已保存: {output_path}")

    if HAS_HARDWARE and HARDWARE_AVAILABLE:
        try:
            epd = epd3in52.EPD()
            epd.init()
            epd.display(epd.getbuffer(image))
            epd.sleep()
            print("✅ 长文本显示成功")
        except Exception as e:
            print(f"⚠️  硬件显示失败: {e}")
            HARDWARE_AVAILABLE = False
        finally:
            image.close()
    else:
        image.close()
        if HAS_HARDWARE and not HARDWARE_AVAILABLE:
            print("ℹ️  硬件不可用，跳过显示")

    return True


def test_multi_line():
    """测试3：多行文本布局"""
    print("\n=== 测试3：多行布局 ===")

    renderer = TextRenderer(240, 360)

    title = "RSS Feeds"
    content = """1. Tech News - AI advances
2. Science - New discovery
3. World - Climate update
4. Sports - Championship
5. Business - Market trends"""
    footer = "Auto-refresh: 5min"

    image = renderer.render(title, content, footer)
    output_path = 'output/test_multiline.png'
    image.save(output_path)
    print(f"✅ 多行布局测试图像已保存: {output_path}")

    if HAS_HARDWARE and HARDWARE_AVAILABLE:
        try:
            epd = epd3in52.EPD()
            epd.init()
            epd.display(epd.getbuffer(image))
            epd.sleep()
            print("✅ 多行布局显示成功")
        except Exception as e:
            print(f"⚠️  硬件显示失败: {e}")
            HARDWARE_AVAILABLE = False
        finally:
            image.close()
    else:
        image.close()
        if HAS_HARDWARE and not HARDWARE_AVAILABLE:
            print("ℹ️  硬件不可用，跳过显示")

    return True


def main():
    """主测试函数"""
    print("=" * 50)
    print("墨水屏测试程序")
    print("=" * 50)

    if HAS_HARDWARE:
        print("✅ 硬件库已加载")
    else:
        print("ℹ️  软件模式（仅生成图像）")

    try:
        # 运行所有测试
        test_basic_display()
        test_long_text()
        test_multi_line()

        print("\n" + "=" * 50)
        print("✅ 所有测试完成")
        print(f"📁 输出文件保存在: {os.path.abspath('output')}")
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
