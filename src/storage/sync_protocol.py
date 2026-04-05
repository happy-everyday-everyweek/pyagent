"""
PyAgent 同步协议 - 跨设备文件同步协议

实现跨设备的文件元数据广播、文件拉取请求和同步消息处理。
"""

import json
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class SyncMessageType(Enum):
    """同步消息类型"""
    FILE_METADATA_BROADCAST = "file_metadata_broadcast"
    FILE_PULL_REQUEST = "file_pull_request"
    FILE_PULL_RESPONSE = "file_pull_response"
    FILE_DELETE_NOTIFICATION = "file_delete_notification"
    FILE_UPDATE_NOTIFICATION = "file_update_notification"
    SYNC_STATUS_REQUEST = "sync_status_request"
    SYNC_STATUS_RESPONSE = "sync_status_response"
    DEVICE_HEARTBEAT = "device_heartbeat"
    CONFLICT_NOTIFICATION = "conflict_notification"


@dataclass
class SyncMessage:
    """同步消息"""
    message_id: str
    message_type: str
    sender_device_id: str
    target_device_id: str
    timestamp: str
    payload: dict[str, Any] = field(default_factory=dict)
    requires_ack: bool = False
    ack_received: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "sender_device_id": self.sender_device_id,
            "target_device_id": self.target_device_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "requires_ack": self.requires_ack,
            "ack_received": self.ack_received,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SyncMessage":
        return cls(
            message_id=data.get("message_id", ""),
            message_type=data.get("message_type", ""),
            sender_device_id=data.get("sender_device_id", ""),
            target_device_id=data.get("target_device_id", ""),
            timestamp=data.get("timestamp", ""),
            payload=data.get("payload", {}),
            requires_ack=data.get("requires_ack", False),
            ack_received=data.get("ack_received", False),
        )


@dataclass
class FilePullRequest:
    """文件拉取请求"""
    request_id: str
    file_id: str
    file_name: str
    checksum: str
    requester_device_id: str
    source_device_id: str
    timestamp: str
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "file_id": self.file_id,
            "file_name": self.file_name,
            "checksum": self.checksum,
            "requester_device_id": self.requester_device_id,
            "source_device_id": self.source_device_id,
            "timestamp": self.timestamp,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FilePullRequest":
        return cls(
            request_id=data.get("request_id", ""),
            file_id=data.get("file_id", ""),
            file_name=data.get("file_name", ""),
            checksum=data.get("checksum", ""),
            requester_device_id=data.get("requester_device_id", ""),
            source_device_id=data.get("source_device_id", ""),
            timestamp=data.get("timestamp", ""),
            priority=data.get("priority", 0),
        )


@dataclass
class FilePullResponse:
    """文件拉取响应"""
    request_id: str
    file_id: str
    success: bool
    file_data: bytes | None = None
    error_message: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "file_id": self.file_id,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }


class SyncProtocol:
    """同步协议处理器

    处理跨设备的文件同步消息。
    """

    def __init__(self, data_dir: str = "data/storage/sync"):
        self.data_dir = Path(data_dir)
        self.messages_dir = self.data_dir / "messages"
        self.pending_dir = self.data_dir / "pending"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        self.pending_dir.mkdir(parents=True, exist_ok=True)

        self._device_id = ""
        self._message_handlers: dict[str, Callable[[SyncMessage], None]] = {}
        self._pending_requests: dict[str, FilePullRequest] = {}
        self._lock = threading.Lock()

        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """注册默认消息处理器"""
        self._message_handlers[SyncMessageType.FILE_METADATA_BROADCAST.value] = self._handle_metadata_broadcast
        self._message_handlers[SyncMessageType.FILE_PULL_REQUEST.value] = self._handle_pull_request
        self._message_handlers[SyncMessageType.FILE_DELETE_NOTIFICATION.value] = self._handle_delete_notification
        self._message_handlers[SyncMessageType.DEVICE_HEARTBEAT.value] = self._handle_heartbeat

    def set_device_id(self, device_id: str) -> None:
        """设置设备ID"""
        self._device_id = device_id

    def _generate_message_id(self) -> str:
        """生成消息ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid4())[:8]
        return f"msg_{timestamp}_{random_suffix}"

    def _save_message(self, message: SyncMessage) -> None:
        """保存消息"""
        message_file = self.messages_dir / f"{message.message_id}.json"
        try:
            with open(message_file, "w", encoding="utf-8") as f:
                json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    def broadcast_file_metadata(self, file_info: dict[str, Any], target_devices: list[str] | None = None) -> list[str]:
        """广播文件元数据到域内设备

        Args:
            file_info: 文件元数据信息
            target_devices: 目标设备列表，None表示广播到所有设备

        Returns:
            list[str]: 消息ID列表
        """
        if target_devices is None:
            target_devices = ["*"]

        message_ids: list[str] = []
        timestamp = datetime.now().isoformat()

        for target_device in target_devices:
            message = SyncMessage(
                message_id=self._generate_message_id(),
                message_type=SyncMessageType.FILE_METADATA_BROADCAST.value,
                sender_device_id=self._device_id,
                target_device_id=target_device,
                timestamp=timestamp,
                payload={"file_info": file_info},
                requires_ack=True,
            )

            self._save_message(message)
            message_ids.append(message.message_id)

            logger.info(f"Broadcasting file metadata: {file_info.get('file_id')} to {target_device}")

        return message_ids

    def request_file_pull(self, file_id: str, from_device: str, file_name: str = "", checksum: str = "") -> str:
        """请求从远程设备拉取文件

        Args:
            file_id: 文件ID
            from_device: 源设备ID
            file_name: 文件名
            checksum: 文件校验和

        Returns:
            str: 请求ID
        """
        request_id = str(uuid4())
        timestamp = datetime.now().isoformat()

        request = FilePullRequest(
            request_id=request_id,
            file_id=file_id,
            file_name=file_name,
            checksum=checksum,
            requester_device_id=self._device_id,
            source_device_id=from_device,
            timestamp=timestamp,
        )

        message = SyncMessage(
            message_id=self._generate_message_id(),
            message_type=SyncMessageType.FILE_PULL_REQUEST.value,
            sender_device_id=self._device_id,
            target_device_id=from_device,
            timestamp=timestamp,
            payload={"request": request.to_dict()},
            requires_ack=True,
        )

        self._save_message(message)
        self._pending_requests[request_id] = request

        request_file = self.pending_dir / f"{request_id}.json"
        try:
            with open(request_file, "w", encoding="utf-8") as f:
                json.dump(request.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save pending request: {e}")

        logger.info(f"File pull request sent: {file_id} from {from_device}")

        return request_id

    def handle_sync_message(self, message: SyncMessage) -> None:
        """处理同步消息

        Args:
            message: 同步消息
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error handling message {message.message_id}: {e}")
        else:
            logger.warning(f"No handler for message type: {message.message_type}")

    def register_message_handler(self, message_type: SyncMessageType, handler: Callable[[SyncMessage], None]) -> None:
        """注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self._message_handlers[message_type.value] = handler

    def _handle_metadata_broadcast(self, message: SyncMessage) -> None:
        """处理元数据广播消息"""
        file_info = message.payload.get("file_info", {})
        logger.info(f"Received file metadata broadcast: {file_info.get('file_id')} from {message.sender_device_id}")

    def _handle_pull_request(self, message: SyncMessage) -> None:
        """处理文件拉取请求"""
        request_data = message.payload.get("request", {})
        request = FilePullRequest.from_dict(request_data)

        logger.info(f"Received file pull request: {request.file_id} from {request.requester_device_id}")

        response = FilePullResponse(
            request_id=request.request_id,
            file_id=request.file_id,
            success=False,
            error_message="File not found or not available",
            timestamp=datetime.now().isoformat(),
        )

        response_message = SyncMessage(
            message_id=self._generate_message_id(),
            message_type=SyncMessageType.FILE_PULL_RESPONSE.value,
            sender_device_id=self._device_id,
            target_device_id=request.requester_device_id,
            timestamp=datetime.now().isoformat(),
            payload={"response": response.to_dict()},
        )

        self._save_message(response_message)

    def _handle_delete_notification(self, message: SyncMessage) -> None:
        """处理文件删除通知"""
        file_id = message.payload.get("file_id", "")
        logger.info(f"Received file delete notification: {file_id} from {message.sender_device_id}")

    def _handle_heartbeat(self, message: SyncMessage) -> None:
        """处理设备心跳消息"""
        logger.debug(f"Received heartbeat from {message.sender_device_id}")

    def notify_file_delete(self, file_id: str, target_devices: list[str] | None = None) -> list[str]:
        """通知文件删除

        Args:
            file_id: 文件ID
            target_devices: 目标设备列表

        Returns:
            list[str]: 消息ID列表
        """
        if target_devices is None:
            target_devices = ["*"]

        message_ids: list[str] = []
        timestamp = datetime.now().isoformat()

        for target_device in target_devices:
            message = SyncMessage(
                message_id=self._generate_message_id(),
                message_type=SyncMessageType.FILE_DELETE_NOTIFICATION.value,
                sender_device_id=self._device_id,
                target_device_id=target_device,
                timestamp=timestamp,
                payload={"file_id": file_id},
                requires_ack=True,
            )

            self._save_message(message)
            message_ids.append(message.message_id)

        logger.info(f"Sent file delete notification: {file_id}")

        return message_ids

    def notify_file_update(self, file_info: dict[str, Any], target_devices: list[str] | None = None) -> list[str]:
        """通知文件更新

        Args:
            file_info: 文件信息
            target_devices: 目标设备列表

        Returns:
            list[str]: 消息ID列表
        """
        if target_devices is None:
            target_devices = ["*"]

        message_ids: list[str] = []
        timestamp = datetime.now().isoformat()

        for target_device in target_devices:
            message = SyncMessage(
                message_id=self._generate_message_id(),
                message_type=SyncMessageType.FILE_UPDATE_NOTIFICATION.value,
                sender_device_id=self._device_id,
                target_device_id=target_device,
                timestamp=timestamp,
                payload={"file_info": file_info},
                requires_ack=True,
            )

            self._save_message(message)
            message_ids.append(message.message_id)

        return message_ids

    def send_heartbeat(self, target_devices: list[str] | None = None) -> list[str]:
        """发送心跳消息

        Args:
            target_devices: 目标设备列表

        Returns:
            list[str]: 消息ID列表
        """
        if target_devices is None:
            target_devices = ["*"]

        message_ids: list[str] = []
        timestamp = datetime.now().isoformat()

        for target_device in target_devices:
            message = SyncMessage(
                message_id=self._generate_message_id(),
                message_type=SyncMessageType.DEVICE_HEARTBEAT.value,
                sender_device_id=self._device_id,
                target_device_id=target_device,
                timestamp=timestamp,
                payload={"status": "active"},
            )

            self._save_message(message)
            message_ids.append(message.message_id)

        return message_ids

    def get_pending_requests(self) -> list[FilePullRequest]:
        """获取待处理的拉取请求

        Returns:
            list[FilePullRequest]: 待处理请求列表
        """
        return list(self._pending_requests.values())

    def remove_pending_request(self, request_id: str) -> bool:
        """移除待处理请求

        Args:
            request_id: 请求ID

        Returns:
            bool: 是否成功移除
        """
        if request_id in self._pending_requests:
            del self._pending_requests[request_id]

            request_file = self.pending_dir / f"{request_id}.json"
            if request_file.exists():
                try:
                    request_file.unlink()
                except Exception:
                    pass

            return True
        return False

    def get_sync_stats(self) -> dict[str, Any]:
        """获取同步统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        return {
            "device_id": self._device_id,
            "pending_requests": len(self._pending_requests),
            "message_handlers": len(self._message_handlers),
        }
