#!/bin/bash
# AI-RSS-Client Installation Script

set -e

echo "=========================================="
echo "  AI-RSS-Client Installation Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python $python_version found"

# Create virtual environment (optional)
read -p "Create virtual environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    print_success "Virtual environment activated"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt
print_success "Dependencies installed"

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data
mkdir -p logs
print_success "Data directories created"

# Check API connection
echo ""
echo "Testing AI-RSS-Hub API connection..."
read -p "Enter AI-RSS-Hub URL (default: http://localhost:8000): " api_url
api_url=${api_url:-http://localhost:8000}

if curl -s "$api_url/api/health" > /dev/null; then
    print_success "API connection successful"
else
    print_error "Cannot connect to API at $api_url"
    echo "Please ensure AI-RSS-Hub is running"
    exit 1
fi

# Configure API token (optional)
echo ""
read -p "Does your API require a token? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter API token: " api_token
    echo "export AI_RSS_API_TOKEN=\"$api_token\"" >> .env
    print_success "API token configured"
fi

# Create systemd service (optional)
echo ""
read -p "Install systemd service for auto-start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    INSTALL_DIR=$(pwd)
    USER=$(whoami)

    echo "Creating systemd service..."

    sudo tee /etc/systemd/system/ai-rss-client.service > /dev/null <<EOF
[Unit]
Description=AI-RSS-Client E-paper Display Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py run --interval 1
WorkingDirectory=$INSTALL_DIR
User=$USER
Group=$USER
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-rss-client

# Security settings
ReadWritePaths=$INSTALL_DIR/data $INSTALL_DIR/logs
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
EOF

    print_success "Systemd service installed"

    # Ask if auto-start should be enabled
    read -p "Enable service to start on boot? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl enable ai-rss-client.service
        print_success "Service enabled for auto-start"
    fi

    # Ask if service should be started now
    read -p "Start service now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start ai-rss-client.service
        print_success "Service started"
        echo ""
        echo "Check status with: sudo systemctl status ai-rss-client"
        echo "View logs with: sudo journalctl -u ai-rss-client -f"
    fi
fi

# Final summary
echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Quick Start Commands:"
echo "  1. Test API:     python3 main.py test-api"
echo "  2. Fetch content: python3 main.py fetch"
echo "  3. Run display:  python3 main.py run"
echo "  4. Show status:  python3 main.py status"
echo "  5. Test display: python3 main.py test-display"
echo ""
echo "For more information, see README.md"
echo ""
