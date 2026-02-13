import ccxt.pro as ccxt
import asyncio
from config import settings
from utils.logger import logger
import structlog

log = structlog.get_logger()

class WebSocketFetcher:
    def __init__(self, exchange_id='binance', symbol='BTC/USDT'):
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.exchange = getattr(ccxt, exchange_id)({'enableRateLimit': True})
        self.keep_running = True

    async def stream_ohlcv(self, timeframe='1m', queue: asyncio.Queue = None):
        """Streams OHLCV data to a queue."""
        log.info("Starting OHLCV stream", symbol=self.symbol, timeframe=timeframe)
        backoff = 1
        while self.keep_running:
            try:
                # watch_ohlcv yields a list of candles. We usually want the latest closed one or the current building one.
                # The strategy needs closed candles.
                candles = await self.exchange.watch_ohlcv(self.symbol, timeframe)
                if queue:
                    await queue.put({'type': 'ohlcv', 'data': candles, 'timeframe': timeframe})
                backoff = 1
            except Exception as e:
                log.error("Error in OHLCV stream", error=str(e))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def stream_ticker(self, queue: asyncio.Queue = None):
        """Streams ticker data for SL/TP monitoring."""
        log.info("Starting Ticker stream", symbol=self.symbol)
        backoff = 1
        while self.keep_running:
            try:
                ticker = await self.exchange.watch_ticker(self.symbol)
                if queue:
                    await queue.put({'type': 'ticker', 'data': ticker})
                backoff = 1
            except Exception as e:
                log.error("Error in Ticker stream", error=str(e))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def close(self):
        self.keep_running = False
        await self.exchange.close()
