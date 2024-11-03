import logging
import time

import src.exchanges.exchange as exc
from src.config import BYBIT
from src.strategy.new_rci_3 import RCIStrategy


def setup_logger():
    """ロガーの設定"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # ファイルハンドラの設定
    fh = logging.FileHandler("trading_bot.log")
    fh.setLevel(logging.INFO)

    # コンソールハンドラの設定
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # フォーマッターの設定
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # ハンドラの追加
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def get_sleep_time(timeframe: str) -> int:
    """
    時間軸に基づいて待機時間を計算
    """
    sleep_seconds = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400,
    }
    return sleep_seconds.get(timeframe, 60)  # デフォルトは60秒


def get_time_offset(exchange) -> int:
    """
    取引所のサーバー時刻と現在時刻のオフセットを計算する。
    TODO: fetch_time()はすべての取引所でサポートされているわけではないかもしれないので注意
    Bybitはサポートされている。
    """
    server_time = exchange.fetch_time()  # ミリ秒
    local_time = int(time.time() * 1000)  # ローカル時刻をミリ秒に変換
    return server_time - local_time


def get_next_candle_time(timeframe: str, current_timestamp: int) -> int:
    """次のローソク足の開始時刻を計算（ミリ秒）"""
    intervals = {
        "1m": 60000,
        "5m": 300000,
        "15m": 900000,
        "1h": 3600000,
        "4h": 14400000,
        "1d": 86400000,
    }
    interval = intervals.get(timeframe, 60000)
    return ((current_timestamp // interval) + 1) * interval


def main():
    # ロガーの初期化
    logger = setup_logger()

    # 設定の読み込み
    config = BYBIT

    try:
        # 取引所の初期化
        exchange = exc.create_exchange(config)

        # ストラテジーの初期化
        strategy = RCIStrategy(config)

        # 初期データの取得
        initial_data = exchange.fetch_ohlcv(
            config.symbol, timeframe=config.timeframe, limit=strategy.required_bars
        )

        # 初期データを履歴に追加
        for candle in initial_data:
            strategy.update_historical_data(candle[4])  # close価格を追加

        # 時刻オフセットを取得
        time_offset = get_time_offset(exchange)
        logger.info(f"サーバー時刻とのオフセット: {time_offset}ms")

        while True:
            try:
                # ローカル時刻にオフセットを適用してサーバー時刻を取得（ミリ秒）
                current_server_time = int(time.time() * 1000) + time_offset
                next_candle_time = get_next_candle_time(
                    config.timeframe, current_server_time
                )

                # 待機時間を計算（秒に変換）
                wait_time = (next_candle_time - current_server_time) / 1000
                if wait_time > 0:
                    time.sleep(wait_time)

                # 少し待機して確実に新しいローソク足のデータを取得できるようにする。
                # 秒単位などの取引ロジックにする場合はここは変えないといけない
                time.sleep(2)

                # 定期的にオフセットを再計算
                if time.time() % 3600 < 10:  # 1時間ごとに更新
                    time_offset = get_time_offset(exchange)
                    logger.info(f"サーバー時刻とのオフセットを更新: {time_offset}ms")

                # 価格データを取得
                ohlcv = exchange.fetch_ohlcv(
                    config.symbol, timeframe=config.timeframe, limit=1
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
                            config.symbol, config.position_size
                        )
                    else:
                        exchange.create_market_buy_order(
                            config.symbol, config.position_size
                        )
                    strategy.position = None

                # エントリー判断
                should_entry, position = strategy.should_entry(df)
                if should_entry and not strategy.position:
                    if position == "long":
                        exchange.create_market_buy_order(
                            config.symbol, config.position_size
                        )
                    else:
                        exchange.create_market_sell_order(
                            config.symbol, config.position_size
                        )
                    strategy.position = position

                # 時間軸に基づいて待機
                sleep_time = get_sleep_time(config.timeframe)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"ループ内でエラーが発生しました: {str(e)}", exc_info=True)
                time.sleep(config.retry_interval)

    except Exception as e:
        logger.error(f"初期化時にエラーが発生しました: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
