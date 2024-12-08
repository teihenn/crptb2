import time
import traceback
from datetime import datetime

import src.exchanges.my_exchange as myexc
from src.config.config import Config
from src.historical_data import HistoricalData
from src.strategy.my_strategy import MyStrategy
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
        "6h": 21600000,
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

    discord = DiscordNotifier(
        config.discord.webhook_url,
        config.discord.mention_user_id,
        config.discord.enabled,
    )

    # ロガーの初期化
    logger = Logger.get_logger()
    logger.info("\n")  # 前のログと区切るために改行

    bot_activate_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    discord.print_and_notify(f"🤖 Starting trading bot... ({bot_activate_time})")
    discord.print_and_notify(f"Config: {config}", title="Config")

    error_count = 0

    try:
        # 取引所の初期化
        exchange: myexc.MyExchange = myexc.MyExchange.create(config.exchange, discord)

        # 現在のポジション状態を確認
        current_position, position_side = exchange.get_position_info(
            config.exchange.symbol
        )

        # ストラテジーの初期化
        strategy = MyStrategy(config)
        if position_side is not None:
            strategy.position = position_side
            discord.print_and_notify(
                f"既存ポジションを検出: {strategy.position}, {current_position}",
                level="info",
            )

        # 保持しておく必要があるバー数。
        # 例: ストラテジーで指標計算に必要なバー数が101の場合。
        # (100本＋1本。＋1本は一つ前の時間でも指標が計算できている必要があるため。)
        # この場合はrequired_bars = 202となる。
        # 202本取得した場合、確定足の本数は最新の一つを除いた201本となる。
        # 201本あれば、100本分くらいのローソク足や指標計算結果の描画と、
        # エントリー判断の計算に必要なデータは十分である。
        required_bars = strategy.required_bars * 2

        # 初期データの取得
        initial_data = exchange.fetch_ohlcv(
            config.exchange.symbol,
            timeframe=config.exchange.timeframe,
            limit=required_bars,
        )
        historical_data = HistoricalData(
            required_bars, initial_data[:-1], discord
        )  # 最後の要素（未確定足）を除外

        # 時刻オフセットを取得
        time_offset = exchange.get_time_offset()
        discord.print_and_notify(f"サーバー時刻とのオフセット: {time_offset}ms")

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
                    discord.print_and_notify(
                        f"ローソク足更新までの待機時間: {wait_time}秒"
                    )
                    time.sleep(wait_time)

                # 少し待機して確実に新しいローソク足のデータを取得できるようにする。
                # 秒単位などの取引ロジックにする場合はここは変えないといけない
                time.sleep(2)

                # 定期的にオフセットを再計算
                if time.time() % 3600 < 10:  # 1時間ごとに更新
                    time_offset = exchange.get_time_offset()
                    discord.print_and_notify(
                        f"サーバー時刻とのオフセットを更新: {time_offset}ms",
                        level="debug",
                    )

                # 最新の確定足を取得
                ohlcv = exchange.fetch_ohlcv(
                    config.exchange.symbol,
                    timeframe=config.exchange.timeframe,
                    limit=2,  # 2つ取得すると、先頭要素が最新の確定足
                )
                historical_data.update(ohlcv[0])  # 確定済みのローソク足を使用

                # インジケーターを計算
                df = strategy.calculate_indicators(historical_data.data)

                # チャートの作成と送信
                chart_image, timestamp = strategy.create_chart(df)
                discord.send_image(
                    image_data=chart_image, message=f"チャート更新 ({timestamp})"
                )

                # 現在ポジションがある場合、決済判断し条件を満たせば全決済
                # if strategy.position and strategy.should_exit(df):
                if strategy.position and strategy.should_exit2(df):
                    exchange.close_all_position(config.exchange.symbol)
                    strategy.position = None

                # エントリー判断
                should_entry, position = strategy.should_entry(df)
                if should_entry:
                    if strategy.position:
                        discord.print_and_notify(
                            "既にポジションを持っているためエントリーしない.",
                            level="info",
                        )
                    else:
                        # exchange.place_order(
                        #    config.exchange.symbol, position, config.exchange.position_size
                        # )
                        exchange.place_order(
                            config.exchange.symbol,
                            position,
                            config.exchange.max_position,  # 一度にmax_position分のポジションを持つ方針
                        )
                        strategy.position = position  # DryRun時もポジション方向を記録

                # DryRun時はPnLを表示
                if config.exchange.dry_run:
                    exchange.pnl_tracker.print_summary()

            except Exception as e:
                error_location = traceback.extract_tb(e.__traceback__)[-1]
                file_name = error_location.filename.split("/")[-1]  # ファイル名のみ抽出
                line_no = error_location.lineno
                func_name = error_location.name

                error_message = (
                    f"エラーが発生しました。{config.exchange.retry_interval}秒後にリトライします:\n"
                    f"場所: {file_name}, 行: {line_no}, 関数: {func_name}\n"
                    f"種類: {type(e).__name__}\n"
                    f"詳細: {str(e)}\n"
                    f"スタックトレース:\n{traceback.format_exc()}"
                )
                discord.print_and_notify(
                    error_message, title="エラー通知", level="error"
                )

                error_count += 1
                if config.exchange.retry_count < error_count:
                    discord.print_and_notify(
                        "リトライ回数を超えたため異常終了します。",
                        title="エラー通知",
                        level="error",
                    )
                    exit()
                else:
                    time.sleep(config.exchange.retry_interval)

    except Exception as e:
        discord.print_and_notify(
            f"初期化時にエラーが発生したので異常終了します: {str(e)}",
            title="初期化エラー",
            level="error",
        )
        exit()


if __name__ == "__main__":
    main()
