import unittest

import src.exchanges.exchange as exc
from src.config import ExchangeConfig
from test.config_for_test import BYBIT_TEST_CONFIG


class ExchangeDebug(unittest.TestCase):
    """取引所APIの動作確認用デバッグクラス

    Note:
        - このクラスはassertionを含まない動作確認用のメソッドを集めたものです
        - 開発時のデバッグや動作確認に使用します
    """

    def setUp(self):
        """テストの前準備"""
        self.config = ExchangeConfig(
            name="bybit",
            api_key=BYBIT_TEST_CONFIG["api_key"],
            api_secret=BYBIT_TEST_CONFIG["api_secret"],
            symbol="BTC/USDT",
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
        self.exchange = exc.create_exchange(self.config)

    def test_fetch_ticker(self):
        """ティッカー情報の表示"""
        ticker = self.exchange.fetch_ticker(self.config.symbol)

        print("\n=== Ticker Details ===")
        print(f"Symbol: {ticker['symbol']}")
        print(f"Timestamp: {ticker['timestamp']}")
        print(f"Datetime: {ticker['datetime']}")
        print("\n=== Price Information ===")
        print(f"Last: {ticker['last']}")
        print(f"Bid: {ticker['bid']}")
        print(f"Ask: {ticker['ask']}")
        print(f"High: {ticker['high']}")
        print(f"Low: {ticker['low']}")

        print("\n=== All Available Fields ===")
        for key, value in ticker.items():
            print(f"{key}: {value}")
