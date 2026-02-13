from datetime import datetime
import os
import smtplib
from email.message import EmailMessage

def current_timestamp_str() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

def format_balance(amount: float) -> str:
    return f"{amount:,.2f}"

def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"
