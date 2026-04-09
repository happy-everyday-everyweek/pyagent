"""
PyAgent IM平台适配器 - Kimi适配器
"""

import asyncio
from typing import Any

import httpx

from .base import BaseIMAdapter, ChatType, IMMessage, IMReply, IMUser, MessageType


class KimiAdapter(BaseIMAdapter):
    """Kimi适配器"""

    platform = "kimi"

    def __init__(
        self,
        bot_token: str = "",
        api_base: str = "https://api.kimi.com",
        timeout: int = 30,
        webhook_enabled: bool = False,
        webhook_port: int = 8080,
        webhook_path: str = "/kimi/webhook",
        config: dict[str, Any] | None = None
    ):
        super().__init__(config)
        self.bot_token = bot_token
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.webhook_enabled = webhook_enabled
        self.webhook_port = webhook_port
        self.webhook_path = webhook_path
        self._poll_task: asyncio.Task | None = None
        self._last_update_id: int = 0

    async def connect(self) -> bool:
        """连接到Kimi"""
        if not self.bot_token:
            print("Kimi bot token not configured")
            return False

        try:
            user = await self._get_me()
            if user:
                self._connected = True
                print(f"Connected to Kimi as: {user.name}")

                if not self.webhook_enabled:
                    self._poll_task = asyncio.create_task(self._poll_loop())

                return True
            return False

        except Exception as e:
            print(f"Failed to connect to Kimi: {e}")
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        self._connected = False
        print("Disconnected from Kimi")

    async def _get_me(self) -> IMUser | None:
        """获取机器人信息"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base}/v1/me",
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    data = response.json()
                    return IMUser(
                        user_id=str(data.get("id", "")),
                        name=data.get("name", ""),
                        nickname=data.get("name", ""),
                        is_bot=True
                    )

        except Exception as e:
            print(f"Failed to get Kimi bot info: {e}")

        return None

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }

    async def _poll_loop(self) -> None:
        """长轮询接收消息"""
        while self._connected:
            try:
                async with httpx.AsyncClient(timeout=self.timeout + 10) as client:
                    response = await client.get(
                        f"{self.api_base}/v1/updates",
                        headers=self._get_headers(),
                        params={
                            "offset": self._last_update_id + 1,
                            "timeout": self.timeout
                        }
                    )

                    if response.status_code == 200:
                        updates = response.json()
                        for update in updates:
                            self._last_update_id = update.get("update_id", 0)
                            message = self._parse_update(update)
                            if message:
                                await self._dispatch_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Kimi poll error: {e}")
                await asyncio.sleep(5)

    def _parse_update(self, update: dict[str, Any]) -> IMMessage | None:
        """解析更新"""
        try:
            message_data = update.get("message")
            if not message_data:
                return None

            chat_data = message_data.get("chat", {})
            sender_data = message_data.get("from", {})

            chat_type = ChatType.PRIVATE
            if chat_data.get("type") == "group":
                chat_type = ChatType.GROUP

            content = ""
            message_type = MessageType.TEXT

            if "text" in message_data:
                content = message_data["text"]
            elif "image" in message_data:
                content = message_data.get("image", {}).get("url", "")
                message_type = MessageType.IMAGE

            at_users = []
            is_at_bot = False

            entities = message_data.get("entities", [])
            for entity in entities:
                if entity.get("type") == "mention":
                    user_id = str(entity.get("user_id", ""))
                    if user_id:
                        at_users.append(user_id)

            return IMMessage(
                message_id=str(message_data.get("message_id", "")),
                platform=self.platform,
                chat_id=str(chat_data.get("id", "")),
                chat_type=chat_type,
                sender=IMUser(
                    user_id=str(sender_data.get("id", "")),
                    name=sender_data.get("name", ""),
                    nickname=sender_data.get("nickname", "")
                ),
                content=content,
                message_type=message_type,
                timestamp=message_data.get("timestamp", 0),
                at_users=at_users,
                is_at_bot=is_at_bot,
                extra={"raw_message": message_data}
            )

        except Exception as e:
            print(f"Failed to parse Kimi update: {e}")
            return None

    async def send_message(
        self,
        chat_id: str,
        reply: IMReply
    ) -> bool:
        """发送消息"""
        if not self._connected:
            return False

        try:
            data: dict[str, Any] = {
                "chat_id": chat_id,
                "parse_mode": "text"
            }

            if reply.message_type == MessageType.IMAGE:
                data["image"] = reply.content
            else:
                data["text"] = reply.content

            if reply.reply_to:
                data["reply_to_message_id"] = reply.reply_to

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/v1/sendMessage",
                    headers=self._get_headers(),
                    json=data
                )

                if response.status_code == 200:
                    return True
                print(f"Failed to send Kimi message: {response.status_code}")
                return False

        except Exception as e:
            print(f"Failed to send Kimi message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> IMUser | None:
        """获取用户信息"""
        if not self._connected:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base}/v1/users/{user_id}",
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    data = response.json()
                    return IMUser(
                        user_id=str(data.get("id", "")),
                        name=data.get("name", ""),
                        nickname=data.get("nickname", ""),
                        avatar=data.get("avatar", "")
                    )

        except Exception as e:
            print(f"Failed to get Kimi user info: {e}")

        return IMUser(user_id=user_id)

    async def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """获取聊天信息"""
        if not self._connected:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base}/v1/chats/{chat_id}",
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            print(f"Failed to get Kimi chat info: {e}")

        return {"chat_id": chat_id}

    async def handle_webhook(self, data: dict[str, Any]) -> bool:
        """处理Webhook请求"""
        if not self.webhook_enabled:
            return False

        try:
            message = self._parse_update(data)
            if message:
                await self._dispatch_message(message)
                return True
        except Exception as e:
            print(f"Failed to handle Kimi webhook: {e}")

        return False
