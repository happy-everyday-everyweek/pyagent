"""
PyAgent 分布式存储 - 智能同步管理器

实现智能同步模式选择、冲突解决、设备能力感知等功能。
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SyncMode(str, Enum):
    """同步模式"""
    REALTIME = "realtime"
    INCREMENTAL = "incremental"
    MANUAL = "manual"
    OFFLINE = "offline"


class NetworkQuality(str, Enum):
    """网络质量"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    OFFLINE = "offline"


@dataclass
class DeviceCapability:
    """设备能力"""
    device_id: str
    cpu_cores: int = 4
    memory_gb: float = 8.0
    storage_gb: float = 100.0
    has_gpu: bool = False
    network_speed_mbps: float = 100.0
    is_mobile: bool = False
    battery_level: float | None = None
    last_updated: float = field(default_factory=time.time)

    def compute_score(self) -> float:
        """计算设备能力得分"""
        score = 0.0
        score += self.cpu_cores * 10
        score += self.memory_gb * 5
        score += min(self.storage_gb / 10, 10)
        if self.has_gpu:
            score += 20
        score += min(self.network_speed_mbps / 10, 10)
        if self.is_mobile and self.battery_level is not None:
            score *= (self.battery_level / 100)
        return score

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "storage_gb": self.storage_gb,
            "has_gpu": self.has_gpu,
            "network_speed_mbps": self.network_speed_mbps,
            "is_mobile": self.is_mobile,
            "battery_level": self.battery_level,
            "last_updated": self.last_updated,
            "score": self.compute_score()
        }


@dataclass
class SyncTask:
    """同步任务"""
    task_id: str
    file_id: str
    source_device: str
    target_devices: list[str]
    priority: int = 1
    created_at: float = field(default_factory=time.time)
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ConflictInfo:
    """冲突信息"""
    file_id: str
    local_version: dict[str, Any]
    remote_version: dict[str, Any]
    local_device: str
    remote_device: str
    detected_at: float = field(default_factory=time.time)


class SmartSyncManager:
    """智能同步管理器"""

    NETWORK_QUALITY_THRESHOLDS = {
        NetworkQuality.EXCELLENT: 50,
        NetworkQuality.GOOD: 20,
        NetworkQuality.FAIR: 5,
        NetworkQuality.POOR: 1,
    }

    def __init__(
        self,
        data_dir: str = "data/storage/sync",
        sync_interval: int = 60
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.sync_interval = sync_interval
        self._current_mode = SyncMode.INCREMENTAL
        self._network_quality = NetworkQuality.GOOD
        self._device_capabilities: dict[str, DeviceCapability] = {}
        self._sync_queue: list[SyncTask] = []
        self._conflict_queue: list[ConflictInfo] = []
        self._offline_cache: list[dict[str, Any]] = []
        self._is_online = True
        self._last_sync: float = 0
        self._sync_handlers: dict[str, Callable] = {}
        self._running = False

    def register_sync_handler(self, event: str, handler: Callable) -> None:
        """注册同步事件处理器"""
        self._sync_handlers[event] = handler

    async def start(self) -> None:
        """启动同步管理器"""
        self._running = True
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._network_monitor_loop())
        logger.info("Smart sync manager started")

    async def stop(self) -> None:
        """停止同步管理器"""
        self._running = False
        logger.info("Smart sync manager stopped")

    async def _sync_loop(self) -> None:
        """同步循环"""
        while self._running:
            try:
                await self._process_sync_queue()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(5)

    async def _network_monitor_loop(self) -> None:
        """网络监控循环"""
        while self._running:
            try:
                quality = await self._detect_network_quality()
                if quality != self._network_quality:
                    self._network_quality = quality
                    await self._adjust_sync_mode()
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Network monitor error: {e}")
                await asyncio.sleep(10)

    async def _detect_network_quality(self) -> NetworkQuality:
        """检测网络质量"""
        try:
            start_time = time.time()
            latency = (time.time() - start_time) * 1000

            if not self._is_online:
                return NetworkQuality.OFFLINE

            if latency < 50:
                return NetworkQuality.EXCELLENT
            if latency < 100:
                return NetworkQuality.GOOD
            if latency < 300:
                return NetworkQuality.FAIR
            return NetworkQuality.POOR
        except Exception:
            return NetworkQuality.OFFLINE

    async def _adjust_sync_mode(self) -> None:
        """调整同步模式"""
        old_mode = self._current_mode

        if self._network_quality == NetworkQuality.OFFLINE:
            self._current_mode = SyncMode.OFFLINE
        elif self._network_quality in (NetworkQuality.EXCELLENT, NetworkQuality.GOOD):
            self._current_mode = SyncMode.REALTIME
        elif self._network_quality == NetworkQuality.FAIR:
            self._current_mode = SyncMode.INCREMENTAL
        else:
            self._current_mode = SyncMode.MANUAL

        if old_mode != self._current_mode:
            logger.info(f"Sync mode changed: {old_mode.value} -> {self._current_mode.value}")
            if "mode_changed" in self._sync_handlers:
                await self._sync_handlers["mode_changed"](old_mode, self._current_mode)

    async def _process_sync_queue(self) -> None:
        """处理同步队列"""
        if not self._sync_queue:
            return

        if self._current_mode == SyncMode.OFFLINE:
            return

        self._sync_queue.sort(key=lambda t: t.priority, reverse=True)

        batch_size = self._get_batch_size()
        batch = self._sync_queue[:batch_size]
        self._sync_queue = self._sync_queue[batch_size:]

        for task in batch:
            try:
                await self._execute_sync_task(task)
            except Exception as e:
                logger.error(f"Sync task failed: {task.task_id}, error: {e}")
                task.retry_count += 1
                if task.retry_count < task.max_retries:
                    task.status = "pending"
                    self._sync_queue.append(task)

    def _get_batch_size(self) -> int:
        """获取批处理大小"""
        if self._current_mode == SyncMode.REALTIME:
            return 10
        if self._current_mode == SyncMode.INCREMENTAL:
            return 5
        return 1

    async def _execute_sync_task(self, task: SyncTask) -> None:
        """执行同步任务"""
        task.status = "syncing"

        if "sync_file" in self._sync_handlers:
            await self._sync_handlers["sync_file"](task)

        task.status = "completed"
        self._last_sync = time.time()

        logger.info(f"Sync task completed: {task.task_id}")

    def add_sync_task(
        self,
        file_id: str,
        source_device: str,
        target_devices: list[str],
        priority: int = 1
    ) -> str:
        """添加同步任务"""
        import uuid
        task_id = f"sync_{uuid.uuid4().hex[:8]}"

        task = SyncTask(
            task_id=task_id,
            file_id=file_id,
            source_device=source_device,
            target_devices=target_devices,
            priority=priority
        )

        if self._current_mode == SyncMode.OFFLINE:
            self._offline_cache.append({
                "type": "sync",
                "task": task.to_dict() if hasattr(task, "to_dict") else {
                    "task_id": task.task_id,
                    "file_id": task.file_id,
                    "source_device": task.source_device,
                    "target_devices": task.target_devices,
                    "priority": task.priority
                }
            })
            logger.info(f"Sync task cached for offline: {task_id}")
        else:
            self._sync_queue.append(task)
            logger.info(f"Sync task added: {task_id}")

        return task_id

    def detect_conflict(
        self,
        file_id: str,
        local_version: dict[str, Any],
        remote_version: dict[str, Any],
        local_device: str,
        remote_device: str
    ) -> ConflictInfo | None:
        """检测冲突"""
        local_time = local_version.get("modified_at", 0)
        remote_time = remote_version.get("modified_at", 0)

        time_diff = abs(local_time - remote_time)

        if time_diff < 5:
            local_checksum = local_version.get("checksum", "")
            remote_checksum = remote_version.get("checksum", "")

            if local_checksum != remote_checksum:
                conflict = ConflictInfo(
                    file_id=file_id,
                    local_version=local_version,
                    remote_version=remote_version,
                    local_device=local_device,
                    remote_device=remote_device
                )
                self._conflict_queue.append(conflict)
                logger.warning(f"Conflict detected: {file_id}")
                return conflict

        return None

    async def resolve_conflict(
        self,
        conflict: ConflictInfo,
        strategy: str = "last_write_wins"
    ) -> dict[str, Any]:
        """解决冲突"""
        if strategy == "last_write_wins":
            local_time = conflict.local_version.get("modified_at", 0)
            remote_time = conflict.remote_version.get("modified_at", 0)

            if local_time >= remote_time:
                winner = conflict.local_version
                winner_device = conflict.local_device
            else:
                winner = conflict.remote_version
                winner_device = conflict.remote_device

            logger.info(f"Conflict resolved (last_write_wins): {conflict.file_id} -> {winner_device}")
            return winner

        if strategy == "merge":
            merged = await self._try_merge(conflict)
            if merged:
                logger.info(f"Conflict resolved (merge): {conflict.file_id}")
                return merged
            return await self.resolve_conflict(conflict, "last_write_wins")

        if strategy == "ask":
            if "conflict_detected" in self._sync_handlers:
                return await self._sync_handlers["conflict_detected"](conflict)
            return conflict.local_version

        return conflict.local_version

    async def _try_merge(self, conflict: ConflictInfo) -> dict[str, Any] | None:
        """尝试合并"""
        local_content = conflict.local_version.get("content", "")
        remote_content = conflict.remote_version.get("content", "")

        if isinstance(local_content, str) and isinstance(remote_content, str):
            if local_content in remote_content:
                return conflict.remote_version
            if remote_content in local_content:
                return conflict.local_version

        return None

    def update_device_capability(self, capability: DeviceCapability) -> None:
        """更新设备能力"""
        self._device_capabilities[capability.device_id] = capability
        logger.debug(f"Device capability updated: {capability.device_id}")

    def get_best_device_for_task(self, task_type: str) -> str | None:
        """获取最适合执行任务的设备"""
        if not self._device_capabilities:
            return None

        scored_devices = [
            (device_id, cap.compute_score())
            for device_id, cap in self._device_capabilities.items()
        ]

        scored_devices.sort(key=lambda x: x[1], reverse=True)

        return scored_devices[0][0] if scored_devices else None

    def distribute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """分发任务到最合适的设备"""
        best_device = self.get_best_device_for_task(task.get("type", "default"))

        if best_device:
            task["assigned_device"] = best_device
            logger.info(f"Task assigned to device: {best_device}")

        return task

    def set_online_status(self, is_online: bool) -> None:
        """设置在线状态"""
        self._is_online = is_online

        if is_online:
            logger.info("Device is online, processing offline cache")
            self._process_offline_cache()
        else:
            logger.info("Device is offline")

    def _process_offline_cache(self) -> None:
        """处理离线缓存"""
        for item in self._offline_cache:
            if item["type"] == "sync":
                task_data = item["task"]
                task = SyncTask(
                    task_id=task_data["task_id"],
                    file_id=task_data["file_id"],
                    source_device=task_data["source_device"],
                    target_devices=task_data["target_devices"],
                    priority=task_data.get("priority", 1)
                )
                self._sync_queue.append(task)

        cache_count = len(self._offline_cache)
        self._offline_cache.clear()
        logger.info(f"Processed {cache_count} cached items")

    def get_sync_status(self) -> dict[str, Any]:
        """获取同步状态"""
        return {
            "mode": self._current_mode.value,
            "network_quality": self._network_quality.value,
            "is_online": self._is_online,
            "last_sync": self._last_sync,
            "pending_tasks": len(self._sync_queue),
            "conflicts": len(self._conflict_queue),
            "offline_cache": len(self._offline_cache),
            "devices": len(self._device_capabilities)
        }

    def get_device_capabilities(self) -> list[dict[str, Any]]:
        """获取所有设备能力"""
        return [cap.to_dict() for cap in self._device_capabilities.values()]


smart_sync_manager = SmartSyncManager()
