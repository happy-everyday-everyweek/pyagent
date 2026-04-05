"""
PyAgent IM平台适配器 - 企业微信适配器
"""

import time
from typing import Any

import httpx

from .base import BaseIMAdapter, IMReply, IMUser


class WeComAdapter(BaseIMAdapter):
    """企业微信适配器"""

    platform = "wecom"

    def __init__(
        self,
        corp_id: str = "",
        agent_id: str = "",
        secret: str = "",
        config: dict[str, Any] | None = None
    ):
        super().__init__(config)
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self._access_token: str | None = None
        self._token_expires: float = 0

    async def connect(self) -> bool:
        """连接到企业微信"""
        if not self.corp_id or not self.secret:
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
                response = await client.get(
                    "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                    params={
                        "corpid": self.corp_id,
                        "corpsecret": self.secret
                    }
                )

                result = response.json()

                if result.get("errcode") == 0:
                    self._access_token = result.get("access_token")
                    self._token_expires = time.time() + result.get("expires_in", 7200) - 300
                    return self._access_token

        except Exception as e:
            print(f"Failed to get WeCom access token: {e}")

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
                    "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                    params={"access_token": token},
                    json={
                        "touser": chat_id,
                        "msgtype": "text",
                        "agentid": self.agent_id,
                        "text": {
                            "content": reply.content
                        }
                    }
                )

                result = response.json()
                return result.get("errcode") == 0

        except Exception as e:
            print(f"Failed to send WeCom message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> IMUser | None:
        """获取用户信息"""
        return IMUser(user_id=user_id)

    async def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """获取聊天信息"""
        return {"chat_id": chat_id}
