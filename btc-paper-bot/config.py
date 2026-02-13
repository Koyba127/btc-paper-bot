from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional

class Settings(BaseSettings):
    # Trading
    PAPER_TRADING_BALANCE: float = Field(10000.0, description="Initial balance for paper trading")
    RISK_PERCENT: float = Field(0.75, description="Max risk percentage per trade")
    SYMBOL: str = Field("BTC/USDT", description="Symbol to trade")
    TIMEFRAME_CHECK: str = "1m"
    SLIPPAGE_PCT: float = 0.00
    TAKER_FEE: float = 0.0004
    
    # Notifications
    RESEND_API_KEY: Optional[SecretStr] = None
    EMAIL_FROM: str = "onboarding@resend.dev"
    EMAIL_TO: str = "user@example.com"
    
    # SMTP Fallback
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[SecretStr] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Metrics
    METRICS_PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
