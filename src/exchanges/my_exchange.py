import time
from typing import List, Optional

import ccxt

from src.config.config import ExchangeConfig
from src.utils.logger import Logger

# from src.exchanges import bybit

logger = Logger.get_logger()


class MyExchange:
    def __init__(self, exchange: ccxt.Exchange):
        self._exchange = exchange

    @classmethod
    def create(cls, config: ExchangeConfig) -> "MyExchange":
        """取引所インスタンスを作成"""
        exchange_class = getattr(ccxt, config.name)
        exchange = exchange_class(config.get_ccxt_config())
        # Bybitのtestnetモードを有効にする
        if config.name == "bybit" and config.testnet:
            exchange.set_sandbox_mode(True)


    def fetch_ohlcv(
        self, symbol: str, timeframe: str = "15m", limit: Optional[int] = None
    ) -> List[List]:
        """
        OHLCVデータを取得する。

        最新分は未確定足である可能性があることに留意する。
        (https://docs.ccxt.com/#/?id=ohlcv-candlestick-charts)
        (ローソク足更新のタイミングで呼び出せば、最新分もほぼ確定足にできる。)

        Returns:
            [[timestamp, open, high, low, close, volume], ...]
            並び順は古い順。
        """
        logger.info(
            f"Fetching OHLCV - Symbol: {symbol}, Timeframe: {timeframe}, Limit: {limit}"
        )
        limit = 48
        data = self._exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        logger.info(f"Fetched {len(data)} candles")

        ## タイムスタンプをISO8601形式に変換したデータをログ出力
        # debug_data = [
        #    [self._exchange.iso8601(candle[0]), *candle[1:]] for candle in data
        # ]
        # for candle in debug_data:
        #    print(candle[4])  # 終値を出力

        return data

    def create_market_buy_order(self, symbol: str, amount: float):
        """成行買い注文"""
        logger.info(f"Creating market buy order - Symbol: {symbol}, Amount: {amount}")
        return self._exchange.create_market_buy_order(symbol, amount)

    def create_market_sell_order(self, symbol: str, amount: float):
        """成行売り注文"""
        logger.info(f"Creating market sell order - Symbol: {symbol}, Amount: {amount}")
        return self._exchange.create_market_sell_order(symbol, amount)

    def get_time_offset(self) -> int:
        """
        取引所のサーバー時刻と現在時刻のオフセットを計算する。
        TODO: fetch_time()はすべての取引所でサポートされているわけではないかもしれないので注意
        Bybitはサポートされている。

        Returns:
            int: オフセット（ミリ秒）
        """
        server_time = self._exchange.fetch_time()  # サーバー時刻を取得(ミリ秒)
        local_time = int(time.time() * 1000)  # ローカル時刻をミリ秒に変換
        return server_time - local_time
