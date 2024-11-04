import pandas as pd


def calculate_rci(df, period):
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
    float
        最新のRCI値
    """
    close_prices = df["Close"].values.tolist()[-period:]
    # 時系列の順位（新しいデータほど大きい順位）
    time_ranks = list(range(period, 0, -1))
    # 価格の順位（降順）を計算
    price_ranks = pd.Series(close_prices).rank(ascending=False).tolist()

    # RCIの計算
    d = sum([(p_rank - t_rank) ** 2 for p_rank, t_rank in zip(price_ranks, time_ranks)])
    rci_value = (1 - 6 * d / (period * (period**2 - 1))) * 100

    return rci_value
