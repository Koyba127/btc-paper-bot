# BTC Paper Trading Bot

Complete, production-ready asynchronous Python trading bot for Paper Trading on Raspberry Pi 5.
No real money involved. Strict risk management and multi-timeframe strategy.

## 1. Project Structure

```
btc-paper-bot/
├── main.py
├── config.py
├── .env.example
├── requirements.txt
├── data/
│   ├── __init__.py
│   ├── websocket_fetcher.py      # ccxt.pro Streams
│   └── historical.py             # Historical Data Fetching
├── strategies/
│   ├── __init__.py
│   └── multi_timeframe.py        # Logic: Trend(4h) + Momentum(1h) + Vol
├── execution/
│   ├── __init__.py
│   └── paper_engine.py           # Core Loop (P&L, State Machine)
├── risk_management/
│   ├── __init__.py
│   └── risk_manager.py           # Placeholder / Integrated in Engine
├── filters/
│   ├── correlation.py
│   └── funding.py
├── notifier/
│   ├── __init__.py
│   ├── email_notifier.py         # Resend API + Gmail Fallback
│   └── daily_report.py           # APScheduler Job (08:00 MEZ)
├── stats/
│   ├── __init__.py
│   └── statistics.py             # Stats & Equity Curve Generation
├── backtesting/
│   ├── __init__.py
│   └── backtest.py               # Historical Simulation 
├── utils/
│   ├── __init__.py
│   ├── logger.py                 # Structured Logging
│   └── helpers.py
├── monitoring/                   # Prometheus Exporter (Optional)
├── logs/                         # Rotated Logs
├── trade_log.json                # Trade History
├── balance_history.csv           # Balance Tracking
├── equity_curve.png              # Generated Daily
└── systemd/
    └── btc-paper-bot.service     # Auto-start on boot
```

## 2. Dependencies
- Python 3.12+
- `ccxt` (Async + Pro)
- `pandas`, `pandas_ta`, `numpy`
- `aiosmtplib`, `resend` (Email)
- `structlog` (Logging)
- `uvloop` (Event Loop Optimization)
- `apscheduler` (Cron Jobs)
- `matplotlib` (Reporting)

## 3. Installation on Raspberry Pi 5

### System Prep
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

### Clone & Setup
```bash
cd /home/pi
git clone https://github.com/your-repo/btc-paper-bot.git
cd btc-paper-bot

# Create Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

### Configuration
```bash
cp .env.example .env
nano .env
```
Fill in your **Resend API Key** (or use SMTP credentials).
Set `PAPER_TRADING_BALANCE` (Default: 10000).

### Systemd Service (Auto-Start)
```bash
# Edit service file to match your paths if different from default (/home/pi/btc-paper-bot)
nano systemd/btc-paper-bot.service

# Copy to systemd
sudo cp systemd/btc-paper-bot.service /etc/systemd/system/

# Reload & Enable
sudo systemctl daemon-reload
sudo systemctl enable btc-paper-bot
sudo systemctl start btc-paper-bot

# Check Status
sudo systemctl status btc-paper-bot
```

## 4. Evaluation Guide (After 14 Days)

### Automated Reports
Every morning at **08:00 MEZ**, you will receive an email with:
- **Equity Curve PNG**: Visual performance.
- **Stats**: Win Rate, Profit Factor, Max Drawdown, Sharpe Ratio.

### Manual Analysis
1.  **Check Logs**:
    ```bash
    tail -f logs/btc_paper_bot.log
    ```
    Verify no errors and consistent "Heartbeat" or "Processing" logs.
    
2.  **Inspect Trade Log**:
    `trade_log.json` contains every trade execution details (Entry, Exit, Reason, Slippage simulation).
    
3.  **Run Backtest Comparison**:
    Stop the bot briefly or run on another machine:
    ```bash
    python backtesting/backtest.py
    ```
    Compare the `Total Return` and `Max Drawdown` from the backtest against the live results in `trade_log.json`.
    
    *Note: Discrepancies may occur due to tick-level slippage (which paper trading simulates simply) vs OHLCV backtest data.*

### Live Monitoring
- **Files**:
    - `balance_history.csv`: Tracks equity over time.
    - `equity_curve.png`: Latest generated chart.

## 5. Strategy Summary
- **Trend**: 4h EMA50 > EMA200 + ADX > 22
- **Momentum**: 1h RSI (30-40 Long / 60-70 Short) + MACD Cross
- **Volume**: > 20-SMA
- **Exit**: Dynamic SL (ATR x 1.5) / TP (Risk x 2.8)
- **Risk**: 0.75% Equity per trade.

---
**Disclaimer**: Paper trading only. No financial advice.
