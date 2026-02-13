import json
import csv
import os
import asyncio
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel
from config import settings
from utils.logger import logger
from utils.helpers import format_balance, format_pct
from strategies.multi_timeframe import MultiTimeframeStrategy, Signal
from notifier.email_notifier import notifier
from monitoring import metrics
import pandas as pd

TRADE_LOG_FILE = "trade_log.json"
BALANCE_HISTORY_FILE = "balance_history.csv"

class Position(BaseModel):
    id: str
    symbol: str
    side: str  # LONG or SHORT
    entry_price: float
    size: float
    sl: float
    tp: float
    open_time: str
    status: str = "OPEN"  # OPEN, CLOSED
    pnl: float = 0.0
    exit_price: float = 0.0
    exit_time: str = ""
    exit_reason: str = ""  # TP, SL, MANUAL
    commission: float = 0.0

class PaperEngine:
    def __init__(self):
        self.strategy = MultiTimeframeStrategy()
        self.balance = settings.PAPER_TRADING_BALANCE
        self.position: Optional[Position] = None
        self.load_state()
        self.lock = asyncio.Lock()
        metrics.BALANCE.set(self.balance)
        if self.position:
            metrics.POSITION_SIZE.set(self.position.size)
        else:
            metrics.POSITION_SIZE.set(0)

    def load_state(self):
        """Recover balance and open position from files."""
        # Load Balance History
        if os.path.exists(BALANCE_HISTORY_FILE):
            try:
                df = pd.read_csv(BALANCE_HISTORY_FILE)
                if not df.empty:
                    self.balance = float(df.iloc[-1]['balance'])
                    logger.info("Restored balance", balance=self.balance)
            except Exception as e:
                logger.error("Error loading balance history", error=str(e))

        # Load Trade Log to find open position
        if os.path.exists(TRADE_LOG_FILE):
            try:
                with open(TRADE_LOG_FILE, 'r') as f:
                    trades = json.load(f)
                    if trades:
                        last_trade = trades[-1]
                        if last_trade['status'] == 'OPEN':
                            self.position = Position(**last_trade)
                            logger.info("Restored open position", position=self.position.dict())
            except Exception as e:
                logger.error("Error loading trade log", error=str(e))
                # Create empty file if corrupted
                with open(TRADE_LOG_FILE, 'w') as f:
                    json.dump([], f)

    async def save_trade(self, position: Position):
        """Append or update trade in log."""
        trades = []
        if os.path.exists(TRADE_LOG_FILE):
            try:
                with open(TRADE_LOG_FILE, 'r') as f:
                    trades = json.load(f)
            except:
                trades = []
        
        # Check if updating existing
        found = False
        for i, t in enumerate(trades):
            if t['id'] == position.id:
                trades[i] = position.dict()
                found = True
                break
        if not found:
            trades.append(position.dict())

        with open(TRADE_LOG_FILE, 'w') as f:
            json.dump(trades, f, indent=4)
        
        # Update balance history if closed
        if position.status == 'CLOSED':
            self.save_balance()

    def save_balance(self):
        file_exists = os.path.exists(BALANCE_HISTORY_FILE)
        with open(BALANCE_HISTORY_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'balance'])
            writer.writerow([datetime.utcnow().isoformat(), self.balance])
        metrics.BALANCE.set(self.balance)

    async def process_ticker(self, ticker: dict):
        """Check SL/TP on price update."""
        if not self.position or self.position.status != 'OPEN':
            metrics.OPEN_REALIZED_PNL.set(0)
            return

        async with self.lock:
            current_price = ticker['last']
            if not current_price:
                return

            # Update Metrics (PnL)
            open_pnl = 0
            if self.position.side == 'LONG':
                open_pnl = (current_price - self.position.entry_price) * self.position.size
            else:
                open_pnl = (self.position.entry_price - current_price) * self.position.size
            metrics.OPEN_REALIZED_PNL.set(open_pnl)

            # Check SL
            hit_sl = False
            hit_tp = False
            
            if self.position.side == 'LONG':
                if current_price <= self.position.sl:
                    hit_sl = True
                elif current_price >= self.position.tp:
                    hit_tp = True
            else: # SHORT
                if current_price >= self.position.sl:
                    hit_sl = True
                elif current_price <= self.position.tp:
                    hit_tp = True
            
            if hit_sl or hit_tp:
                reason = "SL" if hit_sl else "TP"
                await self.close_position(current_price, reason)

    async def close_position(self, price: float, reason: str):
        logger.info("Closing position", reason=reason, price=price)
        pos = self.position
        pos.exit_price = price
        pos.exit_time = datetime.utcnow().isoformat()
        pos.exit_reason = reason
        pos.status = "CLOSED"
        
        # Calculate PnL
        raw_pnl = 0
        if pos.side == 'LONG':
            raw_pnl = (pos.exit_price - pos.entry_price) * pos.size
        else:
            raw_pnl = (pos.entry_price - pos.exit_price) * pos.size
            
        # Fees: 0.04% on Entry value + 0.04% on Exit value
        entry_val = pos.entry_price * pos.size
        exit_val = pos.exit_price * pos.size
        fee = (entry_val + exit_val) * settings.TAKER_FEE
        
        pos.commission = fee
        pos.pnl = raw_pnl - fee
        
        self.balance += pos.pnl
        await self.save_trade(pos)
        self.position = None
        
        metrics.LAST_TRADE_PNL.set(pos.pnl)
        metrics.POSITION_SIZE.set(0)
        metrics.BALANCE.set(self.balance)
        metrics.OPEN_REALIZED_PNL.set(0)
        
        logger.info("Position Closed", pnl=pos.pnl, new_balance=self.balance)
        
        # Notify
        msg = f"""
        Position Closed ({reason})
        Symbol: {pos.symbol}
        Side: {pos.side}
        Entry: {pos.entry_price}
        Exit: {pos.exit_price}
        PnL: {format_balance(pos.pnl)} USDT
        New Balance: {format_balance(self.balance)} USDT
        """
        await notifier.send_email(f"Trade Closed: {reason} {pos.pnl:.2f}", msg)

    async def process_ohlcv(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame):
        """Strategy Check on new Candle."""
        if self.position:
            return  # Max 1 position

        signal = self.strategy.analyze(df_1h, df_4h)
        if signal:
            await self.open_position(signal)

    async def open_position(self, signal: Signal):
        async with self.lock:
            if self.position: return

            risk_amount = self.balance * settings.RISK_PERCENT / 100
            # Distance to SL
            dist = abs(signal.price - signal.sl)
            if dist == 0:
                logger.error("Invalid SL distance 0")
                return

            size = risk_amount / dist
            
            entry_val = signal.price * size
            if entry_val > self.balance * 0.98:
                size = (self.balance * 0.98) / signal.price

            # Create Position
            pos = Position(
                id=f"{int(datetime.utcnow().timestamp())}",
                symbol=settings.SYMBOL,
                side=signal.action,
                entry_price=signal.price,
                size=size,
                sl=signal.sl,
                tp=signal.tp,
                open_time=datetime.utcnow().isoformat(),
                status="OPEN"
            )
            
            logger.info("Opening Position", side=pos.side, size=pos.size, price=pos.entry_price)
            self.position = pos
            await self.save_trade(pos)
            
            metrics.POSITION_SIZE.set(pos.size)
            metrics.OPEN_REALIZED_PNL.set(0)
            
            # Notify
            rr = abs(signal.tp - signal.price) / abs(signal.price - signal.sl)
            msg = f"""
            NEW SIGNAL: {signal.action}
            Symbol: {settings.SYMBOL}
            Entry: {signal.price}
            SL: {signal.sl}
            TP: {signal.tp}
            R:R: {rr:.2f}
            Risk: {settings.RISK_PERCENT}%
            Balance: {format_balance(self.balance)}
            Reason: {signal.reason}
            """
            await notifier.send_email(f"New Trade: {signal.action}", msg)

engine = PaperEngine()
