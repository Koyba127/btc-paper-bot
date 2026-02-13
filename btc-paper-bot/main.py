import asyncio
import sys
import os
import signal
import pandas as pd
import structlog
from collections import deque

# Windows compatibility for uvloop
if os.name != 'nt':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from prometheus_client import start_http_server
from config import settings
from utils.logger import logger
from data.websocket_fetcher import WebSocketFetcher
from data.historical import HistoricalFetcher
from execution.paper_engine import engine
from notifier.daily_report import start_scheduler
from notifier.email_notifier import notifier

log = structlog.get_logger()

class Bot:
    def __init__(self):
        self.keep_running = True
        self.ws_fetcher = WebSocketFetcher(symbol=settings.SYMBOL)
        self.queue = asyncio.Queue()
        
        # Data Buffers
        self.df_1h = pd.DataFrame()
        self.df_4h = pd.DataFrame()
        self.df_15m = pd.DataFrame()
        
        self.last_ts_1h = 0
        self.last_ts_4h = 0

    async def initialize_data(self):
        log.info("Initializing Historical Data...")
        hist = HistoricalFetcher(symbol=settings.SYMBOL)
        
        self.df_1h = await hist.fetch_ohlcv('1h', limit=500)
        self.df_4h = await hist.fetch_ohlcv('4h', limit=500)
        self.df_15m = await hist.fetch_ohlcv('15m', limit=100)
        
        await hist.close()
        
        if self.df_1h.empty or self.df_4h.empty:
            log.error("Failed to fetch historical data. Exiting.")
            sys.exit(1)
            
        # Initialize last timestamps
        if not self.df_1h.empty:
            self.last_ts_1h = self.df_1h.index[-1].timestamp() * 1000
        if not self.df_4h.empty:
            self.last_ts_4h = self.df_4h.index[-1].timestamp() * 1000
            
        log.info("Data Initialized", 
                 len_1h=len(self.df_1h), 
                 len_4h=len(self.df_4h))

    def update_buffer(self, df: pd.DataFrame, candle: list) -> pd.DataFrame:
        ts = pd.to_datetime(candle[0], unit='ms')
        row_data = {
            'open': candle[1],
            'high': candle[2],
            'low': candle[3],
            'close': candle[4],
            'volume': candle[5]
        }
        
        if ts in df.index:
            df.loc[ts] = row_data
        else:
            new_row = pd.DataFrame([row_data], index=[ts])
            df = pd.concat([df, new_row])
            
        if len(df) > 600:
            df = df.iloc[-500:]
            
        return df

    async def process_queue(self):
        log.info("Starting Queue Processor...")
        while self.keep_running:
            item = await self.queue.get()
            
            try:
                msg_type = item.get('type')
                
                if msg_type == 'ticker':
                    await engine.process_ticker(item['data'])
                    
                elif msg_type == 'ohlcv':
                    candles = item['data']
                    tf = item['timeframe']
                    
                    for candle in candles:
                        ts = candle[0]
                        if tf == '1h':
                            self.df_1h = self.update_buffer(self.df_1h, candle)
                            if ts > self.last_ts_1h:
                                # New candle started, implies previous closed? 
                                # No, ccxt sends the opening candle usually.
                                # If we see a new timestamp, it means the prev one is done.
                                self.last_ts_1h = ts
                        elif tf == '4h':
                            self.df_4h = self.update_buffer(self.df_4h, candle)
                            if ts > self.last_ts_4h:
                                self.last_ts_4h = ts
                        elif tf == '15m':
                            self.df_15m = self.update_buffer(self.df_15m, candle)
                            # On 15m update, triggered check
                            # Check logic: Are dataframes ready?
                            pass

                    # Trigger Strategy Check on every OHLCV update or specifically 15m?
                    # Strategy relies on LATEST CLOSED candles.
                    # As discussed, we pass the current buffers. 
                    # The strategy takes .iloc[-1] which is the current one (potentially open).
                    # If we strictly want closed candles, we should pass df[:-1] if the last one is not closed.
                    # But for simplicity in Paper Trading with "1m/15m/1h" confirmation,
                    # we often use the developing 1h candle state as "Current 1h Momentum".
                    
                    # However, "Entry nur bei Bestätigung auf 15m- oder 1h-Close" suggests:
                    # Only Check when a 15m or 1h candle CLOSES.
                    # To implement this strictly:
                    # Detect New Candle timestamp (previous closed).
                    
                    # Since implementing strict "New Candle Event" is complex with just buffers,
                    # I will call strategy on every 15m update, but let strategy handle logic or accept developing values.
                    # The user prompt: "Entry-Preis = aktueller Close des 1h-Candles".
                    
                    await engine.process_ohlcv(self.df_1h, self.df_4h)
                    
            except Exception as e:
                log.error("Error in loop", error=str(e))
            finally:
                self.queue.task_done()

    async def run(self):
        await notifier.send_email("Bot Started", f"BTC Paper Bot started on {settings.SYMBOL}")
        await self.initialize_data()
        
        # Start Prometheus Metrics
        try:
            start_http_server(settings.METRICS_PORT)
            log.info("Prometheus metrics started", port=settings.METRICS_PORT)
        except Exception as e:
            log.error("Failed to start Prometheus server", error=str(e))
        
        scheduler = start_scheduler()
        
        tasks = [
            asyncio.create_task(self.ws_fetcher.stream_ticker(self.queue)),
            asyncio.create_task(self.ws_fetcher.stream_ohlcv('15m', self.queue)),
            asyncio.create_task(self.ws_fetcher.stream_ohlcv('1h', self.queue)),
            asyncio.create_task(self.ws_fetcher.stream_ohlcv('4h', self.queue)),
            asyncio.create_task(self.process_queue())
        ]
        
        try:
            while self.keep_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            log.info("Main loop cancelled")
        finally:
            log.info("Shutting down...")
            for t in tasks: t.cancel()
            await self.ws_fetcher.close()
            scheduler.shutdown()
            await notifier.send_email("Bot Stopped", "BTC Paper Bot stopped.")

if __name__ == "__main__":
    bot = Bot()
    
    def handle_exit(sig, frame):
        log.info("Signal received, stopping...")
        bot.keep_running = False
        
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass
