import unittest

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
            # symbol="BTCUSD",
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

        actual = sut.MyExchange.create(config)

        print(f"exchange: {actual}")

        self.assertEqual(actual._exchange.apiKey, config.api_key)
        self.assertEqual(actual._exchange.secret, config.api_secret)
        self.assertEqual(actual._exchange.options.get("defaultType"), "future")
