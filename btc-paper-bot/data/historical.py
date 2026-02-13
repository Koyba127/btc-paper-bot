import ccxt
import pandas as pd
from config import settings
from utils.logger import logger
import structlog
import asyncio

log = structlog.get_logger()

class HistoricalFetcher:
    def __init__(self, exchange_id='binance', symbol='BTC/USDT'):
        self.exchange_id = exchange_id
        self.symbol = symbol
        # CCXT standard (blocking). We'll run it in executor or use async ccxt if preferred for consistency.
        # But this is "initial load", blocking is fine or use async. Since everything is async, let's use async ccxt.
        self.exchange = getattr(ccxt.pro, exchange_id)({'enableRateLimit': True})

    async def fetch_ohlcv(self, timeframe='1h', limit=1000) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        try:
            log.info("Fetching historical data", symbol=self.symbol, timeframe=timeframe, limit=limit)
            ohlcv = await self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            log.error("Error fetching historical data", error=str(e))
            return pd.DataFrame()

    async def close(self):
        await self.exchange.close()
