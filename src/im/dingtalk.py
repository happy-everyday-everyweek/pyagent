"""
PyAgent IM平台适配器 - 钉钉适配器
"""

import hashlib
import hmac
import time
from typing import Any

import httpx

from .base import BaseIMAdapter, IMReply, IMUser


class DingTalkAdapter(BaseIMAdapter):
    """钉钉适配器"""

    platform = "dingtalk"

    def __init__(
        self,
        webhook_url: str = "",
        secret: str = "",
        config: dict[str, Any] | None = None
    ):
        super().__init__(config)
        self.webhook_url = webhook_url
        self.secret = secret

    async def connect(self) -> bool:
        """连接到钉钉"""
        self._connected = bool(self.webhook_url)
        return self._connected

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False

    def _sign_url(self) -> str:
        """生成签名URL"""
        if not self.secret:
            return self.webhook_url

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"

        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        sign = hmac_code.hex()

        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

    async def send_message(
        self,
        chat_id: str,
        reply: IMReply
    ) -> bool:
        """发送消息"""
        if not self._connected:
            return False

        try:
            url = self._sign_url()

            data = {
                "msgtype": "text",
                "text": {
                    "content": reply.content
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                result = response.json()

                return result.get("errcode") == 0

        except Exception as e:
            print(f"Failed to send DingTalk message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> IMUser | None:
        """获取用户信息"""
        return IMUser(user_id=user_id)

    async def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """获取聊天信息"""
        return {"chat_id": chat_id}

    async def send_markdown(
        self,
        chat_id: str,
        title: str,
        content: str
    ) -> bool:
        """发送Markdown消息"""
        if not self._connected:
            return False

        try:
            url = self._sign_url()

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": content
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                result = response.json()

                return result.get("errcode") == 0

        except Exception as e:
            print(f"Failed to send DingTalk markdown: {e}")
            return False
