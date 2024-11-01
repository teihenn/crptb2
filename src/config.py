from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ExchangeConfig:
    name: str
    api_key: str
    api_secret: str
    symbol: str
    position_size: float
    leverage: int
    buy_leverage: str
    sell_leverage: str
    margin_type: str  # isolated or cross
    timeframe: str
    max_position: int
    retry_count: int
    retry_interval: int

    def get_ccxt_config(self) -> Dict[str, Any]:
        return {
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "future",
            },
        }


# Bybit設定
BYBIT = ExchangeConfig(
    name="bybit",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    symbol="BTC/USDT",
    position_size=0.001,
    leverage=1,
    buy_leverage=1,
    sell_leverage=1,
    margin_type="isolated",
    timeframe="1m",
    max_position=1,
    retry_count=3,
    retry_interval=5,
)
