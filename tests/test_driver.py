#!/usr/bin/env python3
"""
E-Paper Driver Test
墨水屏驱动测试脚本

测试硬件驱动和 Mock 模式
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.epaper_driver import EpaperDriver, create_driver
from utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)


def create_test_image(width: int = 240, height: int = 360) -> 'Image':
    """
    创建测试图像

    Args:
        width: 图像宽度
        height: 图像高度

    Returns:
        Image: PIL Image 对象
    """
    from PIL import Image, ImageDraw, ImageFont

    # 创建单色图像（白色背景）
    img = Image.new('1', (width, height), 255)  # 255 = 白色
    draw = ImageDraw.Draw(img)

    # 绘制边框
    margin = 10
    draw.rectangle(
        [(margin, margin), (width - margin, height - margin)],
        outline=0,  # 0 = 黑色
        width=2
    )

    # 绘制对角线（X）
    draw.line(
        [(margin, margin), (width - margin, height - margin)],
        fill=0,
        width=3
    )
    draw.line(
        [(width - margin, margin), (margin, height - margin)],
        fill=0,
        width=3
    )

    # 尝试加载字体
    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            24
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            14
        )
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 绘制标题
    title = "E-Paper Test"
    # 居中显示
    bbox = font_large.getbbox(title)
    title_width = bbox[2] - bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 50), title, font=font_large, fill=0)

    # 绘制信息
    info_lines = [
        f"Resolution: {width}x{height}",
        "Mode: Test",
        "Status: OK"
    ]

    y = 120
    for line in info_lines:
        draw.text((20, y), line, font=font_small, fill=0)
        y += 25

    # 绘制底部时间
    from datetime import datetime
    time_str = datetime.now().strftime("%H:%M:%S")
    draw.text((20, height - 40), f"Time: {time_str}", font=font_small, fill=0)

    return img


def test_basic_display():
    """测试基本显示功能"""
    logger.info("=" * 60)
    logger.info("墨水屏驱动测试")
    logger.info("=" * 60)

    try:
        # 1. 加载配置
        logger.info("步骤 1: 加载配置...")
        cfg = Config("config.yml")
        setup_logging(cfg)
        logger.info("✅ 配置加载成功")

        # 2. 创建驱动
        logger.info("\n步骤 2: 创建墨水屏驱动...")
        driver = create_driver()
        logger.info(f"✅ 驱动创建完成")
        logger.info(f"   - 模式: {'Mock 模拟' if driver.is_mock else '硬件'}")
        logger.info(f"   - 分辨率: {driver.width}x{driver.height}")

        # 3. 初始化显示器
        logger.info("\n步骤 3: 初始化显示器...")
        success = driver.init_display()
        if not success:
            logger.error("❌ 显示器初始化失败")
            return False
        logger.info("✅ 显示器初始化成功")

        # 4. 创建测试图像
        logger.info("\n步骤 4: 创建测试图像...")
        test_img = create_test_image(driver.width, driver.height)
        logger.info("✅ 测试图像创建完成")

        # 5. 显示图像
        logger.info("\n步骤 5: 显示测试图像...")
        success = driver.display_image(test_img)
        if not success:
            logger.error("❌ 图像显示失败")
            return False
        logger.info("✅ 图像显示成功")

        # 6. 清理资源
        logger.info("\n步骤 6: 清理资源...")
        driver.sleep()
        logger.info("✅ 驱动已进入睡眠模式")

        # 7. 测试总结
        logger.info("\n" + "=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)

        if driver.is_mock:
            logger.info("✅ Mock 模式测试通过")
            logger.info("💡 提示: 查看 data/debug_current_view.png 查看显示效果")
        else:
            logger.info("✅ 硬件模式测试通过")
            logger.info("💡 提示: 检查墨水屏是否显示测试图像")

        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


def test_context_manager():
    """测试上下文管理器"""
    logger.info("\n测试上下文管理器...")

    try:
        with create_driver() as driver:
            test_img = create_test_image(driver.width, driver.height)
            driver.display_image(test_img)

        logger.info("✅ 上下文管理器测试通过")
        return True

    except Exception as e:
        logger.error(f"❌ 上下文管理器测试失败: {e}")
        return False


def main():
    """主测试函数"""
    import argparse

    parser = argparse.ArgumentParser(description="墨水屏驱动测试")
    parser.add_argument(
        "--test",
        choices=["basic", "context", "all"],
        default="all",
        help="测试类型"
    )

    args = parser.parse_args()

    # 执行测试
    if args.test in ["basic", "all"]:
        test_basic_display()

    if args.test in ["context", "all"]:
        test_context_manager()


if __name__ == "__main__":
    main()
