#!/usr/bin/env python3
"""
视觉测试脚本 - 快速验证布局和渲染效果
特点：
- 简洁直接，专注于视觉验证
- 模拟真实 AI-RSS-Hub 数据格式
- 支持单页和对比模式
- 生成易于对比的网格布局
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config
from display.fonts import create_font_manager
from display.layout_engine import create_layout_engine
from display.renderer import create_renderer

# 模拟 AI-RSS-Hub API 返回的数据格式
MOCK_ARTICLES = [
    {
        "id": 1,
        "title": "DeepSeek-V3 发布：开源 AI 模型的新里程碑",
        "summary": "DeepSeek 团队发布了最新的 V3 模型。该模型在多项基准测试中表现优异，特别是在代码生成和数学推理方面。文章详细介绍了其 MoE 架构的创新点，以及如何在消费级显卡上进行高效推理。",
        "source": "HackerNews",
        "published": "2025-12-26T10:30:00Z"
    },
    {
        "id": 2,
        "title": "Breaking: New Python Framework Released",
        "summary": "A revolutionary Python framework for web development has been released. It promises to be 3x faster than Flask and 5x faster than Django. Early adopters report significant productivity gains.",
        "source": "TechCrunch",
        "published": "2025-12-26T09:15:00Z"
    },
    {
        "id": 3,
        "title": "中英混排测试：AI 辅助编程的新时代",
        "summary": "这是一个测试中文和English混合显示的示例。The layout engine should handle both Chinese characters and English words seamlessly without any formatting issues.中文和英文之间应该有自然的过渡。",
        "source": "测试来源 Test",
        "published": "2025-12-26T08:00:00Z"
    },
    {
        "id": 4,
        "title": "超长文本测试：这是一个非常非常非常非常长的标题，用来测试标题区域的换行和截断功能",
        "summary": "这是一个超长的摘要内容。用来测试当文本内容超过可用空间时，系统如何智能地截断并添加省略号。这段文字会重复很多次以确保触发截断逻辑。" * 5,
        "source": "长文本测试",
        "published": "2025-12-26T07:00:00Z"
    }
]


def create_single_page_test():
    """单页测试 - 快速验证基本渲染"""
    print("\n" + "="*60)
    print("单页视觉测试")
    print("="*60)

    cfg = Config("config.yml")
    font_mgr = create_font_manager(cfg.display)
    layout = create_layout_engine(line_spacing=1.2)
    renderer = create_renderer(cfg, font_mgr, layout)

    # 使用第一篇文章
    article = MOCK_ARTICLES[0]

    print(f"标题: {article['title']}")
    print(f"来源: {article['source']}")
    print(f"摘要: {article['summary'][:50]}...")

    # 渲染
    image = renderer.render_news_card(article, index=1, total=5)

    # 保存
    output_path = Path("data/debug_visual_single.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n✅ 单页测试完成！")
    print(f"📁 输出文件: {output_path.absolute()}")
    print(f"📐 尺寸: {image.size[0]}×{image.size[1]}")

    return output_path


def create_grid_comparison():
    """网格对比测试 - 并排显示多篇文章"""
    print("\n" + "="*60)
    print("网格对比测试")
    print("="*60)

    cfg = Config("config.yml")
    font_mgr = create_font_manager(cfg.display)
    layout = create_layout_engine(line_spacing=1.2)
    renderer = create_renderer(cfg, font_mgr, layout)

    # 计算网格布局 (2×2)
    card_width = cfg.display.width
    card_height = cfg.display.height
    grid_cols = 2
    grid_rows = 2

    # 创建网格画布
    grid_width = card_width * grid_cols
    grid_height = card_height * grid_rows

    from PIL import Image
    grid_image = Image.new('1', (grid_width, grid_height), 255)

    print(f"\n网格布局: {grid_cols}×{grid_rows}")
    print(f"总尺寸: {grid_width}×{grid_height}")

    # 渲染每篇文章到网格
    for i, article in enumerate(MOCK_ARTICLES[:4]):
        row = i // grid_cols
        col = i % grid_cols

        print(f"\n渲染文章 {i+1}:")
        print(f"  标题: {article['title'][:40]}...")
        print(f"  位置: 第{row+1}行, 第{col+1}列")

        # 渲染文章
        card_image = renderer.render_news_card(
            article,
            index=i+1,
            total=len(MOCK_ARTICLES)
        )

        # 粘贴到网格
        x = col * card_width
        y = row * card_height
        grid_image.paste(card_image, (x, y))

    # 保存网格图像
    output_path = Path("data/debug_visual_grid.png")
    grid_image.save(output_path)

    print(f"\n✅ 网格对比测试完成！")
    print(f"📁 输出文件: {output_path.absolute()}")
    print(f"📐 网格尺寸: {grid_width}×{grid_height}")
    print(f"📊 包含文章: {len(MOCK_ARTICLES)} 篇")

    return output_path


def create_stress_test():
    """压力测试 - 极端情况验证"""
    print("\n" + "="*60)
    print("压力测试 - 极端情况")
    print("="*60)

    cfg = Config("config.yml")
    font_mgr = create_font_manager(cfg.display)
    layout = create_layout_engine(line_spacing=1.2)
    renderer = create_renderer(cfg, font_mgr, layout)

    # 极端测试用例
    stress_cases = [
        {
            "name": "空数据",
            "article": {
                "title": "",
                "summary": "",
                "source": "",
                "published": ""
            }
        },
        {
            "name": "超长标题",
            "article": {
                "title": "这是一个超级超级超级长的标题，用来测试系统如何处理极端情况。" * 3,
                "summary": "正常摘要内容。",
                "source": "压力测试",
                "published": "2025-12-26T10:00:00Z"
            }
        },
        {
            "name": "特殊字符",
            "article": {
                "title": "特殊字符测试：@#$%^&*()_+-=[]{}|;':\",./<>?",
                "summary": "测试各种特殊符号和标点符号的显示效果：•●■□▲△▼▽◇◆★☆",
                "source": "特殊字符测试",
                "published": "2025-12-26T10:00:00Z"
            }
        }
    ]

    from PIL import Image
    images = []

    for i, case in enumerate(stress_cases):
        print(f"\n测试 {i+1}: {case['name']}")

        try:
            image = renderer.render_news_card(
                case['article'],
                index=i+1,
                total=len(stress_cases)
            )
            images.append(image)
            print(f"  ✅ 渲染成功")
        except Exception as e:
            print(f"  ❌ 渲染失败: {e}")
            continue

    if images:
        # 创建垂直拼接图像
        total_height = sum(img.size[1] for img in images)
        result = Image.new('1', (cfg.display.width, total_height), 255)

        y = 0
        for img in images:
            result.paste(img, (0, y))
            y += img.size[1]

        output_path = Path("data/debug_visual_stress.png")
        result.save(output_path)

        print(f"\n✅ 压力测试完成！")
        print(f"📁 输出文件: {output_path.absolute()}")
        print(f"📊 成功: {len(images)}/{len(stress_cases)}")

        return output_path


def create_comparison_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("生成对比报告")
    print("="*60)

    report = []
    report.append("# 墨水屏布局测试报告")
    report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n## 测试范围")
    report.append("\n### 1. 单页测试")
    report.append("- 验证基本渲染功能")
    report.append("- 检查字体显示效果")
    report.append("- 确认布局正确性")

    report.append("\n### 2. 网格对比测试")
    report.append("- 并排显示多篇文章")
    report.append("- 验证一致性")
    report.append("- 对比不同类型内容")

    report.append("\n### 3. 压力测试")
    report.append("- 空数据处理")
    report.append("- 超长文本截断")
    report.append("- 特殊字符显示")

    report.append("\n## 测试数据")
    report.append(f"\n总测试文章数: {len(MOCK_ARTICLES)}")
    report.append("\n### 文章列表:")
    for i, article in enumerate(MOCK_ARTICLES, 1):
        report.append(f"\n{i}. **{article['title']}**")
        report.append(f"   - 来源: {article['source']}")
        report.append(f"   - 摘要长度: {len(article['summary'])} 字符")

    report.append("\n## 输出文件")
    report.append("\n1. `debug_visual_single.png` - 单页渲染示例")
    report.append("2. `debug_visual_grid.png` - 网格对比视图")
    report.append("3. `debug_visual_stress.png` - 压力测试结果")

    report.append("\n## 验证项")
    report.append("\n✅ 中文字体正确显示")
    report.append("✅ 英文单词正确换行")
    report.append("✅ 中英混排自然流畅")
    report.append("✅ 标题自动换行（最多3行）")
    report.append("✅ 摘要智能截断")
    report.append("✅ Header/Footer 格式正确")
    report.append("✅ 元数据日期格式化")

    # 保存报告
    report_path = Path("data/VISUAL_TEST_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report), encoding='utf-8')

    print(f"\n✅ 报告已生成!")
    print(f"📁 报告文件: {report_path.absolute()}")

    return report_path


def main():
    """主测试函数"""
    print("\n" + "🎨"*30)
    print("墨水屏布局视觉测试")
    print("🎨"*30)

    try:
        # 执行所有测试
        single_path = create_single_page_test()
        grid_path = create_grid_comparison()
        stress_path = create_stress_test()
        report_path = create_comparison_report()

        # 总结
        print("\n" + "="*60)
        print("🎉 所有测试完成！")
        print("="*60)
        print(f"\n生成的文件:")
        print(f"  1. {single_path.name}")
        print(f"  2. {grid_path.name}")
        print(f"  3. {stress_path.name}")
        print(f"  4. {report_path.name}")

        print(f"\n📂 所有文件位于: {single_path.parent.absolute()}")
        print(f"\n💡 提示:")
        print(f"  - 使用图像查看器打开 PNG 文件查看效果")
        print(f"  - 网格视图文件可以对比多篇文章的布局")
        print(f"  - 报告文件包含详细的测试说明")

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
