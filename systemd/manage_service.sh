#!/bin/bash
# AI-RSS-Hub Service Management Script
# Easy commands to manage the AI-RSS-Hub service

SERVICE_NAME="ai-rss-hub"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  AI-RSS-Hub Service Manager${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_menu() {
    print_header
    echo "Please select an action:"
    echo ""
    echo "  1) Status     - Check service status"
    echo "  2) Start      - Start the service"
    echo "  3) Stop       - Stop the service"
    echo "  4) Restart    - Restart the service"
    echo "  5) Logs       - View service logs (live)"
    echo "  6) All Logs   - View all service logs"
    echo "  7) Enable     - Enable auto-start on boot"
    echo "  8) Disable    - Disable auto-start on boot"
    echo "  9) Test API   - Test if API is responding"
    echo "  0) Exit       - Exit this menu"
    echo ""
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}⚠️  Note: Some operations require sudo privileges${NC}"
        echo ""
        return 1
    fi
    return 0
}

action_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    systemctl status ${SERVICE_NAME} --no-pager
}

action_start() {
    echo -e "${YELLOW}▶️  Starting service...${NC}"
    sudo systemctl start ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service started successfully${NC}"
        sleep 1
        systemctl status ${SERVICE_NAME} --no-pager
    else
        echo -e "${RED}❌ Failed to start service${NC}"
    fi
}

action_stop() {
    echo -e "${YELLOW}⏹️  Stopping service...${NC}"
    sudo systemctl stop ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service stopped successfully${NC}"
    else
        echo -e "${RED}❌ Failed to stop service${NC}"
    fi
}

action_restart() {
    echo -e "${YELLOW}🔄 Restarting service...${NC}"
    sudo systemctl restart ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service restarted successfully${NC}"
        sleep 1
        systemctl status ${SERVICE_NAME} --no-pager
    else
        echo -e "${RED}❌ Failed to restart service${NC}"
    fi
}

action_logs() {
    echo -e "${BLUE}📝 Service Logs (Ctrl+C to exit):${NC}"
    echo ""
    sudo journalctl -u ${SERVICE_NAME} -f
}

action_all_logs() {
    echo -e "${BLUE}📝 All Service Logs:${NC}"
    echo ""
    sudo journalctl -u ${SERVICE_NAME} --no-pager | less
}

action_enable() {
    echo -e "${YELLOW}⏳ Enabling auto-start on boot...${NC}"
    sudo systemctl enable ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service will start automatically on boot${NC}"
    else
        echo -e "${RED}❌ Failed to enable service${NC}"
    fi
}

action_disable() {
    echo -e "${YELLOW}⏳ Disabling auto-start on boot...${NC}"
    sudo systemctl disable ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service will not start on boot${NC}"
    else
        echo -e "${RED}❌ Failed to disable service${NC}"
    fi
}

action_test() {
    echo -e "${BLUE}🧪 Testing API...${NC}"
    echo ""

    # Test health endpoint
    echo "Testing health endpoint..."
    response=$(curl -s http://localhost:8000/api/health)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ API is responding${NC}"
        echo "Response: ${response}"
    else
        echo -e "${RED}❌ API not responding${NC}"
        return 1
    fi

    echo ""
    echo "Testing feeds endpoint..."
    response=$(curl -s "http://localhost:8000/api/feeds" | python3 -c "import sys, json; feeds=json.load(sys.stdin); print(f'Found {len(feeds)} feeds')" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${response}${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not parse feeds response${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ API is working!${NC}"
}

# Main loop
if [ "$1" != "" ]; then
    # Command line mode
    case "$1" in
        status) action_status ;;
        start) action_start ;;
        stop) action_stop ;;
        restart) action_restart ;;
        logs) action_logs ;;
        all-logs) action_all_logs ;;
        enable) action_enable ;;
        disable) action_disable ;;
        test) action_test ;;
        *)
            echo "Usage: $0 {status|start|stop|restart|logs|all-logs|enable|disable|test}"
            exit 1
            ;;
    esac
else
    # Interactive mode
    while true; do
        print_menu
        read -p "Enter choice [0-9]: " choice
        echo ""

        case $choice in
            1) action_status ;;
            2) action_start ;;
            3) action_stop ;;
            4) action_restart ;;
            5) action_logs ;;
            6) action_all_logs ;;
            7) action_enable ;;
            8) action_disable ;;
            9) action_test ;;
            0)
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Please try again.${NC}"
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
    done
fi
