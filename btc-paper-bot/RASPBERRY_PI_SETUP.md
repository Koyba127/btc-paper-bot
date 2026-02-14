# 🚀 Raspberry Pi 5 Deployment Guide

## Complete Setup & Configuration for Paper Trading Bot

---

## 📋 Prerequisites

### Hardware:
- ✅ Raspberry Pi 5 (4GB+ RAM recommended)
- ✅ MicroSD card (32GB+ recommended)
- ✅ Power supply
- ✅ Internet connection (Ethernet or WiFi)

### Software:
- ✅ Raspberry Pi OS (Bookworm or later)
- ✅ SSH access (optional but recommended)

---

## 🔧 Installation Steps

### Step 1: Transfer Files to Raspberry Pi

**Option A: Using Git (Recommended)**
```bash
# On your Raspberry Pi
cd ~
git clone <your-repo-url> btc-paper-bot
cd btc-paper-bot
```

**Option B: Using SCP (from Windows)**
```powershell
# From Windows (PowerShell)
scp -r e:\python\btc-paper-bot pi@raspberrypi.local:~/btc-paper-bot
```

**Option C: Using WinSCP or FileZilla**
- Connect to your Raspberry Pi
- Upload the entire `btc-paper-bot` folder to `/home/pi/`

---

### Step 2: Run Automated Setup

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Navigate to bot directory
cd ~/btc-paper-bot

# Make setup script executable
chmod +x setup_pi.sh

# Run setup (this will take 5-10 minutes)
./setup_pi.sh
```

**What this does:**
- ✅ Updates system packages
- ✅ Installs Python 3.11+
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Creates systemd service
- ✅ Sets up logging
- ✅ Configures auto-start

---

### Step 3: Configure Email Notifications

Edit the `.env` file with your credentials:

```bash
nano .env
```

**For Resend (Recommended - No Limits):**
```bash
# Get API key from: https://resend.com
RESEND_API_KEY=re_your_actual_api_key_here
EMAIL_FROM=onboarding@resend.dev
EMAIL_TO=your-email@example.com
```

**For Gmail SMTP (Fallback):**
```bash
# Use Gmail App Password (not your regular password!)
# Create at: https://myaccount.google.com/apppasswords
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=abcd-efgh-ijkl-mnop
EMAIL_TO=your-email@example.com
```

**Other Settings:**
```bash
# Trading Configuration
PAPER_TRADING_BALANCE=10000.0  # Starting balance
RISK_PERCENT=0.75              # Risk 0.75% per trade
SYMBOL=BTC/USDT
LOG_LEVEL=INFO
```

**Save with:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

### Step 4: Test Email System

```bash
# Activate environment
source venv/bin/activate

# Test email notifications
python test_email.py
```

**Expected output:**
```
✅ Test email sent successfully!
📬 Check your inbox at: your-email@example.com
```

If you don't receive the email:
1. Check spam folder
2. Verify credentials in `.env`
3. For Gmail: Ensure "App Password" is used (not regular password)
4. For Resend: Verify API key from dashboard

---

### Step 5: Test the Bot Manually

```bash
# Start bot in foreground (debugging mode)
python main.py
```

**Expected output:**
```
[info] Starting BTC Paper Trading Bot
[info] Strategy: DayTradingStrategy
[info] Symbol: BTC/USDT, Risk: 0.75%
[info] Paper Balance: $10,000.00
[info] Email: ✅ Configured
[info] Connected to Binance WebSocket
[info] Monitoring 15m and 1H timeframes...
```

**Press Ctrl+C to stop** when you see data streaming.

---

### Step 6: Enable Auto-Start (Production Mode)

```bash
# Enable systemd service (runs at boot)
sudo systemctl enable btc-bot

# Start the service
sudo systemctl start btc-bot

# Check status
sudo systemctl status btc-bot
```

**Expected output:**
```
● btc-bot.service - BTC Paper Trading Bot
   Active: active (running) since...
```

---

## 📊 Monitoring & Management

### View Live Logs:
```bash
# Application logs
tail -f ~/btc-paper-bot/logs/bot.log

# System logs (systemd)
journalctl -u btc-bot -f

# Last 50 lines
journalctl -u btc-bot -n 50
```

### Control the Bot:
```bash
# Start
sudo systemctl start btc-bot

# Stop
sudo systemctl stop btc-bot

# Restart (after config changes)
sudo systemctl restart btc-bot

# Status
sudo systemctl status btc-bot

# Disable auto-start
sudo systemctl disable btc-bot
```

### Quick Scripts:
```bash
# Start bot
./start_bot.sh

# Stop bot
./stop_bot.sh
```

---

## 📧 Email Notifications

You'll receive emails for:

### 🎯 Trade Entries:
```
📈 LONG Signal - BTC/USDT
Entry: $95,000
Stop Loss: $93,500 (-$150 risk)
Take Profit: $98,000 (+$300 target)
Position Size: 0.1 BTC
```

### ✅ Successful Trades:
```
✅ LONG Closed - PROFIT
Entry: $95,000 → Exit: $98,000
Profit: +$300 (+3.16%)
New Balance: $10,300
```

### ❌ Stop Loss Hits:
```
❌ LONG Closed - STOP LOSS
Entry: $95,000 → Exit: $93,500
Loss: -$150 (-1.58%)
New Balance: $9,850
```

---

## 🔍 Troubleshooting

### Bot Won't Start:
```bash
# Check service status
sudo systemctl status btc-bot

# View error logs
journalctl -u btc-bot -n 100

# Check Python errors
tail -n 50 logs/bot_error.log
```

### No Email Notifications:
```bash
# Test email system
source venv/bin/activate
python test_email.py

# Common issues:
# - Wrong API key → Check Resend dashboard
# - Gmail blocking → Use App Password, not regular password
# - Spam folder → Check spam/junk folder
```

### Connection Errors:
```bash
# Test internet connection
ping binance.com

# Check if ccxt can connect
python -c "import ccxt; print(ccxt.binance().fetch_ticker('BTC/USDT'))"
```

### High CPU Usage:
```bash
# Check process
top -p $(pgrep -f "python main.py")

# Normal CPU usage: 5-15%
# If >50%: Check for bugs or reduce log verbosity
```

### Out of Memory:
```bash
# Check memory usage
free -h

# Raspberry Pi 5 should have plenty
# If low: Reduce buffer sizes in main.py
```

---

## 🎛️ Performance Optimization

### For Raspberry Pi 5:

**1. Disable Unnecessary Services:**
```bash
# If you don't need GUI
sudo systemctl set-default multi-user.target

# Disable Bluetooth (if not used)
sudo systemctl disable bluetooth
```

**2. Reduce Log Verbosity (optional):**
```bash
# In .env
LOG_LEVEL=WARNING  # Instead of INFO
```

**3. Enable CPU Governor:**
```bash
# Performance mode (slightly more power)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

---

## 🔐 Security Best Practices

### 1. Secure .env File:
```bash
chmod 600 .env  # Only you can read
```

###2. Update Regularly:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update bot dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 3. Firewall (optional):
```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow 22

# Allow Prometheus metrics (if needed)
sudo ufw allow 8000

# Enable firewall
sudo ufw enable
```

### 4. SSH Keys (instead of passwords):
```bash
# Generate key on your computer
ssh-keygen -t ed25519

# Copy to Pi
ssh-copy-id pi@raspberrypi.local
```

---

## 📈 Expected Performance

### Raspberry Pi 5 Specs:
- **CPU Usage**: 5-15% (normal)
- **Memory**: 200-400MB
- **Network**: Minimal (WebSocket data)
- **Storage**: <100MB for logs per month

### Bot Performance (60 days):
- **Trades**: ~25 per month (50 in 60 days)
- **Win Rate**: 46%
- **Monthly Return**: ~6.5% (13% in 60 days)
- **Max Drawdown**: <10%

---

## 🆘 Support & Maintenance

### Daily Checks:
```bash
# Quick status check
sudo systemctl status btc-bot
```

### Weekly Checks:
```bash
# Review trade log
cat ~/btc-paper-bot/trade_log.json

# Check balance
grep "Balance" logs/bot.log | tail -n 1
```

### Monthly Tasks:
1. Review performance in emails
2. Check if re-optimization needed
3. Update dependencies
4. Backup trade logs

---

## 📦 Backup & Recovery

### Backup Important Files:
```bash
# Create backup
tar -czf btc-bot-backup-$(date +%Y%m%d).tar.gz \
    .env \
    trade_log.json \
    paper_state.json \
    logs/

# Copy to safe location
scp btc-bot-backup-*.tar.gz user@backup-server:~/backups/
```

### Restore:
```bash
# Extract backup
tar -xzf btc-bot-backup-20260214.tar.gz

# Restart bot
sudo systemctl restart btc-bot
```

---

## ✅ Post-Setup Checklist

- [ ] Bot installed on Raspberry Pi
- [ ] Email notifications tested and working
- [ ] Bot running as systemd service
- [ ] Auto-start enabled
- [ ] Receiving emails for test trades
- [ ] Logs are being written
- [ ] CPU/memory usage is normal
- [ ] .env file is secured (chmod 600)
- [ ] Backup plan in place

---

## 🎯 You're All Set!

Your BTC Paper Trading Bot is now:
- ✅ Running 24/7 on Raspberry Pi 5
- ✅ Sending email notifications
- ✅ Auto-starting on boot
- ✅ Logging all activity
- ✅ Paper trading BTC/USDT
- ✅ Using optimized day trading strategy

**The bot will:**
1. Monitor BTC price 24/7
2. Look for high-probability setups
3. Email you when entering trades
4. Email you when closing trades
5. Manage risk automatically (0.75% per trade)
6. Log everything for review

**Just wait for emails and watch your paper balance grow!** 📈

---

**Questions? Check:**
- `OPTIMIZATION_COMPLETE_GUIDE.md` - Strategy tuning
- `OPTIMIZATION_LESSONS.md` - What to avoid
- `logs/bot.log` - Activity log
