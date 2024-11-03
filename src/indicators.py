import pandas as pd


def calculate_rci(df, period):
    """
    RCIを計算する関数
    """
    close_prices = df["Close"].values.tolist()
    rci = []
    for i in range(period, len(close_prices)):
        period_prices = close_prices[i - period : i]
        ranked_prices = sorted(period_prices, reverse=True)
        price_ranks = [ranked_prices.index(price) + 1 for price in period_prices]
        d = sum([(rank - (period + 1) / 2) ** 2 for rank in price_ranks])
        rci_value = (1 - 6 * d / (period * (period**2 - 1))) * 100
        rci.append(rci_value)
    return pd.Series(rci, index=df.index[period:])
