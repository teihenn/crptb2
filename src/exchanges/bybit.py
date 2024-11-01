import ccxt
from ccxt.base.errors import BadRequest, MarginModeAlreadySet

from src.config import ExchangeConfig


def config(exchange: ccxt.Exchange, config: ExchangeConfig) -> ccxt.Exchange:
    """Bybit取引所の設定を行う

    Args:
        exchange (ccxt.Exchange): 取引所インスタンス
        config (ExchangeConfig): 取引所の設定

    Returns:
        ccxt.Exchange: 設定済みの取引所インスタンス

    Raises:
        BadRequest: レバレッジ設定に失敗した場合
        MarginModeAlreadySet: 証拠金モード設定に失敗した場合
    """
    try:
        # BTC/USDTでは以下の例外でセット不可(BTCUSDなら可)
        # ccxt.base.errors.NotSupported: bybit setLeverage() only support linear and inverse market
        exchange.set_leverage(config.leverage, config.symbol)
    except BadRequest as e:
        # すでにセットされていて変更されていない場合にも
        # 例外を投げてしまうらしく握りつぶして良さげ
        # https://github.com/ccxt/ccxt/issues/6919
        if "Set leverage not modified" in str(e):
            print(f"Leverage is already set to {config.leverage}")
        else:
            raise e

    try:
        exchange.set_margin_mode(
            config.margin_type,
            config.symbol,
            params={
                "buy_leverage": config.buy_leverage,
                "sell_leverage": config.sell_leverage,
            },
        )
    except MarginModeAlreadySet as e:
        if "Cross/isolated margin mode is not modified" in str(e):
            print(f"Margin mode is already set to {config.margin_type}")
        else:
            raise e

    return exchange
