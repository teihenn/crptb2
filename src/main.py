import time
import traceback
from datetime import datetime

import src.exchanges.my_exchange as myexc
from src.config.config import Config
from src.strategy.new_rci_3 import RCIStrategy
from src.utils.discord import DiscordNotifier
from src.utils.logger import Logger


def get_next_candle_time(timeframe: str, current_timestamp: int) -> int:
    """
    次のローソク足の開始時刻を計算（ミリ秒）

    Parameters:
    -----------
    timeframe : str
        タイムフレーム（"1m", "5m", "15m", "1h", "4h", "1d"）
    current_timestamp : int
        現在のタイムスタンプ（ミリ秒）

    Returns:
    --------
    int
        次のローソク足の開始時刻（ミリ秒）

    Raises:
    -------
    ValueError
        無効なタイムフレームが指定された場合
    """
    intervals = {
        "1m": 60000,
        "5m": 300000,
        "15m": 900000,
        "1h": 3600000,
        "4h": 14400000,
        "1d": 86400000,
    }

    interval = intervals.get(timeframe)
    if interval is None:
        raise ValueError(
            f"無効なタイムフレーム: {timeframe}。有効な値: {list(intervals.keys())}"
        )

    return ((current_timestamp // interval) + 1) * interval


def main():
    # 設定の読み込み
    config = Config.load()

    discord = DiscordNotifier(config.discord.webhook_url)

    # ロガーの初期化
    logger = Logger.get_logger()
    logger.info("\n")  # 前のログと区切るために改行
    discord.print_and_notify("Starting trading bot...")

    discord.print_and_notify(f"Config: {config}")

    try:
        # 取引所の初期化
        exchange: myexc.MyExchange = myexc.MyExchange.create(config.exchange)

        # ストラテジーの初期化
        strategy = RCIStrategy(config.exchange)

        # 初期データの取得
        initial_data = exchange.fetch_ohlcv(
            config.exchange.symbol,
            timeframe=config.exchange.timeframe,
            limit=strategy.required_bars,
        )

        # 初期データを履歴に追加
        for candle in initial_data:
            strategy.update_historical_data(candle[4])  # close価格を追加

        # 時刻オフセットを取得
        time_offset = exchange.get_time_offset()
        logger.info(f"サーバー時刻とのオフセット: {time_offset}ms")

        while True:
            try:
                # ローカル時刻にオフセットを適用してサーバー時刻を取得（ミリ秒）
                current_server_time = int(time.time() * 1000) + time_offset
                next_candle_time = get_next_candle_time(
                    config.exchange.timeframe, current_server_time
                )

                # 待機時間を計算（秒に変換）
                wait_time = (next_candle_time - current_server_time) / 1000
                if wait_time > 0:
                    logger.debug(f"ローソク足更新までの待機時間: {wait_time}秒")
                    time.sleep(wait_time)

                # 少し待機して確実に新しいローソク足のデータを取得できるようにする。
                # 秒単位などの取引ロジックにする場合はここは変えないといけない
                time.sleep(2)

                # 定期的にオフセットを再計算
                if time.time() % 3600 < 10:  # 1時間ごとに更新
                    time_offset = exchange.get_time_offset()
                    logger.info(f"サーバー時刻とのオフセットを更新: {time_offset}ms")

                # 価格データを取得
                ohlcv = exchange.fetch_ohlcv(
                    config.exchange.symbol, timeframe=config.exchange.timeframe, limit=1
                )

                current_price = ohlcv[-1][4]

                # 価格データを履歴に追加
                strategy.update_historical_data(current_price)

                # インジケーターを計算
                df = strategy.calculate_indicators(strategy.historical_data)

                # 現在ポジションがある場合、決済判断
                if strategy.position and strategy.should_exit(df):
                    if strategy.position == "long":
                        exchange.create_market_sell_order(
                            config.exchange.symbol, config.exchange.position_size
                        )
                    else:
                        exchange.create_market_buy_order(
                            config.exchange.symbol, config.exchange.position_size
                        )
                    strategy.position = None

                # エントリー判断
                should_entry, position = strategy.should_entry(df)
                if should_entry and not strategy.position:
                    if position == "long":
                        exchange.create_market_buy_order(
                            config.exchange.symbol, config.exchange.position_size
                        )
                    else:
                        exchange.create_market_sell_order(
                            config.exchange.symbol, config.exchange.position_size
                        )
                    strategy.position = position

            except Exception as e:

                error_location = traceback.extract_tb(e.__traceback__)[-1]
                file_name = error_location.filename.split("/")[-1]  # ファイル名のみ抽出
                line_no = error_location.lineno
                func_name = error_location.name

                error_message = (
                    f"エラーが発生しました:\n"
                    f"場所: {file_name}, 行: {line_no}, 関数: {func_name}\n"
                    f"種類: {type(e).__name__}\n"
                    f"詳細: {str(e)}\n"
                    f"スタックトレース:\n{traceback.format_exc()}"
                )

                discord.print_and_notify(error_message, "エラー通知", level="error")

                time.sleep(config.exchange.retry_interval)

    except Exception as e:
        logger.error(f"初期化時にエラーが発生しました: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
