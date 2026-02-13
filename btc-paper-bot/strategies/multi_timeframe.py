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

class MultiTimeframeStrategy:
    def __init__(self):
        self.atr_period = 14
        self.atr_multiplier = 1.5
        self.risk_reward_min = 2.8

    def analyze(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Optional[Signal]:
        """
        Analyzes 1h and 4h dataframes for signals.
        df_1h and df_4h must have 'open', 'high', 'low', 'close', 'volume' columns and datetime index.
        """
        if df_1h.empty or df_4h.empty:
            return None

        # --- 4h Trend Analysis ---
        # EMA50 > EMA200
        df_4h['EMA50'] = ta.ema(df_4h['close'], length=50)
        df_4h['EMA200'] = ta.ema(df_4h['close'], length=200)
        
        # ADX > 22
        adx_4h = ta.adx(df_4h['high'], df_4h['low'], df_4h['close'], length=14)
        if adx_4h is None or adx_4h.empty:
            return None
        df_4h = df_4h.join(adx_4h) # Adds ADX_14, DMP_14, DMN_14

        latest_4h = df_4h.iloc[-1]
        
        trend_long = (latest_4h['EMA50'] > latest_4h['EMA200']) and (latest_4h['ADX_14'] > 22)
        trend_short = (latest_4h['EMA50'] < latest_4h['EMA200']) and (latest_4h['ADX_14'] > 22) # Downtrend assumption? 
        # Strategy text: "SHORT: Alle umgekehrt" implies EMA50 < EMA200. ADX represents trend strength, so ADX > 22 is required for BOTH.
        
        # --- 1h Momentum Analysis ---
        # RSI(14)
        df_1h['RSI'] = ta.rsi(df_1h['close'], length=14)
        
        # MACD
        macd = ta.macd(df_1h['close'])
        if macd is None or macd.empty:
            return None
        df_1h = df_1h.join(macd) # MACD_12_26_9, MACDh_12_26_9 (Hist), MACDs_12_26_9 (Signal)
        
        # Volume MA(20)
        df_1h['VolMA20'] = ta.sma(df_1h['volume'], length=20)
        
        current_1h = df_1h.iloc[-1]
        prev_1h = df_1h.iloc[-2]
        
        # Conditions
        # Volume Check
        vol_ok = current_1h['volume'] > current_1h['VolMA20']
        if not vol_ok:
            return None

        # Long Setup
        # RSI 30-40
        rsi_long = (30 <= current_1h['RSI'] <= 40)
        # MACD Bullish Cross: Hist > 0 and Prev Hist <= 0  (OR just strict crossing event logic)
        macd_cross_long = (current_1h['MACDh_12_26_9'] > 0) and (prev_1h['MACDh_12_26_9'] <= 0)
        
        # Short Setup
        # RSI 60-70
        rsi_short = (60 <= current_1h['RSI'] <= 70)
        # MACD Bearish Cross
        macd_cross_short = (current_1h['MACDh_12_26_9'] < 0) and (prev_1h['MACDh_12_26_9'] >= 0)

        # ATR for SL/TP
        atr = ta.atr(df_1h['high'], df_1h['low'], df_1h['close'], length=self.atr_period)
        current_atr = atr.iloc[-1]

        signal = None
        action = "NONE"
        reason = ""

        if trend_long and rsi_long and macd_cross_long:
            action = "LONG"
            reason = "Trend(4h): EMA50>EMA200 & ADX>22 | Mom(1h): RSI 30-40 & MACD Bull Cross | Vol OK"
            entry_price = current_1h['close']
            sl = entry_price - (current_atr * self.atr_multiplier)
            risk = entry_price - sl
            tp_dist = risk * self.risk_reward_min
            tp = entry_price + tp_dist
            
        elif trend_short and rsi_short and macd_cross_short:
            action = "SHORT"
            reason = "Trend(4h): EMA50<EMA200 & ADX>22 | Mom(1h): RSI 60-70 & MACD Bear Cross | Vol OK"
            entry_price = current_1h['close']
            sl = entry_price + (current_atr * self.atr_multiplier)
            risk = sl - entry_price
            tp_dist = risk * self.risk_reward_min
            tp = entry_price - tp_dist
        
        if action != "NONE":
            return Signal(
                action=action,
                price=entry_price,
                reason=reason,
                sl=sl,
                tp=tp,
                timestamp=current_1h.name
            )
        
        return None
