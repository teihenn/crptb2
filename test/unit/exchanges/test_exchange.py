import unittest

import src.exchanges.exchange as sut
from src.config import ExchangeConfig
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

        exchange = sut.create_exchange(config)

        print(f"exchange: {exchange}")

        self.assertEqual(exchange.apiKey, config.api_key)
        self.assertEqual(exchange.secret, config.api_secret)
        self.assertEqual(exchange.options.get("defaultType"), "future")
