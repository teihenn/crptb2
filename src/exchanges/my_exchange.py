import time
from typing import List, Optional

import ccxt

from src.config.config import ExchangeConfig
from src.utils.discord import DiscordNotifier
from src.utils.logger import Logger

# from src.exchanges import bybit

logger = Logger.get_logger()


class MyExchange:
    def __init__(self, exchange: ccxt.Exchange, discord: DiscordNotifier):
        self._exchange = exchange
        self._discord = discord

    @classmethod
    def create(cls, config: ExchangeConfig, discord: DiscordNotifier) -> "MyExchange":
        """取引所インスタンスを作成"""
        exchange_class = getattr(ccxt, config.name)
        exchange = exchange_class(config.get_ccxt_config())

        # Bybitのtestnetモードを有効にする
        if config.name == "bybit" and config.testnet:
            discord.print_and_notify(
                "Bybitのtestnetで稼働.", title="Bybit testnet mode", level="info"
            )
            exchange.set_sandbox_mode(True)

        return cls(exchange, discord)

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
        data = self._exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        logger.info(f"Fetched {len(data)} candles")

        ## タイムスタンプをISO8601形式に変換したデータをログ出力
        # debug_data = [
        #    [self._exchange.iso8601(candle[0]), *candle[1:]] for candle in data
        # ]
        # logger.debug(debug_data)
        ## for candle in debug_data:
        ##    print(candle[4])  # 終値を出力
        # time.sleep(5)

        return data

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

    def create_market_buy_order(self, symbol: str, amount: float):
        """成行買い注文"""
        self._discord.print_and_notify(
            f"Creating market buy order - Symbol: {symbol}, Amount: {amount}",
            title="成行買い注文",
            level="info",
        )
        return self._exchange.create_market_buy_order(symbol, amount)

    def create_market_sell_order(self, symbol: str, amount: float):
        """成行売り注文"""
        self._discord.print_and_notify(
            f"Creating market sell order - Symbol: {symbol}, Amount: {amount}",
            title="成行売り注文",
            level="info",
        )
        return self._exchange.create_market_sell_order(symbol, amount)

    def get_position_size(self, symbol: str) -> float:
        """
        現在のポジションサイズを取得

        Args:
            symbol (str): 取引ペア（例: 'BTCUSDT'）

        Returns:
            float: ポジションサイズ（ロングはプラス、ショートはマイナス）
        """
        try:
            # 先物取引所の場合
            if self._exchange.has["fetchPosition"]:
                position = self._exchange.fetch_position(symbol)
                if position is None or position["contracts"] == 0:
                    return 0.0
                # contractsは保有数量、sideはポジションの方向
                size = float(position["contracts"])
                return size if position["side"] == "long" else -size

            # 現物取引所の場合
            elif self._exchange.has["fetchBalance"]:
                balance = self._exchange.fetch_balance()
                base_currency = symbol.split("/")[0]  # 例: 'BTC/USDT' -> 'BTC'
                return float(balance[base_currency]["free"])

        except Exception as e:
            self._discord.print_and_notify(
                f"ポジションサイズの取得に失敗: {str(e)}",
                title="ポジションサイズ取得エラー",
                level="error",
            )
            raise

        raise NotImplementedError(
            f"この取引所（{self._exchange.id}）はポジションサイズの取得に対応していません"
        )

    def close_all_position(self, symbol: str) -> None:
        """
        保有中のポジション（ロング/ショート）を全て成行決済

        Args:
            symbol (str): 取引ペア（例: 'BTC/USDT:USDT'）
        """
        try:
            # 現在のポジションサイズを取得
            position_size = self.get_position_size(symbol)

            if position_size == 0:
                message = "決済すべきポジションがありません"
                self._discord.print_and_notify(
                    message, title="ポジション決済", level="warning"
                )
                return

            if position_size > 0:
                # ロングポジションの決済（成行売り）
                order = self._exchange.create_market_sell_order(
                    symbol, abs(position_size), params={"reduceOnly": True}
                )
                message = f"ロングポジションを決済しました: {order}"
                self._discord.print_and_notify(
                    message, title="ポジション決済", level="info"
                )
            else:
                # ショートポジションの決済（成行買い）
                order = self._exchange.create_market_buy_order(
                    symbol, abs(position_size), params={"reduceOnly": True}
                )
                message = f"ショートポジションを決済しました: {order}"
                self._discord.print_and_notify(
                    message, title="ポジション決済", level="info"
                )

        except Exception as e:
            error_message = f"ポジション決済に失敗: {str(e)}"
            self._discord.print_and_notify(
                error_message, title="ポジション決済エラー", level="error"
            )
            raise
