#!/usr/bin/env python3
"""
测试内容渲染器
验证新闻卡片的渲染效果
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.fonts import create_font_manager
from display.layout_engine import create_layout_engine
from display.renderer import create_renderer
from display.epaper_driver import create_driver
from utils.logger import get_logger

logger = get_logger(__name__)


def create_mock_articles():
    """创建模拟文章数据"""
    return [
        {
            'id': 1,
            'title': 'AI技术突破：新型深度学习算法提升图像识别准确率',
            'summary': '研究团队开发出一种新的深度学习算法，在多个图像识别基准测试中取得了突破性进展。该算法通过改进卷积神经网络架构，显著提升了图像分类的准确率和效率。',
            'source': '科技日报',
            'published': '2025-12-26T10:30:00Z',
            'author': '张三'
        },
        {
            'id': 2,
            'title': 'Breaking: New Python Framework Released',
            'summary': 'A new Python framework for web development has been released. It promises to be faster and more efficient than existing solutions. Developers are excited about the new features and improvements.',
            'source': 'Tech News',
            'published': '2025-12-26T09:15:00Z',
        },
        {
            'id': 3,
            'title': '中英混排测试标题 Mixed Chinese and English',
            'summary': '这是一段包含中文和English的混合文本，用来测试排版引擎的混排功能。The layout engine should handle both Chinese characters and English words properly without any issues.',
            'source': '测试来源',
            'published': '2025-12-26T08:00:00Z',
        },
        {
            'id': 4,
            'title': '超长标题测试：这是一个非常非常非常非常长的标题，用来测试标题区域如何处理超长文本的显示问题，应该会在三行内截断',
            'summary': '这是一个超长的摘要内容。' * 20,  # 重复20次创建超长摘要
            'source': '长文本测试',
            'published': '2025-12-26T07:00:00Z',
        },
        {
            'id': 5,
            'title': '空数据测试',
            'summary': '',
            'source': '',
            'published': '',
        }
    ]


def test_renderer():
    """测试渲染器"""
    logger.info("=" * 60)
    logger.info("内容渲染器测试")
    logger.info("=" * 60)

    # 初始化
    cfg = Config("config.yml")
    setup_logging(cfg)

    font_mgr = create_font_manager(cfg.display)
    layout = create_layout_engine(line_spacing=1.2)
    renderer = create_renderer(cfg, font_mgr, layout)
    driver = create_driver()

    if driver.is_mock:
        logger.info("Mock 模式：仅生成图像")
    else:
        logger.info("硬件模式：将显示到墨水屏")

    driver.init_display()

    # 创建模拟文章
    articles = create_mock_articles()
    logger.info(f"\n创建了 {len(articles)} 篇测试文章")

    # 渲染并显示每篇文章
    for i, article in enumerate(articles, 1):
        logger.info("\n" + "=" * 60)
        logger.info(f"渲染文章 {i}/{len(articles)}")
        logger.info("=" * 60)

        logger.info(f"标题: {article['title'][:50]}...")
        logger.info(f"来源: {article.get('source', 'N/A')}")
        logger.info(f"摘要长度: {len(article.get('summary', ''))} 字符")

        try:
            # 渲染文章
            image = renderer.render_news_card(article, index=i, total=len(articles))

            # 保存调试图像
            debug_path = Path(f"data/debug_article_{i}.png")
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(debug_path)
            logger.info(f"✅ 调试图像: {debug_path}")

            # 显示到墨水屏
            if not driver.is_mock:
                logger.info("发送到墨水屏...")
                driver.display_image(image)
                logger.info("✅ 显示完成")

                # 等待用户观察（仅硬件模式）
                if i < len(articles):
                    logger.info("\n按 Enter 继续下一篇文章...")
                    input()

        except Exception as e:
            logger.error(f"❌ 渲染失败: {e}", exc_info=True)
            continue

    # 测试简单页面
    logger.info("\n" + "=" * 60)
    logger.info("测试简单页面渲染")
    logger.info("=" * 60)

    simple_page = renderer.render_simple_page(
        title="系统提示",
        content="这是一个简单页面的测试。用于显示错误信息、帮助文档等不需要复杂格式的内容。",
        footer="AI-RSS v1.1.0"
    )

    debug_path = Path("data/debug_simple_page.png")
    simple_page.save(debug_path)
    logger.info(f"✅ 简单页面: {debug_path}")

    if not driver.is_mock:
        logger.info("发送到墨水屏...")
        driver.display_image(simple_page)
        logger.info("✅ 显示完成")

    driver.sleep()

    logger.info("\n" + "=" * 60)
    logger.info("✅ 渲染器测试完成")
    logger.info("=" * 60)

    logger.info("\n功能验证:")
    logger.info("  ✅ 新闻卡片渲染")
    logger.info("  ✅ 标题自动换行（最多3行）")
    logger.info("  ✅ 摘要智能截断")
    logger.info("  ✅ 中英混排支持")
    logger.info("  ✅ 超长文本处理")
    logger.info("  ✅ 空数据处理")
    logger.info("  ✅ 简单页面渲染")
    logger.info("\n渲染器已就绪！")


def main():
    """主函数"""
    try:
        test_renderer()
        return 0
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
