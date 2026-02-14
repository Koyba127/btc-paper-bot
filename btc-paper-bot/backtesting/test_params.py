"""
Quick Parameter Testing Script
Run this to test different strategy parameters without editing code
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.backtest import run_backtest
from strategies.day_trading import DayTradingStrategy

# --- MODIFY THESE TO TEST DIFFERENT CONFIGURATIONS ---

CONFIGS = [
    {
        "name": "Current (Conservative)",
        "adx_threshold": 20,
        "stoch_oversold": 20,
        "stoch_overbought": 80,
        "risk_reward_ratio": 2.0,
        "sl_atr_multiplier": 2.0,
    },
    {
        "name": "Aggressive (More Trades)",
        "adx_threshold": 15,
        "stoch_oversold": 30,
        "stoch_overbought": 70,
        "risk_reward_ratio": 1.8,
        "sl_atr_multiplier": 1.8,
    },
    {
        "name": "Ultra Conservative (High WR)",
        "adx_threshold": 25,
        "stoch_oversold": 15,
        "stoch_overbought": 85,
        "risk_reward_ratio": 1.5,
        "sl_atr_multiplier": 2.5,
    },
]

async def test_config(config):
    """Temporarily modify strategy and run backtest."""
    # Save original
    orig_adx = DayTradingStrategy().adx_threshold
    orig_osold = DayTradingStrategy().stoch_oversold
    orig_obought = DayTradingStrategy().stoch_overbought
    orig_rr = DayTradingStrategy().risk_reward_ratio
    orig_sl = DayTradingStrategy().sl_atr_multiplier
    
    # Monkey patch (not ideal but quick for testing)
    DayTradingStrategy.__init__ = lambda self: setattr(self, '__dict__', {
        'atr_period': 14,
        'adx_threshold': config['adx_threshold'],
        'stoch_oversold': config['stoch_oversold'],
        'stoch_overbought': config['stoch_overbought'],
        'risk_reward_ratio': config['risk_reward_ratio'],
        'sl_atr_multiplier': config['sl_atr_multiplier'],
        'rsi_long_max': 60,
        'rsi_short_min': 40,
    })
    
    # Note: This script won't work perfectly due to how backtesting is structured
    # Better approach: Edit strategies/day_trading.py directly and run backtest.py
    
    print(f"\nThis is a TEMPLATE. To test configurations:")
    print(f"1. Edit strategies/day_trading.py __init__ method")
    print(f"2. Change parameters to: {config}")
    print(f"3. Run: python backtesting/backtest.py")

if __name__ == "__main__":
    print("=" * 60)
    print("STRATEGY PARAMETER TESTING GUIDE")
    print("=" * 60)
    
    for i, config in enumerate(CONFIGS, 1):
        print(f"\n{i}. {config['name']}")
        print("-" * 60)
        for key, val in config.items():
            if key != 'name':
                print(f"   {key}: {val}")
        print("\n   To test this:")
        print(f"   1. Open strategies/day_trading.py")
        print(f"   2. Update __init__ with these values")
        print(f"   3. Run: python backtesting/backtest.py")
        print(f"   4. Compare results")
    
    print("\n" + "=" * 60)
    print("QUICK OPTIMIZATION TIPS:")
    print("=" * 60)
    print("• Lower ADX → More trades, lower win rate")
    print("• Wider Stoch zones → More entries")
    print("• Higher R:R → Fewer TPs hit, bigger wins")
    print("• Lower SL multiplier → More SL hits, less risk")
    print("\nAlways backtest before going live!")
