import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
import asyncio
from datetime import datetime
import structlog
import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from strategies.day_trading import DayTradingStrategy

log = structlog.get_logger()

async def run_backtest():
    exchange = ccxt.binance({'enableRateLimit': True})
    symbol = settings.SYMBOL
    timeframe = '15m'
    
    # Fetch 15m Data (Last 60 days approx 6000 candles)
    # 15m * 4 * 24 = 96 candles per day. 96 * 60 = 5760.
    limit = 1000
    ohlcv = []
    
    # Start date: 2 months ago
    start_time = exchange.parse8601((pd.Timestamp.now() - pd.Timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    log.info("Fetching 15m data (Last 60 days)...")
    since = start_time
    while True:
        data = exchange.fetch_ohlcv(symbol, timeframe, since, limit=limit)
        if not data:
            break
        ohlcv.extend(data)
        since = data[-1][0] + (15 * 60 * 1000) # +15m
        if len(data) < limit:
            break
            
    df_15m = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_15m['timestamp'] = pd.to_datetime(df_15m['timestamp'], unit='ms')
    df_15m.set_index('timestamp', inplace=True)
    
    # Create 1H Dataframe (Resample)
    df_1h = df_15m.resample('1h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    log.info("Data loaded", len_15m=len(df_15m), len_1h=len(df_1h))
    
    # Initialize Strategy
    strategy = DayTradingStrategy()
    
    # Pre-calculate Indicators for Speed (Vectorized)
    
    # --- 1H Context ---
    df_1h['EMA50'] = ta.ema(df_1h['close'], length=50)
    df_1h['EMA200'] = ta.ema(df_1h['close'], length=200)
    adx = ta.adx(df_1h['high'], df_1h['low'], df_1h['close'], length=14)
    if adx is not None:
        df_1h = df_1h.join(adx) # ADX_14, DMP_14, DMN_14
    
    # --- 15m Execution ---
    df_15m['EMA200'] = ta.ema(df_15m['close'], length=200)
    df_15m['RSI'] = ta.rsi(df_15m['close'], length=14)
    df_15m['ATR'] = ta.atr(df_15m['high'], df_15m['low'], df_15m['close'], length=14)
    
    # Stoch RSI
    stoch = ta.stochrsi(df_15m['close'], length=14, rsi_length=14, k=3, d=3)
    if stoch is not None:
        df_15m = df_15m.join(stoch)
    
    # Identify Col names
    k_col = [c for c in df_15m.columns if c.startswith('STOCHRSIk')][0]
    d_col = [c for c in df_15m.columns if c.startswith('STOCHRSId')][0]
    
    balance = settings.PAPER_TRADING_BALANCE
    position = None
    trades = []
    
    log.info("Starting Backtest Loop...")
    
    # Iterate through 15m candles
    # Start after warm up (200 candles)
    for i in range(200, len(df_15m)):
        current_time = df_15m.index[i]
        row_15m = df_15m.iloc[i]
        prev_15m = df_15m.iloc[i-1]
        
        # Get 1H Context
        # We need the last COMPLETED 1H candle.
        # If current time is 10:15, last completed 1H is 09:00-10:00 (timestamp 09:00, closed 10:00).
        # floor(current_time, '1h') gives 10:00. minus 1h gives 09:00.
        
        # Check alignment:
        # 15m candle at 10:15 (closes 10:30).
        # We know 1H close of 10:00.
        # So look for 1H candle with timestamp 09:00.
        
        last_hour_ts = current_time.floor('1h') - pd.Timedelta(hours=1)
        
        if last_hour_ts not in df_1h.index:
            continue
            
        row_1h = df_1h.loc[last_hour_ts]
        
        # Check Exits
        if position:
            # Check vs High/Low
            pnl = 0
            closed = False
            reason = ""
            
            if position['side'] == 'LONG':
                if row_15m['low'] <= position['sl']:
                    pnl = (position['sl'] - position['entry']) * position['size']
                    closed = True; reason = "SL"
                elif row_15m['high'] >= position['tp']:
                    pnl = (position['tp'] - position['entry']) * position['size']
                    closed = True; reason = "TP"
            else: # SHORT
                if row_15m['high'] >= position['sl']:
                    pnl = (position['entry'] - position['sl']) * position['size']
                    closed = True; reason = "SL"
                elif row_15m['low'] <= position['tp']:
                    pnl = (position['entry'] - position['tp']) * position['size']
                    closed = True; reason = "TP"
                    
            if closed:
                # Fee
                fee = (position['entry'] * position['size'] + (position['entry'] + pnl/position['size']) * position['size']) * 0.0004
                pnl -= fee
                balance += pnl
                trades.append({'time': current_time, 'pnl': pnl, 'reason': reason, 'balance': balance})
                position = None
                continue # Don't re-enter same bar
                
        # Check Entries
        if not position:
            # Replicating Strategy Logic
            # Trend + Chop Filter (ADX > 20)
            adx_val = row_1h.get('ADX_14', 0) # Assumes ADX calculated in df_1h
            trend_bullish = (row_1h['EMA50'] > row_1h['EMA200']) and (adx_val > 20)
            trend_bearish = (row_1h['EMA50'] < row_1h['EMA200']) and (adx_val > 20)
            
            atr_val = row_15m.get('ATR', 0)
            if pd.isna(atr_val): continue
            
            signal = None
            
            # LONG - Strict Stoch < 20
            stoch_k = row_15m[k_col]
            stoch_d = row_15m[d_col]
            prev_k = prev_15m[k_col]
            prev_d = prev_15m[d_col]
            
            stoch_cross_up = (stoch_k > stoch_d) and (prev_k <= prev_d)
            stoch_oversold = (stoch_k < 20) 
            
            valid_long_rsi = (row_15m['RSI'] < 60) # Room to move up
            price_above_ema = row_15m['close'] > row_15m['EMA200']
            
            if trend_bullish and price_above_ema and valid_long_rsi and stoch_cross_up and stoch_oversold:
                sl_dist = atr_val * 2.0
                entry = row_15m['close']
                sl = entry - sl_dist
                risk = entry - sl
                tp = entry + (risk * 2.0) # Aim for 2.0 RR
                signal = {'side': 'LONG', 'entry': entry, 'sl': sl, 'tp': tp}
                
            # SHORT - Strict Stoch > 80
            stoch_cross_down = (stoch_k < stoch_d) and (prev_k >= prev_d)
            stoch_overbought = (stoch_k > 80)
            
            valid_short_rsi = (row_15m['RSI'] > 40)
            price_below_ema = row_15m['close'] < row_15m['EMA200']
            
            if trend_bearish and price_below_ema and valid_short_rsi and stoch_cross_down and stoch_overbought:
                sl_dist = atr_val * 2.0
                entry = row_15m['close']
                sl = entry + sl_dist
                risk = sl - entry
                tp = entry - (risk * 2.0)
                signal = {'side': 'SHORT', 'entry': entry, 'sl': sl, 'tp': tp}
                
            if signal:
                risk_amt = balance * 0.01 # 1% Risk
                dist = abs(signal['entry'] - signal['sl'])
                if dist > 0:
                    size = risk_amt / dist
                    position = {
                        'side': signal['side'],
                        'entry': signal['entry'],
                        'sl': signal['sl'],
                        'tp': signal['tp'],
                        'size': size
                    }
                    log.info(f"Open {signal['side']} at {current_time}", price=signal['entry'])

    log.info("Backtest Complete", final_balance=balance, trades=len(trades))
    return trades

if __name__ == "__main__":
    t = asyncio.run(run_backtest())
    if t:
        df = pd.DataFrame(t)
        print(f"\nTotal Trades: {len(t)}")
        print(f"Final Balance: {t[-1]['balance']:.2f}")
        print(f"Win Rate: {(len(df[df['pnl']>0])/len(df))*100:.2f}%")
        print(f"Total PnL: {df['pnl'].sum():.2f}")
    else:
        print("No trades.")
