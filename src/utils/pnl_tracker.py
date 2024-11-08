import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.utils.discord import DiscordNotifier


@dataclass
class Trade:
    timestamp: int
    side: str  # "buy" or "sell"
    price: float
    amount: float  # 正の数
    pnl: float = 0.0
    fee: float = 0.0


class PnLTracker:
    def __init__(
        self,
        simulation_initial_balance: float,
        fee_rate: float,
        discord: DiscordNotifier,
    ):
        self.simulation_initial_balance = (
            simulation_initial_balance  # シミュレーション用初期残高
        )
        self.current_balance = simulation_initial_balance  # 現在の残高
        self.fee_rate = fee_rate  # 取引手数料率
        self.trades: List[Trade] = []  # 取引履歴
        self.position: Optional[Trade] = None  # 今持っているポジション
        self.discord = discord

    def add_trade(
        self, timestamp: int, side: str, price: float, amount: float
    ) -> Trade:
        fee = price * amount * self.fee_rate
        trade = Trade(
            timestamp=timestamp, side=side, price=price, amount=amount, fee=fee
        )

        # エントリー(エントリー時はポジションは持っていない想定)
        if self.position is None:
            self.position = trade
            self.trades.append(trade)
            return trade

        # ポジションがある場合、決済時のPnLを計算
        # 現在売買のfeeと、エントリー時のfeeを引く
        if side != self.position.side:  # 反対売買の場合
            if side == "sell":
                pnl = (price - self.position.price) * amount - fee - self.position.fee
            else:  # side == "buy"
                pnl = (self.position.price - price) * amount - fee - self.position.fee

            self.position.pnl = pnl  # PnLをエントリートレードに記録
            self.current_balance += pnl
            self.position = None  # 全決済しているのでNoneにする # TODO: None代入で良いの？self.tradesも消される？
        else:
            # 以下の処理だと同じ方向の取引の場合は上書きされてしまうが、
            # そもそも同じ方向に複数回エントリーすることを想定した作りになっていないので
            # ここには来ないはず
            self.discord.print_and_notify(
                "PnLTracker.add_trade: 同じ方向の取引が2回連続で発生しました(シミュレーション)",
                title="Warning",
                level="warn",
            )
            self.position = trade

        self.trades.append(trade)
        return trade

    def get_summary(self) -> dict:
        total_pnl = sum(trade.pnl for trade in self.trades)
        win_trades = [trade for trade in self.trades if trade.pnl > 0]
        lose_trades = [trade for trade in self.trades if trade.pnl < 0]

        return {
            "初期残高(USDT)": self.simulation_initial_balance,
            "現在残高(USDT)": self.current_balance,
            "総損益(USDT)": total_pnl,
            "総取引数": len(self.trades),
            "勝率": len(win_trades) / len(self.trades) if self.trades else 0,
            "平均利益(USDT)": sum(t.pnl for t in win_trades) / len(win_trades)
            if win_trades
            else 0,
            "平均損失(USDT)": sum(t.pnl for t in lose_trades) / len(lose_trades)
            if lose_trades
            else 0,
            "合計手数料(USDT)": sum(trade.fee for trade in self.trades),
        }

    def get_trade_history(self) -> str:
        history = "取引履歴:\n"
        for trade in self.trades:
            dt = datetime.fromtimestamp(trade.timestamp / 1000)
            history += (
                f"日時: {dt}, サイド: {trade.side}, "
                f"価格: {trade.price:.1f}, 数量: {trade.amount:.3f}, "
                f"PnL: {trade.pnl:.2f}, 手数料: {trade.fee:.2f}\n"
            )
        return history

    def simulate_trade(
        self, symbol: str, side: str, price: float, amount: float
    ) -> tuple[dict, str]:
        """
        取引をシミュレートし、結果と通知メッセージを返す

        Args:
            symbol (str): 取引ペア
            side (str): 取引サイド（"buy" or "sell"）
            price (float): 価格
            amount (float): 数量(buyでもsellでも正の数)

        Returns:
            tuple[dict, str]: (注文情報, 通知メッセージ)
        """
        timestamp = int(time.time() * 1000)  # タイムスタンプ(ミリ秒)

        # トレードを記録
        trade = self.add_trade(
            timestamp=timestamp, side=side, price=price, amount=amount
        )

        # 通知メッセージを生成
        message = (
            f"[DRY RUN] 注文をシミュレート\n"
            f"Symbol: {symbol}, Side: {side}, Price: {price}, Amount: {amount}\n"
            f"PnL: {trade.pnl:.2f}, 手数料: {trade.fee:.2f}\n\n"
            f"=== パフォーマンスサマリー ===\n"
        )
        for key, value in self.get_summary().items():
            if isinstance(value, float):
                message += f"{key}: {value:.2f}\n"
            else:
                message += f"{key}: {value}\n"

        self.discord.print_and_notify(
            message, title="PnLTracker.simulate_trade", level="info"
        )

        order_info = {"dry_run": True, "symbol": symbol, "side": side, "amount": amount}

        return order_info
