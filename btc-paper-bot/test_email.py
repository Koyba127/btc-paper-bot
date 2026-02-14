#!/usr/bin/env python3
"""
Email Configuration Test Script
Tests both Resend API and SMTP fallback
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from notifier.email_notifier import notifier
import structlog

log = structlog.get_logger()

async def test_email():
    """Test email notification system."""
    
    print("=" * 60)
    print("BTC Bot - Email System Test")
    print("=" * 60)
    print()
    
    # Show configuration
    print("📧 Email Configuration:")
    print(f"  Resend API Key: {'✅ Configured' if settings.RESEND_API_KEY else '❌ Not set'}")
    print(f"  From: {settings.EMAIL_FROM}")
    print(f"  To: {settings.EMAIL_TO}")
    print()
    print(f"  SMTP Server: {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
    print(f"  SMTP User: {'✅ Configured' if settings.SMTP_USER else '❌ Not set'}")
    print(f"  SMTP Password: {'✅ Configured' if settings.SMTP_PASSWORD else '❌ Not set'}")
    print()
    
    # Check if at least one method is configured
    if not settings.RESEND_API_KEY and not (settings.SMTP_USER and settings.SMTP_PASSWORD):
        print("❌ ERROR: No email method configured!")
        print()
        print("Please configure either:")
        print("1. Resend API (recommended):")
        print("   RESEND_API_KEY=re_xxxxx")
        print("   EMAIL_FROM=onboarding@resend.dev")
        print("   EMAIL_TO=your-email@example.com")
        print()
        print("2. SMTP (Gmail):")
        print("   SMTP_USER=your-gmail@gmail.com")
        print("   SMTP_PASSWORD=your-app-password")
        print("   EMAIL_TO=your-email@example.com")
        print()
        return False
    
    # Send test email
    print("📤 Sending test email...")
    print()
    
    subject = "🧪 BTC Bot - Email Test"
    body = """
This is a test email from your BTC Paper Trading Bot!

✅ If you're reading this, your email notifications are working correctly.

Test Details:
- Bot is running on Raspberry Pi 5
- Paper trading mode enabled
- Email system online
- Strategy: Day Trading (15m/1H)

You will receive emails for:
📈 LONG trade signals
📉 SHORT trade signals
✅ Profitable trade closures
❌ Stop loss hits
🎯 Take profit targets

The bot is ready to trade!

---
BTC Paper Trading Bot v1.0
    """.strip()
    
    try:
        await notifier.send_email(subject, body)
        print("✅ Test email sent successfully!")
        print()
        print(f"📬 Check your inbox at: {settings.EMAIL_TO}")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        print()
        return False

if __name__ == "__main__":
    print()
    result = asyncio.run(test_email())
    
    if result:
        print("=" * 60)
        print("✅ EMAIL SYSTEM READY!")
        print("=" * 60)
        print()
        print("Your bot will send notifications for:")
        print("  • Trade entries (LONG/SHORT)")
        print("  • Trade exits (TP/SL)")
        print("  • Balance updates")
        print()
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ EMAIL SETUP INCOMPLETE")
        print("=" * 60)
        print()
        print("Edit your .env file and try again:")
        print("  nano .env")
        print()
        sys.exit(1)
