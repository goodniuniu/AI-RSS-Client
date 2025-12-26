#!/bin/bash
#
# 墨水屏资源检查脚本
# 检查所有可能占用 GPIO/SPI 的服务和进程
#

echo "=================================================="
echo "墨水屏资源检查"
echo "=================================================="
echo ""

echo "1. 检查运行中的 systemd 服务"
echo "-------------------------------------------"
systemctl_list=$(sudo systemctl | grep -E "ai-news|weather|epaper|display" || echo "  无相关服务")
echo "$systemctl_list"
echo ""

echo "2. 检查相关 Python 进程"
echo "-------------------------------------------"
process_list=$(ps aux | grep -E "python.*epaper|python.*weather|python.*news" | grep -v grep || true)
if [ -n "$process_list" ]; then
    echo "$process_list"
    echo ""
    echo "  ⚠️  发现运行中的墨水屏进程！"
else
    echo "  无相关进程"
fi
echo ""

echo "3. 检查 GPIO/SPI 设备占用"
echo "-------------------------------------------"
device_usage=$(sudo lsof 2>/dev/null | grep -E "spidev|gpiomem" || echo "  无设备占用")
echo "$device_usage"
echo ""

echo "4. 检查 crontab 任务"
echo "-------------------------------------------"
crontab_tasks=$(crontab -l 2>/dev/null | grep -E "epaper|weather|news" || echo "  无相关任务")
echo "$crontab_tasks"
echo ""

echo "5. 总结"
echo "-------------------------------------------"
# 检测是否有冲突
has_conflict=0

if echo "$systemctl_list" | grep -q "active"; then
    echo "  ⚠️  发现运行中的服务"
    has_conflict=1
fi

if [ -n "$process_list" ]; then
    echo "  ⚠️  发现运行中的进程"
    has_conflict=1
fi

if echo "$device_usage" | grep -vq "无设备占用"; then
    echo "  ⚠️  发现设备占用"
    has_conflict=1
fi

if [ $has_conflict -eq 0 ]; then
    echo "  ✅ 未发现资源冲突"
    echo ""
    echo "墨水屏资源可用，可以正常使用"
else
    echo "  ❌ 发现资源冲突"
    echo ""
    echo "建议操作："
    echo "  停止所有服务: sudo systemctl stop ai-news-* weather-poetry-display.service"
    echo "  终止进程: sudo kill -9 <PID>"
fi

echo ""
echo "=================================================="
echo "检查完成"
echo "=================================================="
