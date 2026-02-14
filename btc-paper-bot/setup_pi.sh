#!/bin/bash

# ============================================================================
# BTC Paper Trading Bot - Raspberry Pi 5 Deployment Script
# ============================================================================

set -e  # Exit on error

echo "======================================"
echo "BTC Paper Trading Bot Setup"
echo "Raspberry Pi 5 Deployment"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo -e "${GREEN}[1/8] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ if not already installed
echo -e "${GREEN}[2/8] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    sudo apt install -y python3 python3-pip python3-venv
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "Python $PYTHON_VERSION installed"
fi

# Install git if needed
echo -e "${GREEN}[3/8] Checking git installation...${NC}"
if ! command -v git &> /dev/null; then
    sudo apt install -y git
fi

# Get bot directory
BOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Bot directory: $BOT_DIR"

# Create virtual environment
echo -e "${GREEN}[4/8] Setting up Python virtual environment...${NC}"
cd "$BOT_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo -e "${GREEN}[5/8] Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
echo -e "${GREEN}[6/8] Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file with your credentials!${NC}"
    echo "   nano .env"
else
    echo ".env file already exists"
fi

# Create systemd service
echo -e "${GREEN}[7/8] Creating systemd service...${NC}"

SERVICE_FILE="/etc/systemd/system/btc-bot.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=BTC Paper Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:$BOT_DIR/logs/bot.log
StandardError=append:$BOT_DIR/logs/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

echo "Systemd service created at $SERVICE_FILE"

# Create logs directory
mkdir -p "$BOT_DIR/logs"

# Set permissions
echo -e "${GREEN}[8/8] Setting permissions...${NC}"
chmod +x "$BOT_DIR/start_bot.sh"
chmod +x "$BOT_DIR/stop_bot.sh"
chmod +x "$BOT_DIR/setup_pi.sh"

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "======================================"
echo "NEXT STEPS:"
echo "======================================"
echo ""
echo "1. Configure your credentials:"
echo "   nano .env"
echo ""
echo "2. Test the bot manually:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Start the bot as a service:"
echo "   sudo systemctl enable btc-bot"
echo "   sudo systemctl start btc-bot"
echo ""
echo "4. Check bot status:"
echo "   sudo systemctl status btc-bot"
echo ""
echo "5. View logs:"
echo "   tail -f logs/bot.log"
echo "   journalctl -u btc-bot -f"
echo ""
echo "======================================"
echo "USEFUL COMMANDS:"
echo "======================================"
echo ""
echo "Start bot:    sudo systemctl start btc-bot"
echo "Stop bot:     sudo systemctl stop btc-bot"
echo "Restart bot:  sudo systemctl restart btc-bot"
echo "View status:  sudo systemctl status btc-bot"
echo "View logs:    tail -f logs/bot.log"
echo ""
