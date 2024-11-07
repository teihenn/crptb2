import pandas as pd

from src.utils.discord import DiscordNotifier
from src.utils.time_utils import convert_to_jst


class HistoricalData:
    COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(
        self,
        num_bars: int,
        initial_data: list[list],
        discord: DiscordNotifier,
    ):
        """_summary_

        Args:
            num_bars (int): 保持するデータ数
            initial_data (list[list]): 初期データ。本数分のCOLUMNSデータリストのリスト
            discord (DiscordNotifier): discordクライアント
        """
        self.num_bars = num_bars  # 保持するデータ数
        initial_df = pd.DataFrame(initial_data, columns=self.COLUMNS)
        initial_df.set_index("timestamp", inplace=True)
        self.data = convert_to_jst(initial_df)
        self.discord = discord

    def update(self, new_data: list, enable_log: bool = True) -> None:
        """1件分のデータで更新する"""
        new_df = pd.DataFrame([new_data], columns=self.COLUMNS)
        new_df.set_index("timestamp", inplace=True)
        new_df = convert_to_jst(new_df)

        # 同じ時刻の足の場合は更新し、そうでない場合は追加
        if new_df.index[-1] == self.data.index[-1]:
            self.data.loc[new_df.index[-1]] = new_df.iloc[-1]
        else:
            self.data = pd.concat([self.data, new_df])

        # データ数を制限
        if len(self.data) > self.num_bars:
            self.data = self.data.tail(self.num_bars)

        # データの状態を確認（日本時間で表示）
        if enable_log:
            # self.discord.print_and_notify(
            #    f"HistoricalData.update, Latest prices:\n{self.data.tail()}",
            #    "データ更新",
            #    level="debug",
            # )
            pass
