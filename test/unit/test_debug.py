import unittest

import src.exchanges.my_exchange as myexc
from src.config.config import ExchangeConfig
from test.config_for_test import BYBIT_TEST_CONFIG


class TestExchangeDebug(unittest.TestCase):
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
            timeframe="15m",
            max_position=1,
            retry_count=3,
            retry_interval=5,
        )
        self.exchange = myexc.MyExchange.create(self.config)

    def test_fetch_ohlcv(self):
        """OHLCV（ローソク足）データの表示"""
        print("\n---------- test_fetch_ohlcv ----------")
        ohlcv = self.exchange.fetch_ohlcv(
            self.config.symbol,
            timeframe=self.config.timeframe,
            limit=5,  # 直近5件のデータを取得
        )

        print("\n=== OHLCV Details ===")
        print(f"Symbol: {self.config.symbol}")
        print(f"Timeframe: {self.config.timeframe}")

        print("\n=== Latest Candles ===")
        candle = ohlcv[-2]  # 最新の確定足
        timestamp = self.exchange._exchange.iso8601(candle[0])
        print(f"\nTimestamp: {timestamp}")
        print(f"Open: {candle[1]}")
        print(f"High: {candle[2]}")
        print(f"Low: {candle[3]}")
        print(f"Close: {candle[4]}")
        print(f"Volume: {candle[5]}")
