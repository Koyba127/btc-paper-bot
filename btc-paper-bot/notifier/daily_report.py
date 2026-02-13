import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from stats.statistics import calculate_stats, generate_equity_curve
from execution.paper_engine import TRADE_LOG_FILE, BALANCE_HISTORY_FILE, engine
from notifier.email_notifier import notifier
from utils.logger import logger
import structlog
from config import settings
import os

log = structlog.get_logger()

async def send_daily_report():
    log.info("Generating Daily Report...")
    try:
        stats = calculate_stats(TRADE_LOG_FILE, BALANCE_HISTORY_FILE)
        if not stats:
            log.info("No trades yet for report")
            msg = "No trades recorded yet."
            await notifier.send_email("Daily Report - No Activity", msg)
            return

        curve_path = generate_equity_curve(BALANCE_HISTORY_FILE)
        
        msg = f"""
        Daily Report ({settings.SYMBOL})
        --------------------------------
        Balance: {stats.get('current_balance', 0):.2f} USDT
        Total Return: {stats.get('total_return_pct', 0):.2f}%
        
        Trades: {stats.get('total_trades', 0)}
        Win Rate: {stats.get('win_rate', 0)*100:.1f}%
        Profit Factor: {stats.get('profit_factor', 0):.2f}
        Max Drawdown: {stats.get('max_drawdown_pct', 0):.2f}%
        Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}
        Expectancy: {stats.get('expectancy', 0):.2f}
        
        Open Position: {'YES' if engine.position else 'NO'}
        """
        
        attachments = [curve_path] if curve_path else []
        
        await notifier.send_email(
            f"Daily Report: {settings.SYMBOL} - {stats.get('total_return_pct', 0):.2f}%",
            msg,
            attachments=attachments
        )
        
        # Cleanup
        # if curve_path and os.path.exists(curve_path):
        #    os.remove(curve_path) 
        # Keep it for history or specialized cleanup

    except Exception as e:
        log.error("Failed to send daily report", error=str(e))

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # 08:00 MEZ (CET/CEST). 
    # Python handle timezones via timezone arg.
    # MEZ is UTC+1. So 07:00 UTC.
    # Better: use 'Europe/Berlin'
    scheduler.add_job(send_daily_report, CronTrigger(hour=8, minute=0, timezone='Europe/Berlin'))
    scheduler.start()
    log.info("Daily Report Scheduler started (08:00 MEZ)")
    return scheduler
