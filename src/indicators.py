import numpy as np
import pandas as pd


def calculate_rci(df: pd.DataFrame, period: int) -> pd.Series:
    """
    指定した期間のRCIを計算する関数

    Parameters:
    -----------
    df : pandas.DataFrame
        価格データを含むデータフレーム
    period : int
        RCI計算期間

    Returns:
    --------
    pandas.Series
        各時点のRCI値
    """
    if len(df) < period:
        return pd.Series(index=df.index, dtype=float)

    # 移動窓でRCIを計算
    rci_values = []
    close_series = df["close"]

    for i in range(period - 1, len(df)):
        window = close_series.iloc[i - period + 1 : i + 1]

        # 時系列順位（新しい方が大きい）
        time_ranks = np.arange(1, period + 1)

        # 価格順位（高い方が大きい）
        price_ranks = window.rank()

        # RCI計算
        d_square = np.sum((time_ranks - price_ranks) ** 2)
        rci = (1 - 6 * d_square / (period * (period**2 - 1))) * 100
        rci_values.append(rci)

    # 計算前の期間はNaNで埋める
    pad_length = period - 1
    rci_values = [np.nan] * pad_length + rci_values

    return pd.Series(rci_values, index=df.index)
