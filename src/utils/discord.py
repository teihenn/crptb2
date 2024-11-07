import io
from typing import Optional

import requests

from src.utils.logger import Logger


class DiscordNotifier:
    """
    Discord通知を送信するクラス
    """

    # Discordのメッセージカラー定数
    COLORS = {
        "debug": 0x808080,  # グレー色
        "info": 0x00FF00,  # 緑色
        "warning": 0xFFA500,  # オレンジ色
        "error": 0xFF0000,  # 赤色
    }

    def __init__(self, webhook_url: str, enabled: bool = True):
        """
        Parameters:
        -----------
        webhook_url : str
            DiscordのWebhook URL
        enabled : bool, default=True
            Discord通知の有効/無効
        """
        self.webhook_url = webhook_url
        self.logger = Logger.get_logger()
        self.enabled = enabled

    def send_message(
        self, message: str, title: Optional[str] = None, level: str = "info"
    ) -> bool:
        """
        Discordにメッセージを送信する

        Parameters:
        -----------
        message : str
            送信するメッセージ
        title : str, optional
            メッセージのタイトル
        level : str, default="info"
            メッセージレベル ("debug", "info", "warning", "error")

        Returns:
        --------
        bool
            送信成功ならTrue、失敗ならFalse

        Examples:
        --------
        >>> notifier = DiscordNotifier(webhook_url)
        >>> notifier.send_message("デバッグ情報", level="debug")  # グレー
        >>> notifier.send_message("通常の情報", level="info")     # 緑
        >>> notifier.send_message("警告", level="warning")        # オレンジ
        >>> notifier.send_message("エラー", level="error")        # 赤
        """
        if not self.enabled:
            return True  # 無効の場合は成功扱い

        try:
            payload = {
                "content": message if not title else None,
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": self.COLORS.get(level, self.COLORS["info"]),
                    }
                ]
                if title
                else None,
            }

            response = requests.post(self.webhook_url, json=payload)

            if response.status_code == 204:
                return True
            else:
                self.logger.error(
                    f"Discord通知送信失敗 - ステータスコード: {response.status_code}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Discord通知送信エラー: {str(e)}")
            return False

    def print_and_notify(
        self, message: str, title: Optional[str] = None, level: str = "info"
    ) -> bool:
        """
        ログ出力とDiscord通知を同時に行う

        Parameters:
        -----------
        message : str
            送信するメッセージ
        title : str, optional
            メッセージのタイトル
        level : str, default="info"
            メッセージレベル ("debug", "info", "warning", "error")

        Returns:
        --------
        bool
            Discord送信成功（または無効時）ならTrue、失敗ならFalse
        """
        # ログレベルに応じてログ出力
        log_func = getattr(self.logger, level.lower())
        log_func(message)

        # Discord通知が有効な場合のみ送信
        if self.enabled:
            return self.send_message(message, title, level)
        return True

    def send_image(self, image_data: io.BytesIO, message: str = "") -> bool:
        """
        画像データをDiscordに送信する

        Parameters:
        -----------
        image_data : io.BytesIO
            送信する画像データ
        message : str, optional
            画像と一緒に送信するメッセージ

        Returns:
        --------
        bool
            送信成功ならTrue、失敗ならFalse
        """
        if not self.enabled:
            return True

        try:
            files = {"file": ("chart.png", image_data, "image/png")}
            payload = {"content": message}

            response = requests.post(self.webhook_url, data=payload, files=files)

            if response.status_code == 204:
                return True
            else:
                self.logger.error(
                    f"Discord画像送信失敗 - ステータスコード: {response.status_code}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Discord画像送信エラー: {str(e)}")
            return False
