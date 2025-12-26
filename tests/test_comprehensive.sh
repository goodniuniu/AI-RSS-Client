#!/bin/bash
#
# 墨水屏综合测试脚本
# 自动运行所有测试以验证墨水屏功能
#

set -e  # 遇到错误立即退出

echo "=================================================="
echo "墨水屏综合测试"
echo "=================================================="
echo ""

total_tests=0
passed_tests=0

# 测试函数
run_test() {
    local test_name=$1
    local test_command=$2

    total_tests=$((total_tests + 1))

    echo "-------------------------------------------"
    echo "测试 $total_tests: $test_name"
    echo "-------------------------------------------"

    if eval "$test_command"; then
        passed_tests=$((passed_tests + 1))
        echo "✅ 测试通过: $test_name"
    else
        echo "❌ 测试失败: $test_name"
        echo ""
        echo "建议："
        echo "  1. 检查资源占用: bash scripts/check_resources.sh"
        echo "  2. 查看日志: tail -100 data/logs/service.log"
        echo "  3. 分步调试: sudo venv/bin/python tests/test_debug_step_by_step.py"
        return 1
    fi
    echo ""
}

# 测试1：Mock 模式（软件模拟）
run_test "Mock 模式（软件模拟）" \
    "venv/bin/python tests/test_driver.py --test basic > /dev/null 2>&1"

# 测试2：资源检查
run_test "资源冲突检查" \
    "bash scripts/check_resources.sh | grep -q '未发现资源冲突'"

# 测试3：硬件初始化
run_test "硬件初始化序列" \
    "sudo venv/bin/python tests/test_original_init.py > /dev/null 2>&1"

# 测试4：图案切换测试
run_test "图案切换显示" \
    "sudo venv/bin/python tests/test_auto_patterns.py > /dev/null 2>&1"

# 测试5：高对比度图案
run_test "高对比度图案显示" \
    "sudo venv/bin/python tests/test_high_contrast.py > /dev/null 2>&1"

# 总结
echo "=================================================="
echo "测试总结"
echo "=================================================="
echo ""
echo "总测试数: $total_tests"
echo "通过测试: $passed_tests"
echo "失败测试: $((total_tests - passed_tests))"
echo ""

if [ $passed_tests -eq $total_tests ]; then
    echo "🎉 所有测试通过！墨水屏工作正常"
    echo ""
    echo "下一步："
    echo "  - 开始开发你的墨水屏应用"
    echo "  - 参考 DEVELOPMENT_GUIDE.md 了解最佳实践"
    exit 0
else
    echo "⚠️  部分测试失败"
    echo ""
    echo "排查建议："
    echo "  1. 运行资源检查: bash scripts/check_resources.sh"
    echo "  2. 分步调试: sudo venv/bin/python tests/test_debug_step_by_step.py"
    echo "  3. 查看故障排查指南: DEVELOPMENT_GUIDE.md 第11章"
    exit 1
fi
