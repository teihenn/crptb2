from typing import Optional

import requests

from src.utils.logger import Logger


class DiscordNotifier:
    """
    Discord通知を送信するクラス
    """

    def __init__(self, webhook_url: str):
        """
        Parameters:
        -----------
        webhook_url : str
            DiscordのWebhook URL
        """
        self.webhook_url = webhook_url
        self.logger = Logger.get_logger()

    def send_message(self, message: str, title: Optional[str] = None) -> bool:
        """
        Discordにメッセージを送信する

        Parameters:
        -----------
        message : str
            送信するメッセージ
        title : str, optional
            メッセージのタイトル

        Returns:
        --------
        bool
            送信成功ならTrue、失敗ならFalse
        """
        try:
            payload = {
                "content": message if not title else None,
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": 0x00FF00,  # 緑色
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
            ログレベル ("debug", "info", "warning", "error", "critical")

        Returns:
        --------
        bool
            Discord送信成功ならTrue、失敗ならFalse
        """
        # ログレベルに応じてログ出力
        log_func = getattr(self.logger, level.lower())
        log_func(message)

        # Discordに送信
        return self.send_message(message, title)
