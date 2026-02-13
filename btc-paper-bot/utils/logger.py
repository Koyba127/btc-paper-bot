import logging
import logging.handlers
import structlog
import sys
import os
from config import settings

LOG_DIR = "logs"
LOG_FILE = "btc_paper_bot.log"
os.makedirs(LOG_DIR, exist_ok=True)

# Standard library logger configuration
file_handler = logging.handlers.TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, LOG_FILE),
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

# Also console output but only for ERROR by default to avoid spam
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

logging.basicConfig(
    format="%(message)s",
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    handlers=[file_handler, console_handler]
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
