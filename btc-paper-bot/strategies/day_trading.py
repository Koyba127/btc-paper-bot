import pandas_ta as ta
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Literal
from structlog import get_logger

log = get_logger()

@dataclass
class Signal:
    action: Literal["LONG", "SHORT", "NONE"]
    price: float
    reason: str
    sl: float
    tp: float
    timestamp: pd.Timestamp

class DayTradingStrategy:
    """
    Day Trading Strategy optimized for BTC/USDT 15m timeframe.
    
    Parameters (Tunable):
    - atr_period: ATR lookback period for volatility measurement
    - sl_atr_multiplier: How many ATRs away to place stop loss
    - risk_reward_ratio: Target profit as multiple of risk
    - adx_threshold: Minimum ADX to confirm trending market (avoid chop)
    - stoch_oversold: Maximum Stochastic RSI K for LONG entry
    - stoch_overbought: Minimum Stochastic RSI K for SHORT entry
    - rsi_long_max: Maximum RSI for LONG (avoid overbought)
    - rsi_short_min: Minimum RSI for SHORT (avoid oversold)
    """
    def __init__(self):
        # --- TUNABLE PARAMETERS ---
        self.atr_period = 14
        self.sl_atr_multiplier = 2.0        # Conservative stops
        self.risk_reward_ratio = 2.0         # 2:1 R:R
        
        # Trend Strength Filter
        self.adx_threshold = 18              # Allow moderate trends
        
        # Stochastic RSI Zones
        self.stoch_oversold = 20             # STRICT oversold zone
        self.stoch_overbought = 80           # STRICT overbought zone
        
        # RSI Filters
        self.rsi_long_max = 60               # Reasonable RSI filter
        self.rsi_short_min = 40              # Reasonable RSI filter

    def analyze(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Optional[Signal]:
        """
        Analyzes 15m and 1h dataframes for Day Trading signals.
        
        Strategy:
        1. 1H Trend Filter: EMA50 > EMA200 (Bull) or < (Bear) + ADX > threshold
        2. 15m Entry: StochRSI Cross in extreme zones + Price vs EMA200 + RSI filter
        3. Risk Management: ATR-based SL, 2.0 R:R
        """
        if df_15m.empty or df_1h.empty:
            return None

        # --- 1H Trend Filter + Chop Filter ---
        df_1h['EMA50'] = ta.ema(df_1h['close'], length=50)
        df_1h['EMA200'] = ta.ema(df_1h['close'], length=200)
        
        # ADX for Trend Strength
        adx_result = ta.adx(df_1h['high'], df_1h['low'], df_1h['close'], length=14)
        if adx_result is None or adx_result.empty:
            return None
        df_1h = df_1h.join(adx_result)
        
        last_1h = df_1h.iloc[-2]  # Last COMPLETED 1H candle
        
        # Trend + Strength
        trend_bullish = (last_1h['EMA50'] > last_1h['EMA200']) and (last_1h['ADX_14'] > self.adx_threshold)
        trend_bearish = (last_1h['EMA50'] < last_1h['EMA200']) and (last_1h['ADX_14'] > self.adx_threshold)

        # --- 15m Execution Indicators ---
        df_15m['EMA200'] = ta.ema(df_15m['close'], length=200)
        df_15m['RSI'] = ta.rsi(df_15m['close'], length=14)
        
        # Stochastic RSI
        stoch = ta.stochrsi(df_15m['close'], length=14, rsi_length=14, k=3, d=3)
        if stoch is None or stoch.empty:
            return None
        df_15m = df_15m.join(stoch)
        
        # Column names
        k_col = [c for c in df_15m.columns if c.startswith('STOCHRSIk')][0]
        d_col = [c for c in df_15m.columns if c.startswith('STOCHRSId')][0]
        
        # ATR for dynamic stops
        atr = ta.atr(df_15m['high'], df_15m['low'], df_15m['close'], length=self.atr_period)
        if atr is None:
            return None
        df_15m = df_15m.join(atr)
        atr_col = 'ATRr_14' if 'ATRr_14' in df_15m.columns else 'ATR_14'

        # Analyze last COMPLETED candle
        current = df_15m.iloc[-2]
        prev = df_15m.iloc[-3]
        
        # --- LONG SETUP ---
        stoch_k = current[k_col]
        stoch_d = current[d_col]
        prev_k = prev[k_col]
        prev_d = prev[d_col]
        
        stoch_cross_up = (stoch_k > stoch_d) and (prev_k <= prev_d)
        stoch_in_oversold = stoch_k < self.stoch_oversold
        
        rsi_valid_long = current['RSI'] < self.rsi_long_max
        price_above_ema = current['close'] > current['EMA200']
        
        if trend_bullish and price_above_ema and rsi_valid_long and stoch_cross_up and stoch_in_oversold:
            entry_price = current['close']
            sl_dist = current[atr_col] * self.sl_atr_multiplier
            sl = entry_price - sl_dist
            risk = entry_price - sl
            tp = entry_price + (risk * self.risk_reward_ratio)
            
            return Signal(
                action="LONG",
                price=entry_price,
                reason=f"1H Bull+ADX>{self.adx_threshold} | 15m>EMA | StochRSI<{self.stoch_oversold} Cross↑ | RSI<{self.rsi_long_max}",
                sl=sl,
                tp=tp,
                timestamp=current.name
            )
            
        # --- SHORT SETUP ---
        stoch_cross_down = (stoch_k < stoch_d) and (prev_k >= prev_d)
        stoch_in_overbought = stoch_k > self.stoch_overbought
        
        rsi_valid_short = current['RSI'] > self.rsi_short_min
        price_below_ema = current['close'] < current['EMA200']
        
        if trend_bearish and price_below_ema and rsi_valid_short and stoch_cross_down and stoch_in_overbought:
            entry_price = current['close']
            sl_dist = current[atr_col] * self.sl_atr_multiplier
            sl = entry_price + sl_dist
            risk = sl - entry_price
            tp = entry_price - (risk * self.risk_reward_ratio)
            
            return Signal(
                action="SHORT",
                price=entry_price,
                reason=f"1H Bear+ADX>{self.adx_threshold} | 15m<EMA | StochRSI>{self.stoch_overbought} Cross↓ | RSI>{self.rsi_short_min}",
                sl=sl,
                tp=tp,
                timestamp=current.name
            )
            
        return None
