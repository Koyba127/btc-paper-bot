# ✅ Raspberry Pi Deployment Checklist

## Pre-Deployment (On Windows)

### Files Ready:
- [x] All Python code tested
- [x] Strategy optimized (46% win rate, +13% profit)
- [x] Email system configured
- [x] Deployment scripts created
- [x] Documentation complete

### What to Transfer:
```
btc-paper-bot/
├── All Python files (.py)
├── requirements.txt
├── .env.example (NOT .env - create fresh on Pi)
├── All markdown docs (.md)
├── All shell scripts (.sh)
└── All subdirectories (strategies/, execution/, etc.)
```

**DO NOT transfer:**
- `.env` (contains your credentials - create fresh on Pi)
- `.venv/` or `venv/` (rebuild on Pi)
- `__pycache__/` (auto-generated)
- `*.pyc` files
- `logs/` (will be created on Pi)

---

## On Raspberry Pi

### Step 1: Transfer Files ✅

**Method 1: SCP (from Windows)**
```powershell
# PowerShell on Windows
scp -r e:\python\btc-paper-bot pi@raspberrypi.local:~/
```

**Method 2: Git Clone**
```bash
# On Raspberry Pi
git clone <your-repo-url> ~/btc-paper-bot
```

**Method 3: USB Drive**
1. Copy folder to USB drive
2. Plug into Raspberry Pi
3. Copy to `/home/pi/btc-paper-bot`

---

### Step 2: Run Setup Script ✅

```bash
cd ~/btc-paper-bot
chmod +x setup_pi.sh
./setup_pi.sh
```

**This will:**
- [x] Update system packages
- [x] Install Python dependencies
- [x] Create virtual environment
- [x] Set up systemd service
- [x] Create log directories
- [x] Set permissions

**Time: ~5-10 minutes**

---

### Step 3: Configure Email ✅

```bash
nano .env
```

**Choose ONE method:**

#### Option A: Resend (Recommended)
```env
RESEND_API_KEY=re_your_actual_key_here
EMAIL_FROM=onboarding@resend.dev
EMAIL_TO=your-email@example.com
```

Get API key: https://resend.com

#### Option B: Gmail SMTP
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=abcd-efgh-ijkl-mnop
EMAIL_TO=your-email@example.com
```

Get App Password: https://myaccount.google.com/apppasswords

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

### Step 4: Test Email ✅

```bash
source venv/bin/activate
python test_email.py
```

**Expected output:**
```
✅ Test email sent successfully!
📬 Check your inbox at: your-email@example.com
```

**If failed:**
- Check spam folder
- Verify credentials in `.env`
- For Gmail: Ensure App Password used (not regular password)
- Try: `nano .env` and re-enter credentials

---

### Step 5: Test Bot Manually ✅

```bash
# Should already be in venv from previous step
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
[info] Analyzing...
```

**Let it run for 1-2 minutes to verify:**
- [x] No errors
- [x] Connected to Binance
- [x] Receiving price data
- [x] Analyzing candles

**Press Ctrl+C to stop**

---

### Step 6: Enable Auto-Start ✅

```bash
# Enable service (starts on boot)
sudo systemctl enable btc-bot

# Start service now
sudo systemctl start btc-bot

# Verify it's running
sudo systemctl status btc-bot
```

**Expected output:**
```
● btc-bot.service - BTC Paper Trading Bot
   Active: active (running) since Fri 2026-02-14 13:00:00 CET
```

---

### Step 7: Monitor Initial Run ✅

```bash
# Watch live logs
tail -f logs/bot.log
```

**What to look for:**
- [x] "Connected to Binance WebSocket"
- [x] "Analyzing..." messages every 15 minutes
- [x] No error messages
- [x] Price updates streaming

**Leave it running for 30 minutes minimum**

---

### Step 8: Verify Email on First Trade ✅

**Within 24-48 hours, you should receive an email for the first trade.**

When you receive it:
- [x] Subject starts with "📈 LONG" or "📉 SHORT"
- [x] Contains entry price
- [x] Contains stop loss and take profit
- [x] Email is well-formatted

**If no email after 48 hours:**
- That's normal! Strategy is selective
- Check logs: `grep "Open" logs/bot.log`
- If trades in logs but no email → Re-test email system

---

## Post-Deployment Monitoring

### Daily Check (30 seconds):
```bash
sudo systemctl status btc-bot
```

Should show "active (running)"

### Weekly Review (5 minutes):
```bash
# Check trades
cat trade_log.json | python -m json.tool | tail -n 50

# Check balance
grep "Balance" logs/bot.log | tail -n 5

# Check for errors
grep "ERROR\|error" logs/bot.log | tail -n 20
```

### Monthly Tasks (15 minutes):
1. Review performance in email history
2. Calculate actual win rate and profit
3. Consider re-optimization if performance declined
4. Update system and dependencies:
   ```bash
   sudo apt update && sudo apt upgrade -y
   source venv/bin/activate
   pip install --upgrade -r requirements.txt
   sudo systemctl restart btc-bot
   ```

---

## Troubleshooting

### Bot Crashed:
```bash
# Check what happened
journalctl -u btc-bot -n 100

# Restart
sudo systemctl restart btc-bot
```

### High CPU Usage:
```bash
# Check usage
top -p $(pgrep -f "python main.py")

# Normal: 5-15%
# If >50%: Something's wrong, check logs
```

### Out of Disk Space:
```bash
# Check space
df -h

# Clean old logs (if needed)
find logs/ -name "*.log" -mtime +30 -delete
```

### Email Stopped Working:
```bash
# Re-test
source venv/bin/activate
python test_email.py

# If failed: Check API key/password hasn't expired
nano .env
```

---

## Security Checklist

- [ ] `.env` file permissions set to 600
  ```bash
  chmod 600 .env
  ```

- [ ] SSH password login disabled (use keys)
  ```bash
  # Generate key on your computer
  ssh-keygen -t ed25519
  
  # Copy to Pi
  ssh-copy-id pi@raspberrypi.local
  
  # Disable password login
  # sudo nano /etc/ssh/sshd_config
  # Set: PasswordAuthentication no
  ```

- [ ] System firewall enabled (optional)
  ```bash
  sudo apt install ufw
  sudo ufw allow 22  # SSH
  sudo ufw enable
  ```

- [ ] Regular updates scheduled
  ```bash
  # Auto-updates (optional)
  sudo apt install unattended-upgrades
  sudo dpkg-reconfigure --priority=low unattended-upgrades
  ```

---

## Performance Expectations

### Normal Operation:
| Metric | Expected |
|--------|----------|
| CPU Usage | 5-15% |
| Memory | 200-400MB |
| Network | <1 Mbps |
| Disk I/O | Minimal |
| Trades/Day | 0.5-1.5 |
| Emails/Day | 1-3 |

### Warning Signs:
| Issue | Cause | Fix |
|-------|-------|-----|
| CPU >50% | Infinite loop | Check logs, restart |
| Memory >1GB | Memory leak | Restart bot |
| No trades 7+ days | Market conditions | Normal, wait |
| Emails stopped | API key expired | Update .env |

---

## Backup Plan

### Daily Auto-Backup (Recommended):
```bash
# Create backup script
nano ~/backup_bot.sh
```

```bash
#!/bin/bash
cd ~/btc-paper-bot
tar -czf ~/backups/bot-$(date +%Y%m%d).tar.gz \
    .env trade_log.json paper_state.json logs/
# Keep last 7 days only
find ~/backups -name "bot-*.tar.gz" -mtime +7 -delete
```

```bash
chmod +x ~/backup_bot.sh

# Add to crontab (runs daily at 3am)
crontab -e
# Add line: 0 3 * * * ~/backup_bot.sh
```

---

## Final Verification

Run this command to verify everything:

```bash
cd ~/btc-paper-bot
echo "=== System Check ===" && \
systemctl is-active btc-bot && echo "✅ Service running" || echo "❌ Service not running" && \
test -f .env && echo "✅ .env configured" || echo "❌ .env missing" && \
test -d venv && echo "✅ Venv exists" || echo "❌ Venv missing" && \
test -f logs/bot.log && echo "✅ Logs working" || echo "❌ No logs" && \
test -f paper_state.json && echo "✅ State persisted" || echo "⚠️  No trades yet" && \
tail -n 1 logs/bot.log | grep -q "Analyzing" && echo "✅ Bot analyzing" || echo "⚠️  Check logs" && \
echo "=== All checks complete ==="
```

**If all show ✅ → You're fully deployed!** 🎉

---

## Support Resources

### Documentation:
- `README.md` - Project overview
- `QUICKSTART.md` - 5-minute setup
- `RASPBERRY_PI_SETUP.md` - Full deployment guide
- `OPTIMIZATION_COMPLETE_GUIDE.md` - Parameter tuning

### Files to Monitor:
- `logs/bot.log` - Main application log
- `trade_log.json` - All trades
- `paper_state.json` - Current state

### Commands:
```bash
# Status
sudo systemctl status btc-bot

# Logs
tail -f logs/bot.log
journalctl -u btc-bot -f

# Restart
sudo systemctl restart btc-bot

# Stop
sudo systemctl stop btc-bot
```

---

## 🎯 Success Criteria

Your deployment is successful when:

- [x] Bot runs as systemd service
- [x] Auto-starts on boot
- [x] Receives market data continuously
- [x] Sends test email successfully
- [x] Logs are being written
- [x] No errors in logs
- [x] CPU usage is normal (5-15%)
- [x] Memory usage is stable (<400MB)
- [x] First trade email received (within 48h)

---

**Once all items are checked, you're LIVE!** 🚀

Sit back, relax, and wait for the trade emails. The bot will:
1. Monitor BTC 24/7
2. Find high-probability setups
3. Email you for each trade
4. Manage risk automatically
5. Log everything for review

**Happy trading!** 📈💰
