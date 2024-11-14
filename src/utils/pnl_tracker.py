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
    pnl: float = None  # 決済前はNone
    fee: float = 0.0


class PnLTracker:
    def __init__(
        self,
        simulation_initial_balance: float,
        fee_rate: float,
        leverage: float,
        discord: DiscordNotifier,
    ):
        self.simulation_initial_balance = (
            simulation_initial_balance  # シミュレーション用初期残高
        )
        self.current_balance = simulation_initial_balance  # 現在の残高
        self.fee_rate = fee_rate  # 取引手数料率
        self.trades: List[Trade] = []  # 取引履歴
        self.position: Optional[Trade] = None  # 今持っているポジション
        self.leverage = leverage
        self.discord = discord

    def add_trade(
        self, timestamp: int, side: str, price: float, amount: float
    ) -> Trade:
        # 取引手数料の計算
        fee = price * amount * self.fee_rate
        trade = Trade(
            timestamp=timestamp, side=side, price=price, amount=amount, fee=fee
        )

        # エントリー(エントリー時はポジションは持っていない想定)
        if self.position is None:
            self.position = trade
            self.trades.append(trade)
            return trade

        # 決済の場合
        if side != self.position.side:
            # 取引額の計算（レバレッジを考慮）
            trade_value = price * amount

            if side == "sell":  # ロングポジションの決済
                # (決済価格 - エントリー価格) / エントリー価格 = 価格変化率
                # 価格変化率 × レバレッジ × 取引額 = 損益

                # 価格変化率
                price_change_rate = (price - self.position.price) / self.position.price

                pnl = (
                    (price_change_rate * self.leverage * trade_value)
                    - fee
                    - self.position.fee
                )  # 現在売買のfeeと、エントリー時のfeeを引く
            else:  # ショートポジションの決済
                price_change_rate = (self.position.price - price) / self.position.price
                pnl = (
                    (price_change_rate * self.leverage * trade_value)
                    - fee
                    - self.position.fee
                )

            # デバッグ用のログ出力
            debug_msg = (
                f"PnL計算詳細:\n"
                f"side: {side}\n"
                f"エントリー価格: {self.position.price}\n"
                f"決済価格: {price}\n"
                f"価格変化率: {price_change_rate:.2%}\n"
                f"エントリー時の手数料: {self.position.fee}\n"
                f"決済時の手数料: {fee}\n"
                f"取引額: {trade_value}\n"
                f"レバレッジ: {self.leverage}\n"
                f"計算されたPnL: {pnl}"
            )
            self.discord.print_and_notify(debug_msg, title="PnL Debug", level="debug")

            self.position.pnl = pnl
            self.current_balance += pnl
            self.position = (
                None  # 全決済しているのでNoneにする # TODO: None代入で良いか
            )
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
        """取引サマリーを取得"""
        total_pnl = sum(trade.pnl for trade in self.trades if trade.pnl is not None)
        total_fee = sum(trade.fee for trade in self.trades)
        win_trades = sum(
            1 for trade in self.trades if trade.pnl is not None and trade.pnl > 0
        )
        total_trades = sum(1 for trade in self.trades if trade.pnl is not None)

        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            "初期残高": self.simulation_initial_balance,
            "現在残高": self.current_balance,
            "総損益": total_pnl,
            "総手数料": total_fee,
            "決済回数": total_trades,
            "勝率": f"{win_rate:.2f}%",
            "レバレッジ": f"{self.leverage}倍",
        }

    def get_trade_history(self, limit: int = 10) -> str:
        """
        取引履歴を取得（直近n件）

        Args:
            limit (int): 取得する取引履歴の件数（デフォルト: 10件）

        Returns:
            str: フォーマットされた取引履歴
        """
        history = "=== 直近の取引履歴 ===\n"
        # 直近n件を取得（新しい順）
        recent_trades = list(reversed(self.trades[-limit:]))

        for trade in recent_trades:
            dt = datetime.fromtimestamp(trade.timestamp / 1000)
            pnl_str = f"PnL: {trade.pnl:.2f}" if trade.pnl is not None else "未決済"
            history += (
                f"日時: {dt}, サイド: {trade.side}, "
                f"価格: {trade.price:.1f}, 数量: {trade.amount:.3f}, "
                f"{pnl_str}, 手数料: {trade.fee:.2f}\n"
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
            f"PnL: {trade.pnl}, 手数料: {trade.fee:.2f}\n\n"
            f"=== パフォーマンスサマリー ===\n"
        )
        for key, value in self.get_summary().items():
            if isinstance(value, float):
                message += f"{key}: {value:.2f}\n"
            else:
                message += f"{key}: {value}\n"

        self.discord.send_only_mention()
        self.discord.print_and_notify(
            # message, title="PnLTracker.simulate_trade", level="info"
            message,
            title="PnLTracker.simulate_trade",
            level="warning",  # 目立たせるため一旦Warningレベルにしとく
        )

        order_info = {"dry_run": True, "symbol": symbol, "side": side, "amount": amount}

        return order_info

    def print_summary(self, title: str = "パフォーマンスサマリー"):
        """現在のパフォーマンスサマリーを表示"""
        message = f"=== {title} ===\n"

        for key, value in self.get_summary().items():
            if isinstance(value, float):
                message += f"{key}: {value:.2f}\n"
            else:
                message += f"{key}: {value}\n"

        message += "\n" + self.get_trade_history()

        self.discord.print_and_notify(message, title=title, level="info")
