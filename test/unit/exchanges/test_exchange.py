import unittest
from unittest.mock import MagicMock

import src.exchanges.my_exchange as sut
from src.config.config import ExchangeConfig
from test.config_for_test import BYBIT_TEST_CONFIG


class TestExchange(unittest.TestCase):
    def test_create_exchange_bybit(self):
        """Bybit取引所の正常系の初期化テスト"""
        config = ExchangeConfig(
            name="bybit",
            api_key=BYBIT_TEST_CONFIG["api_key"],
            api_secret=BYBIT_TEST_CONFIG["api_secret"],
            symbol="BTCUSDT",
            position_size=0.001,
            leverage=2,
            buy_leverage=2,
            sell_leverage=2,
            margin_type="isolated",
            timeframe="1m",
            max_position=1,
            retry_count=3,
            retry_interval=5,
        )

        # Discordモックを作成
        mock_discord = MagicMock()

        actual = sut.MyExchange.create(config, mock_discord)

        print(f"exchange: {actual}")

        self.assertEqual(actual._exchange.apiKey, config.api_key)
        self.assertEqual(actual._exchange.secret, config.api_secret)
        self.assertEqual(actual._exchange.options.get("defaultType"), "linear")


class TestExchangeBybitLive(unittest.TestCase):
    """Bybit APIを使用した実際のテスト"""

    def test_get_position_size_basic(self):
        """ポジションサイズ取得の基本テスト"""
        # 設定
        config = ExchangeConfig(
            name="bybit",
            api_key=BYBIT_TEST_CONFIG["api_key"],
            api_secret=BYBIT_TEST_CONFIG["api_secret"],
            symbol="BTCUSDT",
            position_size=0.001,
            leverage=2,
            buy_leverage=2,
            sell_leverage=2,
            margin_type="isolated",
            timeframe="1m",
            max_position=1,
            retry_count=3,
            retry_interval=5,
        )

        # Discordモックを作成
        mock_discord = MagicMock()

        # 取引所インスタンスを作成
        exchange = sut.MyExchange.create(config, mock_discord)

        # ポジションサイズを取得
        position_size = exchange.get_position_size(config.symbol)

        # 結果を表示
        print(f"Position size: {position_size}")

        # ポジションを持っていないことを確認
        self.assertEqual(position_size, 0.0)
