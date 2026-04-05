"""
PyAgent IM平台适配器 - OneBot适配器

支持微信和QQ（通过OneBot协议）。
"""

import asyncio
import json
from typing import Any

import websockets

from .base import BaseIMAdapter, ChatType, IMMessage, IMReply, IMUser, MessageType


class OneBotAdapter(BaseIMAdapter):
    """OneBot协议适配器（支持微信/QQ）"""

    platform = "onebot"

    def __init__(
        self,
        ws_url: str = "",
        access_token: str = "",
        platform_name: str = "qq",
        config: dict[str, Any] | None = None
    ):
        super().__init__(config)
        self.ws_url = ws_url
        self.access_token = access_token
        self.platform_name = platform_name
        self._ws: Any | None = None
        self._receive_task: asyncio.Task | None = None

    async def connect(self) -> bool:
        """连接到OneBot服务器"""
        if not self.ws_url:
            print("OneBot WebSocket URL not configured")
            return False

        try:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            self._ws = await websockets.connect(
                self.ws_url,
                extra_headers=headers
            )

            self._connected = True
            self._receive_task = asyncio.create_task(self._receive_loop())

            print(f"Connected to OneBot server: {self.ws_url}")
            return True

        except Exception as e:
            print(f"Failed to connect to OneBot server: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()
            self._ws = None

        self._connected = False
        print("Disconnected from OneBot server")

    async def _receive_loop(self) -> None:
        """接收消息循环"""
        while self._connected and self._ws:
            try:
                data = await self._ws.recv()
                event = json.loads(data)

                if event.get("post_type") == "message":
                    message = self._parse_message(event)
                    if message:
                        await self._dispatch_message(message)

            except websockets.ConnectionClosed:
                self._connected = False
                print("OneBot connection closed")
                break
            except Exception as e:
                print(f"OneBot receive error: {e}")

    def _parse_message(self, event: dict[str, Any]) -> IMMessage | None:
        """解析OneBot消息"""
        try:
            message_type = event.get("message_type", "")

            if message_type == "private":
                chat_type = ChatType.PRIVATE
                chat_id = str(event.get("user_id", ""))
            elif message_type == "group":
                chat_type = ChatType.GROUP
                chat_id = str(event.get("group_id", ""))
            else:
                return None

            user_id = str(event.get("user_id", ""))
            sender = event.get("sender", {})

            content_parts = []
            at_users = []
            is_at_bot = False

            for seg in event.get("message", []):
                seg_type = seg.get("type", "")

                if seg_type == "text":
                    content_parts.append(seg.get("data", {}).get("text", ""))
                elif seg_type == "at":
                    qq = seg.get("data", {}).get("qq", "")
                    if qq:
                        at_users.append(qq)
                        if qq == str(event.get("self_id", "")):
                            is_at_bot = True

            content = "".join(content_parts)

            return IMMessage(
                message_id=str(event.get("message_id", "")),
                platform=self.platform_name,
                chat_id=chat_id,
                chat_type=chat_type,
                sender=IMUser(
                    user_id=user_id,
                    name=sender.get("nickname", ""),
                    nickname=sender.get("card", "") or sender.get("nickname", "")
                ),
                content=content,
                message_type=MessageType.TEXT,
                timestamp=event.get("time", 0),
                at_users=at_users,
                is_at_bot=is_at_bot
            )

        except Exception as e:
            print(f"Failed to parse OneBot message: {e}")
            return None

    async def send_message(
        self,
        chat_id: str,
        reply: IMReply
    ) -> bool:
        """发送消息"""
        if not self._ws or not self._connected:
            return False

        try:
            if reply.reply_to:
                params = {
                    "message": [
                        {"type": "reply", "data": {"id": reply.reply_to}},
                        {"type": "text", "data": {"text": reply.content}}
                    ]
                }
            else:
                params = {
                    "message": [{"type": "text", "data": {"text": reply.content}}]
                }

            action = "send_private_msg"
            params["user_id"] = int(chat_id)

            request = {
                "action": action,
                "params": params
            }

            await self._ws.send(json.dumps(request))
            return True

        except Exception as e:
            print(f"Failed to send OneBot message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> IMUser | None:
        """获取用户信息"""
        return IMUser(user_id=user_id)

    async def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """获取聊天信息"""
        return {"chat_id": chat_id}
