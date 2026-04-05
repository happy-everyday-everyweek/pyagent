"""
PyAgent 移动端模块 - SMS工具

提供移动设备的短信读取和发送功能。
v0.8.0: 新增移动端支持
"""

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.tools.base import ToolContext, ToolResult, ToolState, UnifiedTool


class MessageType(Enum):
    """消息类型"""
    INBOX = "inbox"
    SENT = "sent"
    DRAFT = "draft"
    OUTBOX = "outbox"


class MessageStatus(Enum):
    """消息状态"""
    RECEIVED = "received"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class SMSMessage:
    """短信消息"""
    id: str
    thread_id: str
    address: str
    body: str
    timestamp: datetime
    type: MessageType = MessageType.INBOX
    status: MessageStatus = MessageStatus.RECEIVED
    read: bool = False
    person: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "address": self.address,
            "body": self.body,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type.value,
            "status": self.status.value,
            "read": self.read,
            "person": self.person,
        }


@dataclass
class SMSFilter:
    """短信过滤器"""
    address: str | None = None
    type: MessageType | None = None
    unread_only: bool = False
    since: datetime | None = None
    limit: int = 100

    def matches(self, message: SMSMessage) -> bool:
        """检查消息是否匹配过滤器"""
        if self.address and self.address not in message.address:
            return False

        if self.type and message.type != self.type:
            return False

        if self.unread_only and message.read:
            return False

        if self.since and message.timestamp < self.since:
            return False

        return True


class SMSTools(UnifiedTool):
    """短信工具

    提供移动设备的短信读取和发送功能。
    """

    name = "sms_tools"
    description = "短信工具，提供短信读取和发送功能"

    def __init__(self, device_id: str = "", adb_path: str = "adb"):
        super().__init__(device_id)
        self._adb_path = adb_path
        self._messages: list[SMSMessage] = []
        self._logger = logging.getLogger(__name__)

    async def activate(self, context: ToolContext) -> bool:
        """激活工具"""
        try:
            if not await self._check_sms_permission():
                self._logger.warning("SMS permission may not be granted")

            self._state = ToolState.ACTIVE
            return True

        except Exception as e:
            self._logger.error(f"Failed to activate SMS tools: {e}")
            self._state = ToolState.ERROR
            return False

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """执行工具"""
        action = kwargs.get("action", "")

        action_map = {
            "get_messages": lambda: self.get_messages(
                kwargs.get("filter"),
                kwargs.get("limit", 100)
            ),
            "send_message": lambda: self.send_message(
                kwargs.get("to", ""),
                kwargs.get("body", "")
            ),
            "get_unread": self.get_unread_messages,
            "mark_read": lambda: self.mark_as_read(kwargs.get("message_id", "")),
            "delete_message": lambda: self.delete_message(kwargs.get("message_id", "")),
        }

        if action not in action_map:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}"
            )

        return await action_map[action]()

    async def dormant(self, context: ToolContext) -> bool:
        """休眠工具"""
        self._messages = []
        self._state = ToolState.DORMANT
        return True

    async def _check_sms_permission(self) -> bool:
        """检查短信权限"""
        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    "pm list permissions | grep android.permission.READ_SMS"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            return "android.permission.READ_SMS" in result.stdout

        except Exception:
            return False

    async def get_messages(
        self,
        filter_obj: SMSFilter | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """获取短信消息

        Args:
            filter_obj: 短信过滤器
            limit: 最大返回数量

        Returns:
            短信消息列表
        """
        if self._state != ToolState.ACTIVE:
            return []

        try:
            raw_messages = await self._fetch_messages(limit * 2)

            messages = []
            for raw in raw_messages:
                message = self._parse_message(raw)

                if message:
                    if filter_obj is None or filter_obj.matches(message):
                        messages.append(message)

                        if len(messages) >= limit:
                            break

            self._messages = messages
            return [m.to_dict() for m in messages]

        except Exception as e:
            self._logger.error(f"Failed to get messages: {e}")
            return []

    async def _fetch_messages(self, limit: int = 200) -> list[dict[str, Any]]:
        """从设备获取短信数据"""
        try:
            query = (
                "content://sms/"
            )

            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    f"content query --uri {query} "
                    f"--projection _id:thread_id:address:body:date:type:read:status "
                    f"--limit {limit}"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self._logger.warning(f"Failed to fetch messages: {result.stderr}")
                return []

            return self._parse_content_query(result.stdout)

        except Exception as e:
            self._logger.error(f"Error fetching messages: {e}")
            return []

    def _parse_content_query(self, output: str) -> list[dict[str, Any]]:
        """解析content query输出"""
        messages = []

        for line in output.splitlines():
            if not line.strip():
                continue

            message = {}
            parts = line.split(", ")

            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    message[key.strip()] = value.strip()

            if message:
                messages.append(message)

        return messages

    def _parse_message(self, raw: dict[str, Any]) -> SMSMessage | None:
        """解析单个短信消息"""
        try:
            message_id = raw.get("_id", "")
            if not message_id:
                return None

            thread_id = raw.get("thread_id", "")
            address = raw.get("address", "")
            body = raw.get("body", "")

            timestamp_ms = int(raw.get("date", "0"))
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)

            msg_type = int(raw.get("type", "1"))
            message_type = MessageType.INBOX
            if msg_type == 1:
                message_type = MessageType.INBOX
            elif msg_type == 2:
                message_type = MessageType.SENT
            elif msg_type == 3:
                message_type = MessageType.DRAFT
            elif msg_type == 4:
                message_type = MessageType.OUTBOX

            read = raw.get("read", "0") == "1"

            status_code = int(raw.get("status", "-1"))
            message_status = MessageStatus.RECEIVED
            if message_type == MessageType.SENT:
                if status_code == 0:
                    message_status = MessageStatus.DELIVERED
                elif status_code == 64:
                    message_status = MessageStatus.PENDING
                elif status_code == 128:
                    message_status = MessageStatus.FAILED
                else:
                    message_status = MessageStatus.SENT

            return SMSMessage(
                id=message_id,
                thread_id=thread_id,
                address=address,
                body=body,
                timestamp=timestamp,
                type=message_type,
                status=message_status,
                read=read,
            )

        except Exception as e:
            self._logger.error(f"Error parsing message: {e}")
            return None

    async def send_message(self, to: str, body: str) -> ToolResult:
        """发送短信

        Args:
            to: 接收方号码
            body: 短信内容

        Returns:
            发送结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        if not to or not body:
            return ToolResult(
                success=False,
                error="Missing required parameters: to or body"
            )

        try:
            escaped_body = body.replace("'", "\\'").replace('"', '\\"')

            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    f"am start -a android.intent.action.SENDTO "
                    f"-d sms:{to} "
                    f"--es sms_body '{escaped_body}' "
                    f"--ez exit_on_sent true"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to send message: {result.stderr}"
                )

            await self._simulate_send_click()

            return ToolResult(
                success=True,
                output=f"Message sent to {to}",
                data={
                    "to": to,
                    "body": body,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            self._logger.error(f"Failed to send message: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to send message: {str(e)}"
            )

    async def _simulate_send_click(self) -> bool:
        """模拟点击发送按钮"""
        try:
            await asyncio.sleep(1)

            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    "input keyevent KEYCODE_ENTER"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            return result.returncode == 0

        except Exception:
            return False

    async def get_unread_messages(self) -> list[dict[str, Any]]:
        """获取未读短信"""
        filter_obj = SMSFilter(unread_only=True)
        return await self.get_messages(filter_obj)

    async def mark_as_read(self, message_id: str) -> ToolResult:
        """标记短信为已读

        Args:
            message_id: 消息ID

        Returns:
            操作结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    f"content call --uri content://sms/{message_id} "
                    f"--method markAsRead"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to mark as read: {result.stderr}"
                )

            return ToolResult(
                success=True,
                output=f"Message {message_id} marked as read"
            )

        except Exception as e:
            self._logger.error(f"Failed to mark as read: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to mark as read: {str(e)}"
            )

    async def delete_message(self, message_id: str) -> ToolResult:
        """删除短信

        Args:
            message_id: 消息ID

        Returns:
            操作结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    f"content delete --uri content://sms/{message_id}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to delete message: {result.stderr}"
                )

            return ToolResult(
                success=True,
                output=f"Message {message_id} deleted"
            )

        except Exception as e:
            self._logger.error(f"Failed to delete message: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to delete message: {str(e)}"
            )

    async def get_conversation(self, thread_id: str) -> list[dict[str, Any]]:
        """获取对话线程中的所有消息

        Args:
            thread_id: 线程ID

        Returns:
            消息列表
        """
        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    f"content query --uri content://sms/ "
                    f"--projection _id:thread_id:address:body:date:type:read:status "
                    f"--where \"thread_id={thread_id}\""
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return []

            messages = []
            raw_messages = self._parse_content_query(result.stdout)

            for raw in raw_messages:
                message = self._parse_message(raw)
                if message:
                    messages.append(message.to_dict())

            messages.sort(key=lambda x: x["timestamp"])
            return messages

        except Exception as e:
            self._logger.error(f"Failed to get conversation: {e}")
            return []

    async def search_messages(self, query: str) -> list[dict[str, Any]]:
        """搜索短信

        Args:
            query: 搜索关键词

        Returns:
            匹配的消息列表
        """
        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    f"content query --uri content://sms/ "
                    f"--projection _id:thread_id:address:body:date:type:read:status "
                    f"--where \"body LIKE '%{query}%'\""
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return []

            messages = []
            raw_messages = self._parse_content_query(result.stdout)

            for raw in raw_messages:
                message = self._parse_message(raw)
                if message:
                    messages.append(message.to_dict())

            return messages

        except Exception as e:
            self._logger.error(f"Failed to search messages: {e}")
            return []

    async def get_message_count(self) -> dict[str, int]:
        """获取短信统计"""
        try:
            inbox = await self.get_messages(SMSFilter(type=MessageType.INBOX), 10000)
            sent = await self.get_messages(SMSFilter(type=MessageType.SENT), 10000)
            unread = await self.get_unread_messages()

            return {
                "total": len(inbox) + len(sent),
                "inbox": len(inbox),
                "sent": len(sent),
                "unread": len(unread),
            }

        except Exception as e:
            self._logger.error(f"Failed to get message count: {e}")
            return {
                "total": 0,
                "inbox": 0,
                "sent": 0,
                "unread": 0,
            }


import asyncio
