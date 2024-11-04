import logging
from typing import List, Optional

import ccxt

# from src.exchanges import bybit

logger = logging.getLogger(__name__)


class MyExchange:
    def __init__(self, exchange: ccxt.Exchange):
        self._exchange = exchange

    @classmethod
    def create(cls, config) -> "MyExchange":
        """取引所インスタンスを作成"""
        exchange_class = getattr(ccxt, config.exchange)
        exchange = exchange_class(
            {"apiKey": config.api_key, "secret": config.api_secret}
        )
        return cls(exchange)

    def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1m", limit: Optional[int] = None
    ) -> List[List]:
        """
        OHLCVデータを取得
        Returns:
            [[timestamp, open, high, low, close, volume], ...]
        """
        logger.debug(
            f"Fetching OHLCV - Symbol: {symbol}, Timeframe: {timeframe}, Limit: {limit}"
        )
        data = self._exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        logger.debug(f"Fetched {len(data)} candles")
        return data

    def fetch_time(self) -> int:
        """サーバー時刻を取得（ミリ秒）"""
        return self._exchange.fetch_time()

    def create_market_buy_order(self, symbol: str, amount: float):
        """成行買い注文"""
        logger.info(f"Creating market buy order - Symbol: {symbol}, Amount: {amount}")
        return self._exchange.create_market_buy_order(symbol, amount)

    def create_market_sell_order(self, symbol: str, amount: float):
        """成行売り注文"""
        logger.info(f"Creating market sell order - Symbol: {symbol}, Amount: {amount}")
        return self._exchange.create_market_sell_order(symbol, amount)
