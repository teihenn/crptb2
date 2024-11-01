import ccxt

from src.config import ExchangeConfig
from src.exchanges import bybit


def create_exchange(config: ExchangeConfig) -> ccxt.Exchange:
    """取引所インスタンスを作成する

    Args:
        config (ExchangeConfig): 取引所の設定情報

    Returns:
        ccxt.Exchange: 設定済みの取引所インスタンス

    Raises:
        AttributeError: 指定された取引所名が存在しない場合
        BadRequest: 取引所固有の設定に失敗した場合
        MarginModeAlreadySet: 証拠金モード設定に失敗した場合
    """
    exchange = getattr(ccxt, config.name)(config.get_ccxt_config())

    # 取引所固有の初期設定
    if config.name == "bybit":
        # exchange = bybit.config(exchange, config)
        pass

    return exchange
