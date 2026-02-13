import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
from config import settings
from utils.logger import logger

def calculate_stats(trades_file: str, balance_file: str) -> dict:
    if not os.path.exists(trades_file):
        return {}
    
    with open(trades_file, 'r') as f:
        trades = json.load(f)
    
    if not trades:
        return {}
    
    df = pd.DataFrame(trades)
    closed_trades = df[df['status'] == 'CLOSED']
    
    if closed_trades.empty:
        return {}

    wins = closed_trades[closed_trades['pnl'] > 0]
    losses = closed_trades[closed_trades['pnl'] <= 0]
    
    total_trades = len(closed_trades)
    win_rate = len(wins) / total_trades
    
    avg_win = wins['pnl'].mean() if not wins.empty else 0
    avg_loss = losses['pnl'].mean() if not losses.empty else 0
    
    gross_profit = wins['pnl'].sum()
    gross_loss = abs(losses['pnl'].sum())
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    total_pnl = closed_trades['pnl'].sum()
    initial_balance = settings.PAPER_TRADING_BALANCE
    total_return_pct = (total_pnl / initial_balance) * 100
    
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    
    # Max Drawdown
    # Load balance history for accurate equity curve
    if os.path.exists(balance_file):
        try:
            bal_df = pd.read_csv(balance_file)
            bal_df['timestamp'] = pd.to_datetime(bal_df['date'] if 'date' in bal_df.columns else bal_df.iloc[:,0]) # flexible column
            # Ensure proper equity curve check
            # For each trade, we can also reconstruct equity curve
        except:
            bal_df = pd.DataFrame()
    
    # If using balance history
    equity_curve = [initial_balance]
    running_balance = initial_balance
    for pnl in closed_trades['pnl']:
        running_balance += pnl
        equity_curve.append(running_balance)
    
    equity_series = pd.Series(equity_curve)
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_dd = drawdown.min() * 100 # percentage
    
    # Sharpe Ratio (Simplified annualization)
    returns = pd.Series(equity_curve).pct_change().dropna()
    if returns.std() != 0:
        sharpe = (returns.mean() / returns.std()) * (252 ** 0.5) # daily based assumption or trade based?
        # if intraday, maybe trade based sqrt(trades)
        sharpe_trade = (returns.mean() / returns.std()) * (total_trades ** 0.5) 
    else:
        sharpe = 0

    return {
        "win_rate": win_rate,     
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_dd,
        "sharpe_ratio": sharpe,
        "expectancy": expectancy,
        "total_return_pct": total_return_pct,
        "total_trades": total_trades,
        "avg_win": avg_win, 
        "avg_loss": avg_loss,
        "current_balance": running_balance
    }

def generate_equity_curve(balance_file: str, output_path: str = "equity_curve.png"):
    if not os.path.exists(balance_file):
        return None
    
    try:
        df = pd.read_csv(balance_file, names=['timestamp', 'balance'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.sort_values('timestamp', inplace=True)
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['timestamp'], df['balance'], label='Equity')
        plt.title('Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Balance (USDT)')
        plt.grid(True)
        plt.legend()
        plt.savefig(output_path)
        plt.close()
        return output_path
    except Exception as e:
        logger.error("Error generating equity curve", error=str(e))
        return None
