"""
Parameter Brute-Force Optimizer for Day Trading Strategy
Tests multiple parameter combinations and finds optimal settings.

WARNING: This is in-sample optimization and can lead to overfitting!
Always validate results with out-of-sample (forward) testing.
"""
import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime
from itertools import product
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

print("=" * 80)
print("PARAMETER OPTIMIZATION - BRUTE FORCE SEARCH")
print("=" * 80)

# --- PARAMETER SEARCH SPACE (Reduced for speed) ---
PARAM_GRID = {
    'adx_threshold': [15, 18, 20, 22, 25],           # 5 values (was 6)
    'stoch_oversold': [15, 20, 25, 30],              # 4 values (was 5)
    'stoch_overbought': [70, 75, 80, 85],            # 4 values (was 5)
    'risk_reward_ratio': [1.5, 2.0, 2.5, 3.0],       # 4 values (was 6)
    'sl_atr_multiplier': [1.5, 2.0, 2.5],            # 3 values (was 5)
    'rsi_long_max': [60, 65],                        # 2 values (was 4) - less impactful
    'rsi_short_min': [35, 40],                       # 2 values (was 4) - less impactful
}
# Total: 5 × 4 × 4 × 4 × 3 × 2 × 2 = 3,840 combinations (~20 min)

# Calculate total combinations
total_combinations = np.prod([len(v) for v in PARAM_GRID.values()])
print(f"\n📊 Testing {total_combinations:,} parameter combinations...")
print(f"⏱️  Estimated time: ~{total_combinations * 0.3 / 60:.1f} minutes\n")

def run_single_backtest(params, df_15m, df_1h):
    """Run backtest with specific parameters."""
    
    # Pre-calculate all indicators (vectorized for speed)
    df_1h_copy = df_1h.copy()
    df_15m_copy = df_15m.copy()
    
    # 1H indicators
    df_1h_copy['EMA50'] = ta.ema(df_1h_copy['close'], length=50)
    df_1h_copy['EMA200'] = ta.ema(df_1h_copy['close'], length=200)
    adx_result = ta.adx(df_1h_copy['high'], df_1h_copy['low'], df_1h_copy['close'], length=14)
    if adx_result is not None:
        df_1h_copy = df_1h_copy.join(adx_result)
    
    # 15m indicators
    df_15m_copy['EMA200'] = ta.ema(df_15m_copy['close'], length=200)
    df_15m_copy['RSI'] = ta.rsi(df_15m_copy['close'], length=14)
    df_15m_copy['ATR'] = ta.atr(df_15m_copy['high'], df_15m_copy['low'], df_15m_copy['close'], length=14)
    
    stoch = ta.stochrsi(df_15m_copy['close'], length=14, rsi_length=14, k=3, d=3)
    if stoch is not None:
        df_15m_copy = df_15m_copy.join(stoch)
    
    k_col = [c for c in df_15m_copy.columns if c.startswith('STOCHRSIk')][0]
    d_col = [c for c in df_15m_copy.columns if c.startswith('STOCHRSId')][0]
    
    balance = settings.PAPER_TRADING_BALANCE
    position = None
    trades = []
    
    # Backtest loop
    for i in range(200, len(df_15m_copy)):
        current_time = df_15m_copy.index[i]
        row_15m = df_15m_copy.iloc[i]
        prev_15m = df_15m_copy.iloc[i-1]
        
        # Get 1H context
        last_hour_ts = current_time.floor('1h') - pd.Timedelta(hours=1)
        if last_hour_ts not in df_1h_copy.index:
            continue
        row_1h = df_1h_copy.loc[last_hour_ts]
        
        # Check exits
        if position:
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
            else:
                if row_15m['high'] >= position['sl']:
                    pnl = (position['entry'] - position['sl']) * position['size']
                    closed = True; reason = "SL"
                elif row_15m['low'] <= position['tp']:
                    pnl = (position['entry'] - position['tp']) * position['size']
                    closed = True; reason = "TP"
            
            if closed:
                # Fees
                fee = (position['entry'] * position['size'] * 2) * 0.0004
                pnl -= fee
                balance += pnl
                trades.append({'time': current_time, 'pnl': pnl, 'reason': reason, 'side': position['side']})
                position = None
                continue
        
        # Check entries
        if not position:
            # Trend filter
            adx_val = row_1h.get('ADX_14', 0)
            trend_bullish = (row_1h['EMA50'] > row_1h['EMA200']) and (adx_val > params['adx_threshold'])
            trend_bearish = (row_1h['EMA50'] < row_1h['EMA200']) and (adx_val > params['adx_threshold'])
            
            atr_val = row_15m.get('ATR', 0)
            if pd.isna(atr_val) or atr_val == 0:
                continue
            
            signal = None
            
            # LONG
            stoch_k = row_15m[k_col]
            stoch_d = row_15m[d_col]
            prev_k = prev_15m[k_col]
            prev_d = prev_15m[d_col]
            
            stoch_cross_up = (stoch_k > stoch_d) and (prev_k <= prev_d)
            stoch_in_oversold = stoch_k < params['stoch_oversold']
            rsi_valid_long = row_15m['RSI'] < params['rsi_long_max']
            price_above_ema = row_15m['close'] > row_15m['EMA200']
            
            if trend_bullish and price_above_ema and rsi_valid_long and stoch_cross_up and stoch_in_oversold:
                sl_dist = atr_val * params['sl_atr_multiplier']
                entry = row_15m['close']
                sl = entry - sl_dist
                risk = entry - sl
                tp = entry + (risk * params['risk_reward_ratio'])
                signal = {'side': 'LONG', 'entry': entry, 'sl': sl, 'tp': tp}
            
            # SHORT
            stoch_cross_down = (stoch_k < stoch_d) and (prev_k >= prev_d)
            stoch_in_overbought = stoch_k > params['stoch_overbought']
            rsi_valid_short = row_15m['RSI'] > params['rsi_short_min']
            price_below_ema = row_15m['close'] < row_15m['EMA200']
            
            if trend_bearish and price_below_ema and rsi_valid_short and stoch_cross_down and stoch_in_overbought:
                sl_dist = atr_val * params['sl_atr_multiplier']
                entry = row_15m['close']
                sl = entry + sl_dist
                risk = sl - entry
                tp = entry - (risk * params['risk_reward_ratio'])
                signal = {'side': 'SHORT', 'entry': entry, 'sl': sl, 'tp': tp}
            
            if signal:
                risk_amt = balance * 0.01
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
    
    # Calculate metrics
    if not trades:
        return None
    
    df_trades = pd.DataFrame(trades)
    wins = df_trades[df_trades['pnl'] > 0]
    losses = df_trades[df_trades['pnl'] <= 0]
    
    total_pnl = df_trades['pnl'].sum()
    win_rate = len(wins) / len(trades) if len(trades) > 0 else 0
    
    avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
    avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 1
    profit_factor = (wins['pnl'].sum() / abs(losses['pnl'].sum())) if len(losses) > 0 and losses['pnl'].sum() != 0 else 0
    
    # Calculate max drawdown
    equity_curve = df_trades['pnl'].cumsum() + settings.PAPER_TRADING_BALANCE
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    # Expectancy
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    return {
        'params': params,
        'total_trades': len(trades),
        'win_rate': win_rate * 100,
        'total_pnl': total_pnl,
        'final_balance': balance,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'expectancy': expectancy,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
    }

def main():
    # Fetch data
    print("Fetching historical data...")
    exchange = ccxt.binance({'enableRateLimit': True})
    symbol = settings.SYMBOL
    
    # Fetch 60 days of 15m data
    start_time = exchange.parse8601((pd.Timestamp.now() - pd.Timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    ohlcv = []
    since = start_time
    while True:
        data = exchange.fetch_ohlcv(symbol, '15m', since, limit=1000)
        if not data:
            break
        ohlcv.extend(data)
        since = data[-1][0] + (15 * 60 * 1000)
        if len(data) < 1000:
            break
    
    df_15m = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_15m['timestamp'] = pd.to_datetime(df_15m['timestamp'], unit='ms')
    df_15m.set_index('timestamp', inplace=True)
    
    df_1h = df_15m.resample('1h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    print(f"✅ Data loaded: {len(df_15m)} 15m candles, {len(df_1h)} 1h candles\n")
    
    # Generate parameter combinations
    keys = list(PARAM_GRID.keys())
    values = [PARAM_GRID[k] for k in keys]
    combinations = list(product(*values))
    
    print(f"🔍 Testing {len(combinations):,} combinations...\n")
    
    results = []
    for i, combo in enumerate(combinations):
        params = dict(zip(keys, combo))
        
        # Progress
        if (i + 1) % 100 == 0 or i == 0:
            print(f"Progress: {i+1}/{len(combinations)} ({(i+1)/len(combinations)*100:.1f}%)")
        
        result = run_single_backtest(params, df_15m, df_1h)
        if result and result['total_trades'] >= 10:  # Minimum 10 trades
            results.append(result)
    
    print(f"\n✅ Optimization complete! Found {len(results)} valid configurations.\n")
    
    # Sort by different metrics
    df_results = pd.DataFrame(results)
    
    # Save all results
    df_results.to_csv('optimization_results.csv', index=False)
    print("💾 Full results saved to: optimization_results.csv\n")
    
    print("=" * 80)
    print("TOP 5 BY WIN RATE")
    print("=" * 80)
    top_wr = df_results.nlargest(5, 'win_rate')
    for idx, row in top_wr.iterrows():
        print(f"\nWin Rate: {row['win_rate']:.1f}% | Trades: {row['total_trades']} | PnL: ${row['total_pnl']:.0f}")
        print(f"  Params: {row['params']}")
    
    print("\n" + "=" * 80)
    print("TOP 5 BY TOTAL PNL")
    print("=" * 80)
    top_pnl = df_results.nlargest(5, 'total_pnl')
    for idx, row in top_pnl.iterrows():
        print(f"\nPnL: ${row['total_pnl']:.0f} | Win Rate: {row['win_rate']:.1f}% | Trades: {row['total_trades']}")
        print(f"  Params: {row['params']}")
    
    print("\n" + "=" * 80)
    print("TOP 5 BY PROFIT FACTOR")
    print("=" * 80)
    top_pf = df_results.nlargest(5, 'profit_factor')
    for idx, row in top_pf.iterrows():
        print(f"\nProfit Factor: {row['profit_factor']:.2f} | Win Rate: {row['win_rate']:.1f}% | PnL: ${row['total_pnl']:.0f}")
        print(f"  Params: {row['params']}")
    
    print("\n" + "=" * 80)
    print("TOP 5 BY EXPECTANCY (Best Risk-Adjusted)")
    print("=" * 80)
    top_exp = df_results.nlargest(5, 'expectancy')
    for idx, row in top_exp.iterrows():
        print(f"\nExpectancy: ${row['expectancy']:.2f} | Win Rate: {row['win_rate']:.1f}% | PnL: ${row['total_pnl']:.0f}")
        print(f"  Params: {row['params']}")
    
    # BEST OVERALL (composite score)
    df_results['composite_score'] = (
        df_results['win_rate'] / 100 * 0.3 +  # 30% weight on win rate
        (df_results['total_pnl'] / df_results['total_pnl'].max()) * 0.3 +  # 30% on PnL
        (df_results['profit_factor'] / df_results['profit_factor'].max()) * 0.2 +  # 20% on PF
        (1 - abs(df_results['max_drawdown']) / 100) * 0.2  # 20% on low drawdown
    )
    
    print("\n" + "=" * 80)
    print("🏆 TOP 3 OVERALL (Composite Score)")
    print("=" * 80)
    top_overall = df_results.nlargest(3, 'composite_score')
    for rank, (idx, row) in enumerate(top_overall.iterrows(), 1):
        print(f"\n#{rank}")
        print(f"  Win Rate: {row['win_rate']:.1f}%")
        print(f"  Total PnL: ${row['total_pnl']:.0f}")
        print(f"  Profit Factor: {row['profit_factor']:.2f}")
        print(f"  Max Drawdown: {row['max_drawdown']:.1f}%")
        print(f"  Trades: {row['total_trades']}")
        print(f"  Expectancy: ${row['expectancy']:.2f}")
        print(f"\n  📋 PARAMETERS:")
        for k, v in row['params'].items():
            print(f"    {k}: {v}")
    
    # Save best config
    best = top_overall.iloc[0]
    with open('best_params.json', 'w') as f:
        json.dump({
            'params': best['params'],
            'performance': {
                'win_rate': best['win_rate'],
                'total_pnl': best['total_pnl'],
                'profit_factor': best['profit_factor'],
                'total_trades': best['total_trades'],
                'max_drawdown': best['max_drawdown'],
                'expectancy': best['expectancy'],
            }
        }, f, indent=2)
    
    print("\n" + "=" * 80)
    print("💾 Best parameters saved to: best_params.json")
    print("=" * 80)
    
    print("\n⚠️  IMPORTANT WARNINGS:")
    print("   1. These are IN-SAMPLE results (overfitting risk)")
    print("   2. Past performance ≠ future results")
    print("   3. Always validate with forward testing on new data")
    print("   4. Consider using walk-forward optimization")
    print("   5. Monitor live performance and adjust if needed")

if __name__ == "__main__":
    main()
