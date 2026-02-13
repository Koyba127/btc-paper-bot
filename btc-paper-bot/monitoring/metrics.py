from prometheus_client import Gauge

# Prometheus Metrics
BALANCE = Gauge('btc_paper_balance', 'Current simulated balance in USDT')
POSITION_SIZE = Gauge('btc_paper_position_size', 'Current position size')
LAST_TRADE_PNL = Gauge('btc_paper_last_trade_pnl', 'PnL of the last closed trade')
OPEN_REALIZED_PNL = Gauge('btc_paper_open_pnl', 'Unrealized PnL of open position') # requires tick update
