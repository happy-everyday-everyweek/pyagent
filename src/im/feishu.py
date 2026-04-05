"""
PyAgent IM平台适配器 - 飞书适配器
"""

import json
import time
from typing import Any

import httpx

from .base import BaseIMAdapter, IMReply, IMUser


class FeishuAdapter(BaseIMAdapter):
    """飞书适配器"""

    platform = "feishu"

    def __init__(
        self,
        app_id: str = "",
        app_secret: str = "",
        config: dict[str, Any] | None = None
    ):
        super().__init__(config)
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token: str | None = None
        self._token_expires: float = 0

    async def connect(self) -> bool:
        """连接到飞书"""
        if not self.app_id or not self.app_secret:
            return False

        token = await self._get_access_token()
        self._connected = bool(token)
        return self._connected

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False
        self._access_token = None

    async def _get_access_token(self) -> str | None:
        """获取访问令牌"""
        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret
                    }
                )

                result = response.json()

                if result.get("code") == 0:
                    self._access_token = result.get("tenant_access_token")
                    self._token_expires = time.time() + result.get("expire", 7200) - 300
                    return self._access_token

        except Exception as e:
            print(f"Failed to get Feishu access token: {e}")

        return None

    async def send_message(
        self,
        chat_id: str,
        reply: IMReply
    ) -> bool:
        """发送消息"""
        if not self._connected:
            return False

        token = await self._get_access_token()
        if not token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    params={"receive_id_type": "chat_id"},
                    json={
                        "receive_id": chat_id,
                        "msg_type": "text",
                        "content": json.dumps({"text": reply.content})
                    }
                )

                result = response.json()
                return result.get("code") == 0

        except Exception as e:
            print(f"Failed to send Feishu message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> IMUser | None:
        """获取用户信息"""
        return IMUser(user_id=user_id)

    async def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """获取聊天信息"""
        return {"chat_id": chat_id}
