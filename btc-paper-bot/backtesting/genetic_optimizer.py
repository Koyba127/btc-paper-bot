"""
FAST Genetic Algorithm Optimizer for Day Trading Strategy
Tests WAY more combinations by using evolution instead of brute force.
~20x faster than grid search!
"""
import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime
import random
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

print("=" * 80)
print("GENETIC ALGORITHM OPTIMIZER - FAST & SMART")
print("=" * 80)

# --- GENETIC ALGORITHM SETTINGS ---
POPULATION_SIZE = 50  # Number of parameter sets per generation
GENERATIONS = 40       # Number of evolution cycles
MUTATION_RATE = 0.15   # Chance of random mutation
ELITE_SIZE = 5         # Top performers to keep unchanged

# --- PARAMETER RANGES ---
PARAM_RANGES = {
    'adx_threshold': (12, 30),
    'stoch_oversold': (10, 35),
    'stoch_overbought': (65, 90),
    'risk_reward_ratio': (1.3, 3.5),
    'sl_atr_multiplier': (1.3, 3.0),
    'rsi_long_max': (55, 75),
    'rsi_short_min': (25, 45),
}

print(f"\n🧬 Population: {POPULATION_SIZE} | Generations: {GENERATIONS}")
print(f"⏱️  Expected tests: {POPULATION_SIZE * GENERATIONS} (~{POPULATION_SIZE * GENERATIONS * 0.15 / 60:.0f} min)\n")

def create_random_params():
    """Generate random parameters within ranges."""
    return {
        'adx_threshold': random.randint(*PARAM_RANGES['adx_threshold']),
        'stoch_oversold': random.randint(*PARAM_RANGES['stoch_oversold']),
        'stoch_overbought': random.randint(*PARAM_RANGES['stoch_overbought']),
        'risk_reward_ratio': round(random.uniform(*PARAM_RANGES['risk_reward_ratio']), 2),
        'sl_atr_multiplier': round(random.uniform(*PARAM_RANGES['sl_atr_multiplier']), 2),
        'rsi_long_max': random.randint(*PARAM_RANGES['rsi_long_max']),
        'rsi_short_min': random.randint(*PARAM_RANGES['rsi_short_min']),
    }

def mutate_params(params):
    """Randomly mutate parameters."""
    mutated = params.copy()
    for key in mutated:
        if random.random() < MUTATION_RATE:
            if isinstance(mutated[key], int):
                mutated[key] = random.randint(*PARAM_RANGES[key])
            else:
                mutated[key] = round(random.uniform(*PARAM_RANGES[key]), 2)
    return mutated

def crossover_params(parent1, parent2):
    """Combine two parameter sets."""
    child = {}
    for key in parent1:
        child[key] = parent1[key] if random.random() < 0.5 else parent2[key]
    return child

def evaluate_params(params, df_15m, df_1h):
    """Fast backtest with given parameters."""
    # Pre-calculate indicators (VECTORIZED - fast!)
    df_1h_copy = df_1h.copy()
    df_15m_copy = df_15m.copy()
    
    df_1h_copy['EMA50'] = ta.ema(df_1h_copy['close'], length=50)
    df_1h_copy['EMA200'] = ta.ema(df_1h_copy['close'], length=200)
    adx_res = ta.adx(df_1h_copy['high'], df_1h_copy['low'], df_1h_copy['close'], length=14)
    if adx_res is not None:
        df_1h_copy = df_1h_copy.join(adx_res)
    
    df_15m_copy['EMA200'] = ta.ema(df_15m_copy['close'], length=200)
    df_15m_copy['RSI'] = ta.rsi(df_15m_copy['close'], length=14)
    df_15m_copy['ATR'] = ta.atr(df_15m_copy['high'], df_15m_copy['low'], df_15m_copy['close'], length=14)
    
    stoch = ta.stochrsi(df_15m_copy['close'], length=14, rsi_length=14, k=3, d=3)
    if stoch is None or stoch.empty:
        return 0  # Failed indicator calculation
    df_15m_copy = df_15m_copy.join(stoch)
    
    k_col = [c for c in df_15m_copy.columns if c.startswith('STOCHRSIk')][0]
    d_col = [c for c in df_15m_copy.columns if c.startswith('STOCHRSId')][0]
    
    balance = settings.PAPER_TRADING_BALANCE
    position = None
    trades = []
    
    # Simulate trading
    for i in range(200, len(df_15m_copy)):
        current_time = df_15m_copy.index[i]
        row = df_15m_copy.iloc[i]
        prev = df_15m_copy.iloc[i-1]
        
        last_hour = current_time.floor('1h') - pd.Timedelta(hours=1)
        if last_hour not in df_1h_copy.index:
            continue
        h_row = df_1h_copy.loc[last_hour]
        
        # Exit check
        if position:
            pnl = 0
            closed = False
            if position['side'] == 'LONG':
                if row['low'] <= position['sl']:
                    pnl = (position['sl'] - position['entry']) * position['size'] - (position['entry'] * position['size'] * 2 * 0.0004)
                    closed = True
                elif row['high'] >= position['tp']:
                    pnl = (position['tp'] - position['entry']) * position['size'] - (position['entry'] * position['size'] * 2 * 0.0004)
                    closed = True
            else:
                if row['high'] >= position['sl']:
                    pnl = (position['entry'] - position['sl']) * position['size'] - (position['entry'] * position['size'] * 2 * 0.0004)
                    closed = True
                elif row['low'] <= position['tp']:
                    pnl = (position['entry'] - position['tp']) * position['size'] - (position['entry'] * position['size'] * 2 * 0.0004)
                    closed = True
            
            if closed:
                balance += pnl
                trades.append(pnl)
                position = None
                continue
        
        # Entry check
        if not position:
            adx = h_row.get('ADX_14', 0)
            trend_bull = (h_row['EMA50'] > h_row['EMA200']) and (adx > params['adx_threshold'])
            trend_bear = (h_row['EMA50'] < h_row['EMA200']) and (adx > params['adx_threshold'])
            
            atr = row.get('ATR', 0)
            if pd.isna(atr) or atr == 0:
                continue
            
            signal = None
            
            # LONG
            k = row[k_col]
            d = row[d_col]
            pk = prev[k_col]
            pd_val = prev[d_col]
            
            if (trend_bull and row['close'] > row['EMA200'] and row['RSI'] < params['rsi_long_max'] 
                and k > d and pk <= pd_val and k < params['stoch_oversold']):
                entry = row['close']
                sl = entry - (atr * params['sl_atr_multiplier'])
                risk = entry - sl
                tp = entry + (risk * params['risk_reward_ratio'])
                signal = {'side': 'LONG', 'entry': entry, 'sl': sl, 'tp': tp}
            
            # SHORT
            if (trend_bear and row['close'] < row['EMA200'] and row['RSI'] > params['rsi_short_min']
                and k < d and pk >= pd_val and k > params['stoch_overbought']):
                entry = row['close']
                sl = entry + (atr * params['sl_atr_multiplier'])
                risk = sl - entry
                tp = entry - (risk * params['risk_reward_ratio'])
                signal = {'side': 'SHORT', 'entry': entry, 'sl': sl, 'tp': tp}
            
            if signal:
                risk_amt = balance * 0.01
                dist = abs(signal['entry'] - signal['sl'])
                if dist > 0:
                    size = risk_amt / dist
                    position = signal.copy()
                    position['size'] = size
    
    # Calculate fitness
    if len(trades) < 10:
        return 0  # Not enough trades
    
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    
    win_rate = len(wins) / len(trades)
    total_pnl = sum(trades)
    profit_factor = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 10
    
    # Normalize PnL (-10k to +10k → 0 to 100)
    pnl_score = max(0, min(100, (total_pnl + 10000) / 200))
    
    # Penalize being far from 45% win rate (sweet spot for 2:1 R:R)
    wr_distance_penalty = abs(win_rate - 0.45) * 50  # 0-50 penalty
    
    # Composite fitness (higher is better)
    fitness = (
        win_rate * 100 +                   # 0-100 from win rate
        pnl_score +                        # 0-100 from PnL
        min(100, profit_factor * 20) +     # 0-100 from profit factor
        min(100, len(trades) / 2) +        # 0-100 from trade count (50+ trades = max)
        (100 - wr_distance_penalty)        # 50-100 from win rate distance
    )
    
    return fitness

def main():
    # Fetch data
    print("Fetching historical data...")
    exchange = ccxt.binance({'enableRateLimit': True})
    symbol = settings.SYMBOL
    
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
    
    # Initialize population
    population = [create_random_params() for _ in range(POPULATION_SIZE)]
    best_ever = None
    best_fitness = 0
    
    for gen in range(GENERATIONS):
        # Evaluate fitness
        fitness_scores = []
        for params in population:
            fitness = evaluate_params(params, df_15m, df_1h)
            fitness_scores.append((fitness, params))
        
        # Sort by fitness
        fitness_scores.sort(reverse=True, key=lambda x: x[0])
        
        # Track best
        if fitness_scores[0][0] > best_fitness:
            best_fitness = fitness_scores[0][0]
            best_ever = fitness_scores[0][1]
        
        # Progress
        avg_fitness = sum(f[0] for f in fitness_scores) / len(fitness_scores)
        print(f"Gen {gen+1}/{GENERATIONS} | Best Fitness: {fitness_scores[0][0]:.2f} | Avg: {avg_fitness:.2f}")
        
        # Selection & reproduction
        elite = [p[1] for p in fitness_scores[:ELITE_SIZE]]
        new_population = elite.copy()
        
        while len(new_population) < POPULATION_SIZE:
            # Tournament selection
            parent1 = random.choice(fitness_scores[:20])[1]  # Top 20
            parent2 = random.choice(fitness_scores[:20])[1]
            
            # Crossover
            child = crossover_params(parent1, parent2)
            
            # Mutation
            child = mutate_params(child)
            
            new_population.append(child)
        
        population = new_population
    
    print("\n" + "=" * 80)
    print("🏆 OPTIMIZATION COMPLETE!")
    print("=" * 80)
    print(f"\nBest Fitness Score: {best_fitness:.2f}")
    print("\n📋 BEST PARAMETERS:")
    for k, v in best_ever.items():
        print(f"  {k}: {v}")
    
    # Save
    with open('best_params_genetic.json', 'w') as f:
        json.dump({
            'params': best_ever,
            'fitness_score': float(best_fitness),
            'note': 'Generated by Genetic Algorithm'
        }, f, indent=2)
    
    print("\n💾 Saved to: best_params_genetic.json")
    print("\n⚠️  RUN A FULL BACKTEST TO VERIFY PERFORMANCE!")
    print("   python backtesting/backtest.py\n")

if __name__ == "__main__":
    main()
