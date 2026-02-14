#!/bin/bash

# ============================================================================
# BTC Paper Trading Bot - Start Script
# Quick start/restart the bot
# ============================================================================

BOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BOT_DIR"

echo "🚀 Starting BTC Paper Trading Bot..."

# Check if running as systemd service
if systemctl is-active --quiet btc-bot; then
    echo "Bot is running as service. Restarting..."
    sudo systemctl restart btc-bot
    echo "✅ Service restarted!"
    echo "📊 View status: sudo systemctl status btc-bot"
    echo "📝 View logs: tail -f logs/bot.log"
else
    echo "Starting bot manually..."
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Run ./setup_pi.sh first."
        exit 1
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo "❌ .env file not found. Create it from .env.example"
        exit 1
    fi
    
    # Start the bot
    python main.py
fi
