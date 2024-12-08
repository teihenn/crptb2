import time
from typing import List, Optional

import ccxt

from src.config.config import ExchangeConfig
from src.exchanges.bybit import config as bybit_config
from src.utils.discord import DiscordNotifier
from src.utils.logger import Logger
from src.utils.pnl_tracker import PnLTracker

logger = Logger.get_logger()


class MyExchange:
    def __init__(
        self, exchange: ccxt.Exchange, config: ExchangeConfig, discord: DiscordNotifier
    ):
        self._exchange = exchange
        self._config = config
        self._discord = discord
        self.pnl_tracker = PnLTracker(
            simulation_initial_balance=config.simulation_initial_balance,
            fee_rate=config.fee_rate,
            leverage=config.leverage,
            discord=discord,
        )

    @classmethod
    def create(cls, config: ExchangeConfig, discord: DiscordNotifier) -> "MyExchange":
        """取引所インスタンスを作成"""
        exchange_class = getattr(ccxt, config.name)
        exchange = exchange_class(config.get_ccxt_config())

        if config.name == "bybit":
            if config.testnet:
                exchange.set_sandbox_mode(True)
                discord.print_and_notify(
                    "Bybitのtestnetで稼働.", title="Bybit testnet mode", level="info"
                )

            # レバレッジと証拠金モードを設定
            bybit_config(exchange, config)

        instance = cls(exchange, config, discord)
        return instance

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

    def place_order(self, symbol: str, side: str, amount: float) -> Optional[dict]:
        """
        ポジションサイズをチェックして成行注文を実行

        Args:
            symbol (str): 取引ペア
            side (str): 注文サイド ("long" or "short")
            amount (float): 注文数量(正の値)

        Returns:
            Optional[dict]: 注文が成功した場合は注文情報、制限された場合はNone
        """
        current_position = self.get_position_size(symbol)  # 正の値
        new_position_size = current_position + amount

        if new_position_size > self._config.max_position:
            self._discord.print_and_notify(
                f"最大ポジション数量({self._config.max_position})を超えるため注文をスキップ(現在のポジションサイズ: {current_position})",
                title="注文制限",
                level="warning",
            )
            return None

        # dry_runモードの場合
        if self._config.dry_run:
            # 現在の価格を取得
            ticker = self._exchange.fetch_ticker(symbol)
            price = ticker["last"]

            # シミュレーション実行と通知メッセージの生成
            order_info = self.pnl_tracker.simulate_trade(
                symbol=symbol,
                side=side,
                price=price,
                amount=amount,
            )

            return order_info

        if side == "long":
            self._discord.send_only_mention()
            self._discord.print_and_notify(
                f"Creating market buy order - Symbol: {symbol}, Amount: {amount}",
                title="成行買い注文",
                level="info",
            )
            return self._exchange.create_market_buy_order(symbol, amount)
        else:
            self._discord.send_only_mention()
            self._discord.print_and_notify(
                f"Creating market sell order - Symbol: {symbol}, Amount: {amount}",
                title="成行売り注文",
                level="info",
            )
            return self._exchange.create_market_sell_order(symbol, amount)

    def get_position_info(self, symbol: str) -> tuple[float, Optional[str]]:
        """
        現在のポジション情報を取得

        Args:
            symbol (str): 取引ペア（例: 'BTCUSDT'）

        Returns:
            tuple[float, Optional[str]]: (ポジションサイズ, ポジションの方向)
            - ポジションサイズ: 常に正の値
            - ポジションの方向: "long", "short", None（ポジションなし）
        """
        try:
            # 先物取引所の場合
            if self._exchange.has["fetchPosition"]:
                position = self._exchange.fetch_position(symbol)
                if position is None or position["contracts"] == 0:
                    return 0.0, None
                return float(position["contracts"]), position["side"]

            # 現物取引所の場合
            elif self._exchange.has["fetchBalance"]:
                balance = self._exchange.fetch_balance()
                base_currency = symbol.split("/")[0]  # 例: 'BTC/USDT' -> 'BTC'
                size = float(balance[base_currency]["free"])
                return size, "long" if size > 0 else None

        except Exception as e:
            self._discord.print_and_notify(
                f"ポジション情報の取得に失敗: {str(e)}",
                title="ポジション情報取得エラー",
                level="error",
            )
            raise

        raise NotImplementedError(
            f"この取引所（{self._exchange.id}）はポジション情報の取得に対応していません"
        )

    def get_position_size(self, symbol: str) -> float:
        """
        現在のポジションサイズを取得（常に正の値）

        Args:
            symbol (str): 取引ペア（例: 'BTCUSDT'）

        Returns:
            float: ポジションサイズ（常に正の値）
        """
        size, _ = self.get_position_info(symbol)
        return size

    def close_all_position(self, symbol: str) -> Optional[dict]:
        """ポジションをすべて決済"""
        try:
            if self._config.dry_run:
                # 今持っているポジション(＝今保有中の全数量)
                position_size = self.pnl_tracker.position.amount

                # 現在の価格を取得
                ticker = self._exchange.fetch_ticker(symbol)
                price = ticker["last"]

                side = "sell" if self.pnl_tracker.position.side == "long" else "buy"
                self.pnl_tracker.simulate_trade(
                    symbol=symbol,
                    side=side,
                    price=price,
                    amount=abs(position_size),
                )
                return

            # 現在のポジションサイズを取得
            position_size, position_side = self.get_position_info(symbol)

            if position_size == 0:
                message = "決済すべきポジションがありません"
                self._discord.print_and_notify(
                    message, title="ポジション決済", level="warning"
                )
                return

            if position_side == "long":
                # ロングポジションの決済（成行売り）
                order = self._exchange.create_market_sell_order(
                    symbol, abs(position_size), params={"reduceOnly": True}
                )
                self._discord.send_only_mention()
                message = f"ロングポジションを決済しました: {order}"
                self._discord.print_and_notify(
                    message, title="ポジション決済", level="info"
                )
            elif position_side == "short":
                # ショートポジションの決済（成行買い）
                order = self._exchange.create_market_buy_order(
                    symbol, abs(position_size), params={"reduceOnly": True}
                )
                self._discord.send_only_mention()
                message = f"ショートポジションを決済しました: {order}"
                self._discord.print_and_notify(
                    message, title="ポジション決済", level="info"
                )
            else:
                self._discord.print_and_notify(
                    "MyExchange.close_all_position(): ポジションの方向が不明です",
                    title="ポジション決済",
                    level="error",
                )

        except Exception as e:
            error_message = f"ポジション決済に失敗: {str(e)}"
            self._discord.print_and_notify(
                error_message, title="ポジション決済エラー", level="error"
            )
            raise
