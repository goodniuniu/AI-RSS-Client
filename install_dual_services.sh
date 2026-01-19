#!/bin/bash
# AI-RSS-Client Dual Services Installation Script
# 双服务架构安装脚本

set -e

SERVICE_NAME_FETCH="ai-rss-client-fetch"
SERVICE_NAME_DISPLAY="ai-rss-client-display"
PROJECT_DIR="/home/admin/Github/AI-RSS-Client"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  AI-RSS-Client 双服务安装${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root or with sudo
check_privileges() {
    if [ "$EUID" -ne 0 ]; then
        print_warning "此脚本需要sudo权限"
        echo "请输入密码以继续..."
    fi
}

# Stop old service if exists
stop_old_service() {
    print_step "停止旧服务（如果存在）..."

    if systemctl list-unit-files | grep -q "^ai-rss-client.service"; then
        echo "  发现旧版单服务，正在停止..."
        sudo systemctl stop ai-rss-client 2>/dev/null || true
        sudo systemctl disable ai-rss-client 2>/dev/null || true
        print_success "旧服务已停止"
    else
        echo "  未发现旧版服务"
    fi

    # Stop any manual processes
    if pgrep -f "main.py run" > /dev/null; then
        echo "  停止手动进程..."
        pkill -f "main.py run" || true
        sleep 2
    fi
}

# Install new services
install_new_services() {
    print_step "安装新的双服务..."

    # Install fetch service
    echo "  安装内容获取服务..."
    sudo cp ${PROJECT_DIR}/systemd/${SERVICE_NAME_FETCH}.service /etc/systemd/system/

    # Install display service
    echo "  安装显示服务..."
    sudo cp ${PROJECT_DIR}/systemd/${SERVICE_NAME_DISPLAY}.service /etc/systemd/system/

    # Reload systemd
    echo "  重载systemd..."
    sudo systemctl daemon-reload

    print_success "新服务已安装"
}

# Enable services
enable_services() {
    print_step "设置开机自启..."

    sudo systemctl enable ${SERVICE_NAME_FETCH}
    sudo systemctl enable ${SERVICE_NAME_DISPLAY}

    print_success "服务已设置为开机自启"
}

# Start services
start_services() {
    print_step "启动服务..."

    # Start fetch service
    echo "  启动内容获取服务..."
    sudo systemctl start ${SERVICE_NAME_FETCH}
    sleep 2

    # Start display service
    echo "  启动显示服务..."
    sudo systemctl start ${SERVICE_NAME_DISPLAY}
    sleep 2

    print_success "服务已启动"
}

# Show status
show_status() {
    print_step "服务状态："
    echo ""

    echo -e "${CYAN}内容获取服务:${NC}"
    sudo systemctl status ${SERVICE_NAME_FETCH} --no-pager
    echo ""

    echo -e "${CYAN}显示服务:${NC}"
    sudo systemctl status ${SERVICE_NAME_DISPLAY} --no-pager
    echo ""
}

# Show next steps
show_next_steps() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${GREEN}✅ 安装完成！${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo -e "${CYAN}常用命令:${NC}"
    echo ""
    echo "查看服务状态:"
    echo "  sudo systemctl status ${SERVICE_NAME_FETCH}"
    echo "  sudo systemctl status ${SERVICE_NAME_DISPLAY}"
    echo ""
    echo "查看服务日志:"
    echo "  sudo journalctl -u ${SERVICE_NAME_FETCH} -f"
    echo "  sudo journalctl -u ${SERVICE_NAME_DISPLAY} -f"
    echo ""
    echo "重启服务:"
    echo "  sudo systemctl restart ${SERVICE_NAME_FETCH}"
    echo "  sudo systemctl restart ${SERVICE_NAME_DISPLAY}"
    echo ""
    echo "停止服务:"
    echo "  sudo systemctl stop ${SERVICE_NAME_FETCH}"
    echo "  sudo systemctl stop ${SERVICE_NAME_DISPLAY}"
    echo ""
    echo -e "${CYAN}手动测试命令:${NC}"
    echo ""
    echo "手动获取一次内容:"
    echo "  python3 ${PROJECT_DIR}/main.py fetch --base-url http://8.134.202.27:8000"
    echo ""
    echo "测试显示硬件:"
    echo "  python3 ${PROJECT_DIR}/main.py test-display --base-url http://8.134.202.27:8000"
    echo ""
    echo "查看系统状态:"
    echo "  python3 ${PROJECT_DIR}/main.py status --base-url http://8.134.202.27:8000"
    echo ""
    echo -e "${CYAN}更多信息:${NC}"
    echo "  查看 ${PROJECT_DIR}/SERVICES_ARCHITECTURE.md"
    echo ""
}

# Main installation flow
main() {
    print_header

    check_privileges
    stop_old_service
    install_new_services
    enable_services
    start_services
    show_status
    show_next_steps
}

# Run main
main
