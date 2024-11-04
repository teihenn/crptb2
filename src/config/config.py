from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class LoggingConfig:
    level: str
    file: str


@dataclass
class ExchangeConfig:
    name: str
    api_key: str
    api_secret: str
    symbol: str
    position_size: float
    leverage: int
    buy_leverage: int
    sell_leverage: int
    margin_type: str  # isolated or cross
    timeframe: str
    max_position: float
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


@dataclass
class Config:
    logging: LoggingConfig
    exchange: ExchangeConfig

    @classmethod
    def load(cls, config_path: str = None) -> "Config":
        """設定ファイルを読み込む"""
        if config_path is None:
            # プロジェクトのルートディレクトリを基準にパスを解決
            root_dir = Path(__file__).parent.parent.parent
            config_path = root_dir / "src" / "config" / "config.yaml"

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        return cls(
            logging=LoggingConfig(**config_dict["logging"]),
            exchange=ExchangeConfig(**config_dict["exchange"]),
        )
