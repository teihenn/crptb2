from abc import ABC, abstractmethod

import pandas as pd

from src.config.config import Config
from src.utils.discord import DiscordNotifier
from src.utils.logger import Logger


class BaseStrategy(ABC):
    """
    ストラテジーの基底クラス
    """

    def __init__(self, config: Config):
        """
        Parameters:
        -----------
        config : Config
            設定オブジェクト
        """
        self.position = None  # 'long' or 'short' or None
        self.logger = Logger.get_logger()

        # Discord通知の設定
        self.discord = DiscordNotifier(
            config.discord.webhook_url,
            config.discord.mention_user_id,
            config.discord.enabled,
        )

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """必要なインジケーターを計算"""
        pass

    @abstractmethod
    def should_entry(self, df: pd.DataFrame) -> tuple[bool, str]:
        """エントリー判断。(エントリーすべきか, ポジション方向)を返す"""
        pass

    @abstractmethod
    def should_exit(self, df: pd.DataFrame) -> bool:
        """決済判断"""
        pass
