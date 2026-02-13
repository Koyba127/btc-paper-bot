import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
import asyncio
from datetime import datetime, timedelta
import structlog
import matplotlib.pyplot as plt
import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from strategies.multi_timeframe import MultiTimeframeStrategy

log = structlog.get_logger()

async def run_backtest():
    exchange = ccxt.binance()
    symbol = settings.SYMBOL
    timeframe = '1h'
    timeframe_4h = '4h'
    
    # Fetch 1h Data
    since = exchange.parse8601('2025-01-01T00:00:00Z')
    log.info("Fetching 1h data...")
    ohlcv = []
    while True:
        data = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
        if not data:
            break
        ohlcv.extend(data)
        since = data[-1][0] + 3600000
        if len(data) < 1000:
            break
            
    df_1h = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_1h['timestamp'] = pd.to_datetime(df_1h['timestamp'], unit='ms')
    df_1h.set_index('timestamp', inplace=True)
    
    # Resample to 4h
    df_4h = df_1h.resample('4h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    strategy = MultiTimeframeStrategy()
    
    balance = settings.PAPER_TRADING_BALANCE
    position = None
    trades = []
    
    log.info("Starting Backtest Loop...")
    
    # Pre-calculate Indicators
    # 4h
    df_4h['EMA50'] = ta.ema(df_4h['close'], length=50)
    df_4h['EMA200'] = ta.ema(df_4h['close'], length=200)
    adx = ta.adx(df_4h['high'], df_4h['low'], df_4h['close'], length=14)
    df_4h = df_4h.join(adx)

    # 1h
    df_1h['RSI'] = ta.rsi(df_1h['close'], length=14)
    macd = ta.macd(df_1h['close'])
    df_1h = df_1h.join(macd)
    df_1h['VolMA20'] = ta.sma(df_1h['volume'], length=20)
    atr = ta.atr(df_1h['high'], df_1h['low'], df_1h['close'], length=14)
    df_1h = df_1h.join(atr) # Adds ATRe_14 usually, check col name

    # Loop
    # Start after warm up
    start_idx = 200 # Need 200 for EMA200
    
    for i in range(start_idx, len(df_1h)):
        # Simulate "Current State"
        # We need the indicators as they were KNOWN at this time.
        # Since we pre-calculated, df_1h.iloc[i] contains value at Close of candle i.
        # Strategy says "Entry = 1h Close". So we trade based on row i values.
        
        current_time = df_1h.index[i]
        
        # Get 4h data available at this time
        # The last closed 4h candle is the one where timestamp + 4h <= current_time
        # Or simply, reindex/ffill.
        # We need the row from df_4h that corresponds to the 4h period *before* or *containing*?
        # If we are at 13:00 (1h close), the 4h candle 08:00-12:00 is closed. Can use it.
        # The 12:00-16:00 is open.
        # So we look for df_4h.index <= current_time - 4h? No.
        # floor to 4h.
        
        # Simple lookup:
        # If we are at 10:00. Last closed 4h is 08:00 (if 4h logic implies 00, 04, 08).
        
        # Let's align indices.
        # df_4h is indexed by start time usually?
        # Resample default uses left label. So 08:00 row covers 08:00-12:00.
        # At 12:00 close, 08:00 row is finished.
        
        # Strategy logic requires passing "df_4h". 
        # But we can just pass the relevant slice to the strategy? No, strategy calculates indicators.
        # But here max speed: we already calculated.
        
        # Re-implement Strategy logic inline for speed or Mock strategy?
        # Let's stick to reading the pre-calc values.
        
        row_1h = df_1h.iloc[i]
        
        # Find relevant 4h row
        # Time of 1h close = current_time (if index is close time? CCXT index is Open Time).
        # So row i is candle starting at T. Closes at T+1h.
        # We trade at T+1h? Or at Open of T+1?
        # "Entry-Preis = aktueller Close des 1h-Candles".
        # So at end of candle i.
        
        # 4h alignment:
        # If 1h candle is 11:00-12:00.
        # 4h candle 08:00-12:00 closes at 12:00.
        # So at 12:00 we have a fresh 4h close.
        # If 1h candle is 10:00-11:00. 4h candle 08:00-12:00 is still open.
        # We must use previous 4h (04:00-08:00).
        
        # 4h index to use: floor(current_time) - 4h if not exact match?
        # Actually simplest is `asof`.
        # But we need "closed" 4h.
        # If `current_time` (open) is 11:00. Close is 12:00.
        # At 12:00, 08:00 candle closes.
        # So we want 4h candle starting at 08:00.
        
        # If `current_time` (open) is 10:00. Close is 11:00.
        # At 11:00, 08:00 candle is OPEN.
        # We want 4h candle starting at 04:00.
        
        # Logic: last_closed_4h_idx = (current_time + 1h) floor 4h - 4h.
        
        close_time = current_time + pd.Timedelta(hours=1)
        # Round close_time down to 4h
        floored_4h = close_time.floor('4h')
        
        # If close_time is exactly on 4h boundary (e.g. 12:00), then 08:00-12:00 is closed.
        # Start time of that candle is 08:00. which is 12:00 - 4h.
        if close_time == floored_4h:
             target_4h_start = close_time - pd.Timedelta(hours=4)
        else:
             # Candle 08:00-12:00. We are at 11:00. Close time 12:00. 
             # Wait, if we are at 10:00 (Open). Close 11:00.
             # 11:00 floor 4h is 08:00.
             # 08:00 candle is OPEN.
             # We need 04:00 candle. (08:00 - 4h).
             target_4h_start = floored_4h - pd.Timedelta(hours=4)
             
        if target_4h_start not in df_4h.index:
            continue
            
        row_4h = df_4h.loc[target_4h_start]
        
        # Logic Check
        # Trend
        trend_long = (row_4h['EMA50'] > row_4h['EMA200']) and (row_4h['ADX_14'] > 22)
        trend_short = (row_4h['EMA50'] < row_4h['EMA200']) and (row_4h['ADX_14'] > 22)
        
        # Momentum
        # Prev values
        if i == 0: continue
        prev_row_1h = df_1h.iloc[i-1]
        
        # Vol
        vol_ok = row_1h['volume'] > row_1h['VolMA20']
        
        # Long
        rsi_long = (30 <= row_1h['RSI'] <= 40)
        # MACD lines: MACD_12_26_9, MACDh..., MACDs...
        # Bull Cross Check
        macd_long = (row_1h['MACDh_12_26_9'] > 0) and (prev_row_1h['MACDh_12_26_9'] <= 0)
        
        # Short
        rsi_short = (60 <= row_1h['RSI'] <= 70)
        macd_short = (row_1h['MACDh_12_26_9'] < 0) and (prev_row_1h['MACDh_12_26_9'] >= 0)
        
        current_price = row_1h['close']
        current_atr = row_1h['ATRr_14'] if 'ATRr_14' in row_1h else row_1h.get('ATR_14', 0)
        
        # Check Exits if Position Open
        if position:
            # Check SL/TP against High/Low of THIS candle?
            # Or assume we held through?
            # "Interner Paper-Trading-Engine... prüft bei jedem Preis-Update".
            # Backtest approximation: Check Low/High.
            
            # Simple assumption: If Low < SL -> Stopped. If High > TP -> Profit.
            # If both, assume SL first (conservative) unless Open is closer to TP?
            # Or assume worst case.
            
            pnl = 0
            closed = False
            reason = ""
            
            if position['side'] == 'LONG':
                if row_1h['low'] <= position['sl']:
                    pnl = (position['sl'] - position['entry']) * position['size']
                    closed = True
                    reason = "SL"
                elif row_1h['high'] >= position['tp']:
                    pnl = (position['tp'] - position['entry']) * position['size']
                    closed = True
                    reason = "TP"
            else:
                if row_1h['high'] >= position['sl']:
                    pnl = (position['entry'] - position['sl']) * position['size']
                    closed = True
                    reason = "SL"
                elif row_1h['low'] <= position['tp']:
                    pnl = (position['entry'] - position['tp']) * position['size']
                    closed = True
                    reason = "TP"
            
            if closed:
                balance += pnl
                trades.append({'pnl': pnl, 'reason': reason, 'balance': balance})
                position = None
                
        # Check Entry if No Position
        if not position:
            signal = None
            if trend_long and rsi_long and macd_long and vol_ok:
                log.info(f"Long Signal at {current_time}", price=current_price)
                sl = current_price - (current_atr * 1.5)
                risk = current_price - sl
                tp = current_price + (risk * 2.8)
                signal = {'side': 'LONG', 'price': current_price, 'sl': sl, 'tp': tp}
                
            elif trend_short and rsi_short and macd_short and vol_ok:
                log.info(f"Short Signal at {current_time}", price=current_price)
                sl = current_price + (current_atr * 1.5)
                risk = sl - current_price
                tp = current_price - (risk * 2.8)
                signal = {'side': 'SHORT', 'price': current_price, 'sl': sl, 'tp': tp}
            
            if signal:
                risk_amt = balance * 0.0075
                dist = abs(signal['price'] - signal['sl'])
                if dist > 0:
                    size = risk_amt / dist
                    position = {
                        'side': signal['side'],
                        'entry': signal['price'],
                        'sl': signal['sl'],
                        'tp': signal['tp'],
                        'size': size
                    }

    log.info("Backtest Complete", final_balance=balance, trades=len(trades))
    return trades

if __name__ == "__main__":
    trades = asyncio.run(run_backtest())
    if trades:
        balance = trades[-1]['balance']
        print(f"\nBacktest Summary:\nTotal Trades: {len(trades)}\nFinal Balance: {balance:.2f} USDT")
        df = pd.DataFrame(trades)
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]
        win_rate = len(wins) / len(trades) if len(trades) > 0 else 0
        print(f"Win Rate: {win_rate*100:.2f}%")
        print(f"Total PnL: {df['pnl'].sum():.2f}")
    else:
        print("\nNo trades executed in backtest.")

