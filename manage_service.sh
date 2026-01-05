#!/bin/bash
# AI-RSS-Client Service Management Script
# Easy commands to manage the AI-RSS-Client service

SERVICE_NAME="ai-rss-client"
SERVICE_FILE="/home/admin/Github/AI-RSS-Client/systemd/${SERVICE_NAME}.service"
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
    echo -e "${BLUE}  AI-RSS-Client Service Manager${NC}"
    echo -e "${BLUE}  E-paper RSS Display Service${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_menu() {
    print_header
    echo "Please select an action:"
    echo ""
    echo "  1) Status        - Check service status"
    echo "  2) Start         - Start the service"
    echo "  3) Stop          - Stop the service"
    echo "  4) Restart       - Restart the service"
    echo "  5) Logs          - View service logs (live)"
    echo "  6) All Logs      - View all service logs"
    echo "  7) Enable        - Enable auto-start on boot"
    echo "  8) Disable       - Disable auto-start on boot"
    echo "  9) Install       - Install service to systemd"
    echo " 10) Uninstall     - Remove service from systemd"
    echo " 11) Fetch News    - Fetch new articles from API"
    echo " 12) Test Display  - Test e-paper display"
    echo " 13) System Info   - Show system information"
    echo "  0) Exit          - Exit this menu"
    echo ""
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Note: Some operations require sudo privileges${NC}"
        echo ""
        return 1
    fi
    return 0
}

action_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo ""

    # Check if service is installed
    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${YELLOW}⚠️  Service is not installed yet.${NC}"
        echo -e "   Run option 9) Install to install the service."
        return 1
    fi

    systemctl status ${SERVICE_NAME} --no-pager

    echo ""
    echo -e "${CYAN}📈 Service Info:${NC}"

    # Show process info
    if pgrep -f "main.py run" > /dev/null; then
        PID=$(pgrep -f "main.py run" | head -1)
        echo -e "   Process ID: ${GREEN}${PID}${NC}"
        echo -e "   Uptime: $(ps -p ${PID} -o etime= 2>/dev/null | xargs)"
    fi

    # Show last display time
    if [ -f "/tmp/ai-rss-client-30s.log" ]; then
        LAST_UPDATE=$(stat -c %y /tmp/ai-rss-client-30s.log | cut -d'.' -f1)
        echo -e "   Last activity: ${GREEN}${LAST_UPDATE}${NC}"
    fi

    # Show article count
    if [ -f "${PROJECT_DIR}/data/articles.db" ]; then
        COUNT=$(sqlite3 ${PROJECT_DIR}/data/articles.db "SELECT COUNT(*) FROM articles" 2>/dev/null)
        if [ ! -z "$COUNT" ]; then
            echo -e "   Cached articles: ${GREEN}${COUNT}${NC}"
        fi
    fi
}

action_start() {
    echo -e "${YELLOW}▶️  Starting service...${NC}"

    # Check if service is installed
    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${RED}❌ Service is not installed. Run option 9) Install first.${NC}"
        return 1
    fi

    # Stop any existing manual processes
    if pgrep -f "main.py run" > /dev/null; then
        echo -e "${YELLOW}   Stopping existing manual process...${NC}"
        pkill -f "main.py run"
        sleep 2
    fi

    sudo systemctl start ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service started successfully${NC}"
        sleep 1
        action_status
    else
        echo -e "${RED}❌ Failed to start service${NC}"
        return 1
    fi
}

action_stop() {
    echo -e "${YELLOW}⏹️  Stopping service...${NC}"

    # Check if service is installed
    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${YELLOW}⚠️  Service not installed, stopping manual process...${NC}"
        pkill -f "main.py run"
        echo -e "${GREEN}✅ Manual process stopped${NC}"
        return 0
    fi

    sudo systemctl stop ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service stopped successfully${NC}"
    else
        echo -e "${RED}❌ Failed to stop service${NC}"
        return 1
    fi
}

action_restart() {
    echo -e "${YELLOW}🔄 Restarting service...${NC}"

    # Check if service is installed
    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${RED}❌ Service is not installed. Run option 9) Install first.${NC}"
        return 1
    fi

    sudo systemctl restart ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service restarted successfully${NC}"
        sleep 1
        action_status
    else
        echo -e "${RED}❌ Failed to restart service${NC}"
        return 1
    fi
}

action_logs() {
    echo -e "${BLUE}📝 Service Logs (Ctrl+C to exit):${NC}"
    echo ""

    # Check if service is installed
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        sudo journalctl -u ${SERVICE_NAME} -f
    else
        # Show manual process logs
        if [ -f "/tmp/ai-rss-client-30s.log" ]; then
            tail -f /tmp/ai-rss-client-30s.log
        else
            echo -e "${RED}❌ No logs found. Service may not be running.${NC}"
        fi
    fi
}

action_all_logs() {
    echo -e "${BLUE}📝 All Service Logs (less to navigate, q to quit):${NC}"
    echo ""

    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        sudo journalctl -u ${SERVICE_NAME} --no-pager | less
    else
        if [ -f "/tmp/ai-rss-client-30s.log" ]; then
            less /tmp/ai-rss-client-30s.log
        else
            echo -e "${RED}❌ No logs found${NC}"
        fi
    fi
}

action_enable() {
    echo -e "${YELLOW}⏳ Enabling auto-start on boot...${NC}"

    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${RED}❌ Service is not installed. Run option 9) Install first.${NC}"
        return 1
    fi

    sudo systemctl enable ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service will start automatically on boot${NC}"
        echo -e "${CYAN}   To disable, run option 8) Disable${NC}"
    else
        echo -e "${RED}❌ Failed to enable service${NC}"
        return 1
    fi
}

action_disable() {
    echo -e "${YELLOW}⏳ Disabling auto-start on boot...${NC}"

    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${RED}❌ Service is not installed${NC}"
        return 1
    fi

    sudo systemctl disable ${SERVICE_NAME}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service will not start on boot${NC}"
    else
        echo -e "${RED}❌ Failed to disable service${NC}"
        return 1
    fi
}

action_install() {
    echo -e "${CYAN}🔧 Installing ${SERVICE_NAME} service...${NC}"
    echo ""

    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}⚠️  This operation requires sudo privileges${NC}"
        echo "Please enter your password if prompted."
    fi

    # Stop existing service if running
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${YELLOW}   Stopping existing service...${NC}"
        sudo systemctl stop ${SERVICE_NAME}
        sudo systemctl disable ${SERVICE_NAME} 2>/dev/null
    fi

    # Stop manual processes
    if pgrep -f "main.py run" > /dev/null; then
        echo -e "${YELLOW}   Stopping manual processes...${NC}"
        pkill -f "main.py run"
        sleep 2
    fi

    # Copy service file
    echo -e "${CYAN}   Installing service file...${NC}"
    sudo cp ${SERVICE_FILE} /etc/systemd/system/${SERVICE_NAME}.service

    # Reload systemd
    echo -e "${CYAN}   Reloading systemd daemon...${NC}"
    sudo systemctl daemon-reload

    # Enable service
    echo -e "${CYAN}   Enabling service...${NC}"
    sudo systemctl enable ${SERVICE_NAME}

    echo ""
    echo -e "${GREEN}✅ Service installed successfully!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "   1. Start service: option 2) Start"
    echo -e "   2. View status:   option 1) Status"
    echo -e "   3. View logs:     option 5) Logs"
}

action_uninstall() {
    echo -e "${RED}⚠️  Uninstalling ${SERVICE_NAME} service...${NC}"
    echo ""

    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}⚠️  This operation requires sudo privileges${NC}"
    fi

    read -p "Are you sure? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Cancelled."
        return 0
    fi

    # Stop and disable service
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "${YELLOW}   Stopping and disabling service...${NC}"
        sudo systemctl stop ${SERVICE_NAME}
        sudo systemctl disable ${SERVICE_NAME}
    fi

    # Remove service file
    echo -e "${CYAN}   Removing service file...${NC}"
    sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service

    # Reload systemd
    echo -e "${CYAN}   Reloading systemd daemon...${NC}"
    sudo systemctl daemon-reload
    sudo systemctl reset-failed 2>/dev/null

    echo ""
    echo -e "${GREEN}✅ Service uninstalled successfully${NC}"
    echo ""
    echo -e "${CYAN}Note:${NC} You can still run the service manually:"
    echo -e "   cd ${PROJECT_DIR}"
    echo -e "   python3 main.py run --base-url http://8.134.202.27:8000"
}

action_fetch() {
    echo -e "${CYAN}📡 Fetching new articles from API...${NC}"
    echo ""

    cd ${PROJECT_DIR}
    python3 main.py fetch --base-url http://8.134.202.27:8000

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Fetch completed${NC}"

        # Show article count
        if [ -f "${PROJECT_DIR}/data/articles.db" ]; then
            COUNT=$(sqlite3 ${PROJECT_DIR}/data/articles.db "SELECT COUNT(*) FROM articles" 2>/dev/null)
            if [ ! -z "$COUNT" ]; then
                echo -e "${CYAN}   Total cached articles: ${COUNT}${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ Fetch failed${NC}"
        return 1
    fi
}

action_test() {
    echo -e "${CYAN}🧪 Testing e-paper display...${NC}"
    echo ""

    cd ${PROJECT_DIR}

    # Stop service temporarily
    if pgrep -f "main.py run" > /dev/null; then
        echo -e "${YELLOW}   Stopping service for test...${NC}"
        pkill -f "main.py run"
        sleep 2
    fi

    python3 main.py test-display --base-url http://8.134.202.27:8000

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Test completed${NC}"
        echo -e "${CYAN}   Check e-paper for test display${NC}"
    else
        echo -e "${RED}❌ Test failed${NC}"
        return 1
    fi

    # Restart service if it was running
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service" && systemctl is-active --quiet ${SERVICE_NAME}; then
        echo -e "${CYAN}   Restarting service...${NC}"
        sudo systemctl start ${SERVICE_NAME} > /dev/null 2>&1
    fi
}

action_info() {
    echo -e "${BLUE}📋 System Information:${NC}"
    echo ""

    # Service status
    echo -e "${CYAN}Service:${NC}"
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo -e "   Status: ${GREEN}Installed${NC}"
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            echo -e "   Running: ${GREEN}Yes${NC}"
        else
            echo -e "   Running: ${RED}No${NC}"
        fi
        if systemctl is-enabled --quiet ${SERVICE_NAME}; then
            echo -e "   Auto-start: ${GREEN}Enabled${NC}"
        else
            echo -e "   Auto-start: ${YELLOW}Disabled${NC}"
        fi
    else
        echo -e "   Status: ${YELLOW}Not installed${NC}"
    fi

    echo ""
    echo -e "${CYAN}Process:${NC}"
    if pgrep -f "main.py run" > /dev/null; then
        PID=$(pgrep -f "main.py run" | head -1)
        echo -e "   PID: ${GREEN}${PID}${NC}"
        echo -e "   Uptime: $(ps -p ${PID} -o etime= 2>/dev/null | xargs)"
        echo -e "   Memory: $(ps -p ${PID} -o rss= 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')"
    else
        echo -e "   Status: ${RED}Not running${NC}"
    fi

    echo ""
    echo -e "${CYAN}Articles:${NC}"
    if [ -f "${PROJECT_DIR}/data/articles.db" ]; then
        TOTAL=$(sqlite3 ${PROJECT_DIR}/data/articles.db "SELECT COUNT(*) FROM articles" 2>/dev/null)
        UNDISPLAYED=$(sqlite3 ${PROJECT_DIR}/data/articles.db "SELECT COUNT(*) FROM articles WHERE status='new'" 2>/dev/null)
        if [ ! -z "$TOTAL" ]; then
            echo -e "   Total: ${GREEN}${TOTAL}${NC}"
            echo -e "   Undisplayed: ${GREEN}${UNDISPLAYED}${NC}"
        fi

        # Date range
        RANGE=$(sqlite3 ${PROJECT_DIR}/data/articles.db "SELECT MIN(date(published_at)), MAX(date(published_at)) FROM articles" 2>/dev/null)
        if [ ! -z "$RANGE" ]; then
            echo -e "   Date range: ${RANGE}"
        fi
    else
        echo -e "   Status: ${YELLOW}No database found${NC}"
    fi

    echo ""
    echo -e "${CYAN}Hardware:${NC}"
    if [ -f "/usr/bin/python3" ]; then
        PYTHON_VERSION=$(/usr/bin/python3 --version 2>&1)
        echo -e "   Python: ${GREEN}${PYTHON_VERSION}${NC}"
    fi

    # Check e-paper driver
    if lsmod | grep -q "spi_bcm2835"; then
        echo -e "   SPI: ${GREEN}Loaded${NC}"
    else
        echo -e "   SPI: ${YELLOW}Not loaded${NC}"
    fi

    echo ""
    echo -e "${CYAN}Network:${NC}"
    if ping -c 1 -W 2 8.134.202.27 > /dev/null 2>&1; then
        echo -e "   API Server: ${GREEN}Online${NC}"
    else
        echo -e "   API Server: ${RED}Offline${NC}"
    fi
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
        install) action_install ;;
        uninstall) action_uninstall ;;
        fetch) action_fetch ;;
        test) action_test ;;
        info) action_info ;;
        *)
            echo "Usage: $0 {status|start|stop|restart|logs|all-logs|enable|disable|install|uninstall|fetch|test|info}"
            exit 1
            ;;
    esac
else
    # Interactive mode
    while true; do
        print_menu
        read -p "Enter choice [0-13]: " choice
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
            9) action_install ;;
            10) action_uninstall ;;
            11) action_fetch ;;
            12) action_test ;;
            13) action_info ;;
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
