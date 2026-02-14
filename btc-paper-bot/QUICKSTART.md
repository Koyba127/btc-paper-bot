# 🚀 Quick Start Guide

## Get Your Bot Running in 5 Minutes

---

## On Raspberry Pi:

### 1️⃣ Transfer files
```bash
# Option 1: Git clone (if you have a repo)
git clone <your-repo> ~/btc-paper-bot

# Option 2: SCP from Windows
scp -r e:\python\btc-paper-bot pi@raspberrypi.local:~/
```

### 2️⃣ Run setup
```bash
cd ~/btc-paper-bot
chmod +x setup_pi.sh
./setup_pi.sh
```

### 3️⃣ Configure email
```bash
nano .env
```

Add your email credentials:
```
# Resend (recommended)
RESEND_API_KEY=re_xxxxx
EMAIL_TO=your-email@example.com

# OR Gmail
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_TO=your-email@example.com
```

### 4️⃣ Test email
```bash
source venv/bin/activate
python test_email.py
```

### 5️⃣ Start bot
```bash
sudo systemctl enable btc-bot
sudo systemctl start btc-bot
```

### ✅ Done!

Check status:
```bash
sudo systemctl status btc-bot
tail -f logs/bot.log
```

---

## 📧 Email Setup Help

### Resend (Recommended):
1. Go to https://resend.com
2. Sign up (free)
3. Get API key
4. Add to `.env`: `RESEND_API_KEY=re_xxxxx`

### Gmail:
1. Go to https://myaccount.google.com/apppasswords
2. Create "App Password"
3. Add to `.env`: `SMTP_PASSWORD=abcd-efgh-ijkl-mnop`

---

## 🎯 What to Expect

**Within 24 hours:**
- Bot finds 0-2 trade setups
- You receive email for each trade
- Balance updates after each trade

**Performance (60 days):**
- ~50 trades total
- 46% win rate
- +13% profit
- $10,000 → $11,300

---

## 📱 Useful Commands

```bash
# View logs
tail -f logs/bot.log

# Restart bot
sudo systemctl restart btc-bot

# Stop bot
sudo systemctl stop btc-bot

# Check status
sudo systemctl status btc-bot
```

---

**Full guide: `RASPBERRY_PI_SETUP.md`**
