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

    def __repr__(self) -> str:
        """機密情報をマスキングして文字列表現を返す"""
        return (
            f"ExchangeConfig("
            f"name='{self.name}', "
            f"api_key='{'*' * 8}', "  # マスキング
            f"api_secret='{'*' * 8}', "  # マスキング
            f"symbol='{self.symbol}', "
            f"position_size={self.position_size}, "
            f"leverage={self.leverage}, "
            f"buy_leverage={self.buy_leverage}, "
            f"sell_leverage={self.sell_leverage}, "
            f"margin_type='{self.margin_type}', "
            f"timeframe='{self.timeframe}', "
            f"max_position={self.max_position}, "
            f"retry_count={self.retry_count}, "
            f"retry_interval={self.retry_interval}"
            f")"
        )

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
class DiscordConfig:
    webhook_url: str
    enabled: bool = True  # 通知の有効/無効を切り替え

    def __repr__(self) -> str:
        """webhook_urlをマスキングして文字列表現を返す"""
        return (
            f"DiscordConfig("
            f"webhook_url='{'*' * 8}', "  # マスキング
            f"enabled={self.enabled}"
            f")"
        )


@dataclass
class Config:
    logging: LoggingConfig
    exchange: ExchangeConfig
    discord: DiscordConfig

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
            discord=DiscordConfig(**config_dict["discord"]),
        )
