# BTC Paper Trading Bot - Optimization Guide

## 🎯 Current Strategy Performance (Last 60 Days)
- **Total Trades**: 50 (~0.8 trades/day)
- **Win Rate**: 46%
- **Total PnL**: +1,300 USDT (+13% in 2 months)
- **Risk/Reward Ratio**: 2.0

---

## 🔧 How to Optimize the Strategy

### 1. **Key Tunable Parameters** (in `strategies/day_trading.py`)

```python
class DayTradingStrategy:
    def __init__(self):
        # --- TUNABLE PARAMETERS ---
        
        # Risk Management
        self.atr_period = 14               # ATR lookback period (7-21)
        self.sl_atr_multiplier = 2.0       # Stop Loss distance (1.5-3.0)
        self.risk_reward_ratio = 2.0       # Target profit multiple (1.5-3.0)
        
        # Trend Filter
        self.adx_threshold = 20            # Minimum ADX (15-30)
        
        # Entry Precision
        self.stoch_oversold = 20           # Max StochRSI for LONG (10-30)
        self.stoch_overbought = 80         # Min StochRSI for SHORT (70-90)
        
        # RSI Filters
        self.rsi_long_max = 60             # Max RSI for LONG (50-70)
        self.rsi_short_min = 40            # Min RSI for SHORT (30-50)
```

---

### 2. **Optimization Workflow**

#### **Step 1: Modify Parameters**
Edit `strategies/day_trading.py` and change the values in `__init__()`.

#### **Step 2: Run Backtest**
```bash
python backtesting/backtest.py
```

#### **Step 3: Analyze Results**
The backtest outputs:
- **Total Trades**: Higher frequency = more opportunities, but lower win rate
- **Win Rate**: Target 40-50% with 2.0 R:R for profitability
- **Total PnL**: Cumulative profit
- **Last Signal Date**: Check if strategy is still active in current market

#### **Step 4: Find the Balance**
- **More Trades** → Relax filters (lower ADX, wider Stoch zones)
- **Higher Win Rate** → Tighten filters (higher ADX, narrower Stoch zones)
- **Better Risk/Reward** → Increase `risk_reward_ratio` or `sl_atr_multiplier`

---

### 3. **Optimization Examples**

#### **Example 1: Increase Trade Frequency**
**Goal**: Get 2-3 trades per day instead of 0.8

```python
# Change in strategies/day_trading.py
self.adx_threshold = 15        # Was 20
self self.stoch_oversold = 30      # Was 20
self.stoch_overbought = 70     # Was 80
```
**Expected**: 100+ trades in 60 days, but win rate may drop to 35-40%

---

#### **Example 2: Maximize Win Rate**
**Goal**: Get 60%+ win rate with fewer trades

```python
self.adx_threshold = 25        # Was 20
self.stoch_oversold = 10       # Was 20
self.stoch_overbought = 90     # Was 80
self.risk_reward_ratio = 1.5   # Was 2.0 (easier to hit TP)
```
**Expected**: 20-30 trades in 60 days, 55-65% win rate

---

#### **Example 3: Aggressive Scalping**
**Goal**: Maximum trades with acceptable risk

```python
self.sl_atr_multiplier = 1.5   # Tighter stops
self.risk_reward_ratio = 1.5   # Easier targets
self.adx_threshold = 15         # Allow ranging markets
self.rsi_long_max = 70          # Less restrictive
self.rsi_short_min = 30
```
**Expected**: 150+ trades, 38-42% win rate, high churn

---

### 4. **Advanced: Market Condition Detection**

Add time-based filters to avoid bad market hours:

```python
# In strategies/day_trading.py, in analyze():
current_hour = current.name.hour

# Avoid low liquidity hours (example: 00:00-04:00 UTC)
if 0 <= current_hour < 4:
    return None
```

---

### 5. **Data-Driven Optimization (Walk-Forward)**

1. **Backtest Jan-Feb 2026** → Find best params
2. **Forward Test March 2026** (historical data) → Validate
3. **If consistent** → Deploy live
4. **Monitor 1 week** → Adjust

---

### 6. **Quick Optimization Commands**

```bash
# Test current strategy
python backtesting/backtest.py

# After changing parameters in strategies/day_trading.py
python backtesting/backtest.py

# Compare results:
# - If PnL improved AND trade count acceptable → keep changes
# - If win rate dropped below 35% → too aggressive
# - If no trades in last 7 days → too conservative
```

---

### 7. **Parameter Impact Cheat Sheet**

| Parameter | ↑ Increase Effect | ↓ Decrease Effect |
|-----------|-------------------|-------------------|
| `adx_threshold` | Fewer trades, stronger trends | More trades, includes chop |
| `stoch_oversold` | More LONG entries | Stricter LONG entries |
| `stoch_overbought` | More SHORT entries | Stricter SHORT entries |
| `sl_atr_multiplier` | Wider stops, fewer SL hits | Tighter stops, more SL hits |
| `risk_reward_ratio` | Harder to hit TP, need bigger moves | Easier to hit TP, less profit |
| `rsi_long_max` | More LONG entries | Fewer LONG entries |
| `rsi_short_min` | More SHORT entries | Fewer SHORT entries |

---

### 8. **Red Flags to Watch**

❌ **Win Rate < 30%** with R:R = 2.0 → Strategy is broken
❌ **0 trades in 7+ days** → Market conditions changed or filters too strict
❌ **Consecutive 10+ losses** → Stop live trading, review parameters
✅ **40-50% WR with R:R 2.0** → Profitable long-term
✅ **Consistent weekly signals** → Strategy is active

---

## 🚀 Current Setup is Optimized For:
- **Day Trading** (15m timeframe)
- **Trending Markets** (ADX > 20)
- **Precision Entries** (StochRSI extremes)
- **2:1 Risk/Reward** (Sustainable profitability)

**To change focus**: Adjust the parameters in `strategies/day_trading.py` and backtest!
