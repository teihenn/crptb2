import logging
from typing import Optional

from src.config.config import Config, LoggingConfig

config_logging = Config.load().logging


class Logger:
    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """ロガーのインスタンスを取得"""
        if cls._instance is None:
            cls._instance = cls._setup(config_logging)
        return cls._instance

    @classmethod
    def _setup(cls, config: LoggingConfig) -> logging.Logger:
        """ロガーの初期化"""
        if cls._instance is not None:
            return cls._instance

        logger = logging.getLogger("trading_bot")
        level = getattr(logging, config.level.upper())
        logger.setLevel(level)

        # ファイルハンドラの設定
        fh = logging.FileHandler(config.file)
        fh.setLevel(level)

        # コンソールハンドラの設定
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # フォーマッターの設定
        formatter = logging.Formatter(
            # "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # ハンドラの追加
        logger.addHandler(fh)
        logger.addHandler(ch)

        cls._instance = logger
        return logger
