# 🤖 BTC Paper Trading Bot - Raspberry Pi 5

**Automated day trading bot for Bitcoin with email notifications**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red.svg)](https://www.raspberrypi.com/)
[![Strategy](https://img.shields.io/badge/Strategy-Day%20Trading-green.svg)](strategies/day_trading.py)

---

## 📊 Performance Summary

**60-Day Backtest Results:**
- ✅ **50 trades** executed
- ✅ **46% win rate** with 2:1 R:R
- ✅ **+13% profit** ($10,000 → $11,300)
- ✅ **0.75% risk per trade** (conservative)
- ✅ **15m/1H timeframes** (day trading)

---

## 🌟 Features

### Trading:
- ✅ **Automated day trading** on BTC/USDT
- ✅ **Paper trading** (no real money risk)
- ✅ **Smart entry signals** (EMA, ADX, RSI, Stoch RSI)
- ✅ **Dynamic stop loss** (ATR-based)
- ✅ **2:1 risk/reward ratio**
- ✅ **Strict risk management** (0.75% per trade)

### Notifications:
- ✅ **Email alerts** for every trade
- ✅ **Resend API** support (recommended)
- ✅ **SMTP fallback** (Gmail compatible)
- ✅ **Real-time updates** on entries/exits

### Infrastructure:
- ✅ **Optimized for Raspberry Pi 5**
- ✅ **Systemd service** (auto-start on boot)
- ✅ **Low resource usage** (<400MB RAM)
- ✅ **WebSocket data streaming**
- ✅ **Comprehensive logging**
- ✅ **State persistence** (survives reboots)

### Optimization:
- ✅ **Genetic algorithm optimizer** included
- ✅ **Backtesting framework**
- ✅ **Parameter validation tools**

---

## 🚀 Quick Start

### 1. Transfer to Raspberry Pi
```bash
# Option 1: Git
git clone <your-repo> ~/btc-paper-bot

# Option 2: SCP
scp -r btc-paper-bot pi@raspberrypi.local:~/
```

### 2. Run Setup
```bash
cd ~/btc-paper-bot
chmod +x setup_pi.sh
./setup_pi.sh
```

### 3. Configure
```bash
nano .env
```

Add your credentials (choose one method):

**Resend (Recommended):**
```env
RESEND_API_KEY=re_your_key_here
EMAIL_TO=your@email.com
```

**Gmail:**
```env
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_TO=your@email.com
```

### 4. Test & Start
```bash
# Test email
source venv/bin/activate
python test_email.py

# Start bot
sudo systemctl enable btc-bot
sudo systemctl start btc-bot

# Check status
sudo systemctl status btc-bot
```

**Done!** 🎉

---

## 📁 Project Structure

```
btc-paper-bot/
├── main.py                          # Main bot entry point
├── config.py                        # Configuration management
├── .env                             # Your credentials (create from .env.example)
│
├── strategies/
│   └── day_trading.py              # Day trading strategy (15m/1H)
│
├── execution/
│   └── paper_engine.py             # Paper trading execution engine
│
├── data/
│   └── data_manager.py             # OHLCV data management
│
├── notifier/
│   └── email_notifier.py           # Email notification system
│
├── backtesting/
│   ├── backtest.py                 # Single strategy backtest
│   ├── genetic_optimizer.py        # Fast parameter optimization
│   └── optimize_params.py          # Grid search optimizer
│
├── monitoring/
│   └── metrics.py                  # Prometheus metrics
│
├── utils/
│   ├── logger.py                   # Structured logging
│   └── helpers.py                  # Utility functions
│
├── setup_pi.sh                     # Automated Raspberry Pi setup
├── start_bot.sh                    # Quick start script
├── stop_bot.sh                     # Quick stop script
├── test_email.py                   # Email system tester
│
├── QUICKSTART.md                   # 5-minute setup guide
├── RASPBERRY_PI_SETUP.md           # Complete deployment guide
├── OPTIMIZATION_COMPLETE_GUIDE.md  # How to optimize parameters
├── OPTIMIZATION_LESSONS.md         # Avoid overfitting mistakes
│
├── trade_log.json                  # All trades (auto-generated)
├── paper_state.json                # Bot state (auto-generated)
└── logs/                           # Log files (auto-generated)
```

---

## 📧 Email Notifications

### What You'll Receive:

**Trade Entry:**
```
📈 LONG Signal - BTC/USDT
Entry: $95,000
Stop Loss: $93,500 (-$150 risk)
Take Profit: $98,000 (+$300 target)
Position Size: 0.1 BTC
Time: 2026-02-14 14:30:00
```

**Profitable Exit:**
```
✅ LONG Closed - PROFIT
Entry: $95,000 → Exit: $98,000
Profit: +$300 (+3.16%)
New Balance: $10,300
Duration: 4h 15m
```

**Stop Loss:**
```
❌ LONG Closed - STOP LOSS
Entry: $95,000 → Exit: $93,500
Loss: -$150 (-1.58%)
New Balance: $9,850
```

---

## 🎯 Strategy Details

### Day Trading Strategy (15m/1H):

**Indicators:**
- **EMA 200** (trend filter on 1H)
- **ADX** (trend strength > 18)
- **Stochastic RSI** (entry timing)
- **RSI** (momentum confirmation)
- **ATR** (dynamic stop loss)

**Entry Rules (LONG):**
- 1H trend: EMA50 > EMA200 + ADX > 18
- 15m: Price > EMA200
- StochRSI: Bullish crossover from oversold (<20)
- RSI: < 60

**Entry Rules (SHORT):**
- 1H trend: EMA50 < EMA200 + ADX > 18
- 15m: Price < EMA200
- StochRSI: Bearish crossover from overbought (>80)
- RSI: > 40

**Exit Rules:**
- Stop Loss: Entry ± (2.0 × ATR)
- Take Profit: Entry ± (2.0 × Risk) [2:1 R:R]
- Maximum 1 position at a time

**Risk Management:**
- 0.75% of balance per trade
- Position sizing based on SL distance
- 0.04% trading fees included

---

## 🔧 Configuration

### Trading Settings (.env):
```env
PAPER_TRADING_BALANCE=10000.0    # Starting balance
RISK_PERCENT=0.75                 # Risk per trade
SYMBOL=BTC/USDT                   # Trading pair
LOG_LEVEL=INFO                    # Logging detail
```

### Strategy Parameters (strategies/day_trading.py):
```python
adx_threshold = 18              # Trend strength filter
stoch_oversold = 20             # LONG entry zone
stoch_overbought = 80           # SHORT entry zone
risk_reward_ratio = 2.0         # TP = 2x risk
sl_atr_multiplier = 2.0         # SL = 2x ATR
rsi_long_max = 60               # RSI filter for LONG
rsi_short_min = 40              # RSI filter for SHORT
```

---

## 📊 Monitoring

### View Logs:
```bash
# Live logs
tail -f logs/bot.log

# Systemd logs
journalctl -u btc-bot -f

# Last 50 lines
journalctl -u btc-bot -n 50
```

### Control Bot:
```bash
# Start
sudo systemctl start btc-bot

# Stop
sudo systemctl stop btc-bot

# Restart
sudo systemctl restart btc-bot

# Status
sudo systemctl status btc-bot
```

### Check Performance:
```bash
# View trades
cat trade_log.json | python -m json.tool

# Check balance
grep "Balance" logs/bot.log | tail -n 1
```

---

## 🔬 Optimization

### Run Genetic Algorithm (Fast):
```bash
source venv/bin/activate
python backtesting/genetic_optimizer.py
# Takes ~5 minutes, tests 2,000 combinations
```

### Run Grid Search (Thorough):
```bash
python backtesting/optimize_params.py
# Takes ~20 minutes, tests 3,840 combinations
```

### Validate Parameters:
```bash
# After optimization, always validate:
python backtesting/backtest.py
```

**⚠️ Important:** Always test optimized parameters on out-of-sample data before deploying!

See `OPTIMIZATION_COMPLETE_GUIDE.md` for details.

---

## 🛠️ Troubleshooting

### Bot won't start:
```bash
# Check service
sudo systemctl status btc-bot

# View errors
journalctl -u btc-bot -n 100
tail logs/bot_error.log
```

### No emails:
```bash
# Test email
python test_email.py

# Check credentials in .env
nano .env
```

### Connection issues:
```bash
# Test internet
ping binance.com

# Test API
python -c "import ccxt; print(ccxt.binance().fetch_ticker('BTC/USDT'))"
```

---

## 📈 Expected Performance

### Raspberry Pi 5:
- CPU: 5-15% (normal load)
- Memory: 200-400MB
- Network: Minimal (WebSocket)
- Storage: <100MB logs/month

### Trading:
- Trades: ~25/month (0.8/day)
- Win Rate: 40-50%
- Monthly Return: 5-15%
- Max Drawdown: <20%

---

## 🔐 Security

### Secure .env:
```bash
chmod 600 .env
```

### Update regularly:
```bash
sudo apt update && sudo apt upgrade -y
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Use SSH keys:
```bash
ssh-keygen -t ed25519
ssh-copy-id pi@raspberrypi.local
```

---

## 📚 Documentation

- **`QUICKSTART.md`** - 5-minute setup guide
- **`RASPBERRY_PI_SETUP.md`** - Complete deployment guide
- **`OPTIMIZATION_COMPLETE_GUIDE.md`** - Parameter tuning
- **`OPTIMIZATION_LESSONS.md`** - Avoid overfitting

---

## 🆘 Support

### Logs to Check:
1. `logs/bot.log` - Application logs
2. `journalctl -u btc-bot` - System logs
3. `logs/bot_error.log` - Error logs
4. `trade_log.json` - Trade history

### Common Issues:

**"No trades being taken"**
→ Strategy is selective. May take hours/days between setups.
→ Check logs for "Analyzing..." messages.

**"Email not received"**
→ Check spam folder
→ Verify credentials: `python test_email.py`
→ For Gmail: Use App Password, not regular password

**"High CPU usage"**
→ Normal: 5-15%
→ If >50%: Check logs for errors

---

## 📋 Requirements

- Python 3.11+
- Internet connection
- Raspberry Pi 5 (4GB+ RAM)
- Email account (Resend or Gmail)

### Python Packages:
```
ccxt>=4.0.0
pandas>=2.0.0
pandas_ta>=0.3.14
pydantic>=2.0.0
pydantic-settings>=2.0.0
structlog>=23.0.0
python-dotenv>=1.0.0
aiosmtplib>=3.0.0
resend>=0.7.0
prometheus-client>=0.17.0
```

---

## 🎓 Learning Resources

### Understanding the Strategy:
- Read `strategies/day_trading.py` - Well commented code
- Run `backtesting/backtest.py` - See it in action
- Check `OPTIMIZATION_LESSONS.md` - Learn from mistakes

### Improving Performance:
- Use `genetic_optimizer.py` monthly
- Monitor win rate and drawdown
- Adjust risk% if needed (0.5-1.0%)

---

## ⚠️ Disclaimer

**This is a PAPER TRADING bot.**
- No real money is at risk
- Use for learning and testing only
- Results are simulated
- Past performance ≠ future results

**Before live trading:**
- Paper trade for at least 1 month
- Understand the strategy completely
- Start with very small amounts
- Never risk more than you can afford to lose

---

## 📜 License

MIT License - Feel free to modify and improve!

---

## ✅ Quick Health Check

Run this after setup:

```bash
# 1. Service running?
sudo systemctl status btc-bot | grep "active (running)"

# 2. Logs working?
test -f logs/bot.log && echo "✅ Logs OK"

# 3. Email configured?
grep -q "RESEND_API_KEY\|SMTP_USER" .env && echo "✅ Email OK"

# 4. State persisted?
test -f paper_state.json && echo "✅ State OK"
```

All ✅? **You're ready to trade!** 🚀

---

## 🎯 Next Steps

1. ✅ Set up on Raspberry Pi (`./setup_pi.sh`)
2. ✅ Configure email (`.env`)
3. ✅ Test email (`python test_email.py`)
4. ✅ Start bot (`sudo systemctl start btc-bot`)
5. ✅ Monitor (`tail -f logs/bot.log`)
6. ✅ Wait for trade emails
7. ✅ Review performance weekly
8. ✅ Re-optimize monthly (optional)

**Happy trading!** 📈💰🤖
