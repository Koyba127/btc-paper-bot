#!/bin/bash

# ============================================================================
# BTC Paper Trading Bot - Stop Script
# ============================================================================

echo "🛑 Stopping BTC Paper Trading Bot..."

# Check if running as systemd service
if systemctl is-active --quiet btc-bot; then
    echo "Stopping systemd service..."
    sudo systemctl stop btc-bot
    echo "✅ Service stopped!"
else
    echo "Stopping manual instance..."
    pkill -f "python main.py" || echo "No running bot process found"
fi

echo "✅ Bot stopped!"
