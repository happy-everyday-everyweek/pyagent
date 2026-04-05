"""
PyAgent 冲突解决机制 - 多设备数据冲突处理

实现三方合并算法和冲突检测、标记、解决功能。
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .sync_engine import Commit, DataChange


class ConflictType(Enum):
    """冲突类型"""
    UPDATE_UPDATE = "update_update"
    UPDATE_DELETE = "update_delete"
    DELETE_UPDATE = "delete_update"
    STRUCTURAL = "structural"


class ConflictStatus(Enum):
    """冲突状态"""
    DETECTED = "detected"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ABORTED = "aborted"


class ResolutionStrategy(Enum):
    """解决策略"""
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    KEEP_BOTH = "keep_both"
    MERGE = "merge"
    MANUAL = "manual"


@dataclass
class Conflict:
    """冲突记录"""
    conflict_id: str
    conflict_type: str
    data_type: str
    data_key: str
    local_change: dict[str, Any]
    remote_change: dict[str, Any]
    base_value: dict[str, Any] | None
    status: str
    detected_at: str
    resolved_at: str = ""
    resolution_strategy: str = ""
    resolved_value: dict[str, Any] | None = None
    resolved_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type,
            "data_type": self.data_type,
            "data_key": self.data_key,
            "local_change": self.local_change,
            "remote_change": self.remote_change,
            "base_value": self.base_value,
            "status": self.status,
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
            "resolution_strategy": self.resolution_strategy,
            "resolved_value": self.resolved_value,
            "resolved_by": self.resolved_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conflict":
        return cls(
            conflict_id=data.get("conflict_id", ""),
            conflict_type=data.get("conflict_type", "update_update"),
            data_type=data.get("data_type", ""),
            data_key=data.get("data_key", ""),
            local_change=data.get("local_change", {}),
            remote_change=data.get("remote_change", {}),
            base_value=data.get("base_value"),
            status=data.get("status", "detected"),
            detected_at=data.get("detected_at", ""),
            resolved_at=data.get("resolved_at", ""),
            resolution_strategy=data.get("resolution_strategy", ""),
            resolved_value=data.get("resolved_value"),
            resolved_by=data.get("resolved_by", ""),
        )


@dataclass
class MergeResult:
    """合并结果"""
    success: bool
    merged_value: dict[str, Any] | None
    has_conflicts: bool
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "merged_value": self.merged_value,
            "has_conflicts": self.has_conflicts,
            "conflicts": self.conflicts,
            "message": self.message,
        }


class ThreeWayMerger:
    """三方合并算法实现"""

    @staticmethod
    def merge(
        base: dict[str, Any] | None,
        local: dict[str, Any] | None,
        remote: dict[str, Any] | None,
    ) -> MergeResult:
        """执行三方合并

        Args:
            base: 基础值（共同祖先）
            local: 本地变更值
            remote: 远程变更值

        Returns:
            MergeResult: 合并结果
        """
        if base is None:
            if local is None and remote is None:
                return MergeResult(
                    success=True,
                    merged_value=None,
                    has_conflicts=False,
                    message="No changes",
                )
            if local is None:
                return MergeResult(
                    success=True,
                    merged_value=remote,
                    has_conflicts=False,
                    message="Remote only",
                )
            if remote is None:
                return MergeResult(
                    success=True,
                    merged_value=local,
                    has_conflicts=False,
                    message="Local only",
                )
            if local == remote:
                return MergeResult(
                    success=True,
                    merged_value=local,
                    has_conflicts=False,
                    message="Same changes",
                )
            return MergeResult(
                success=False,
                merged_value=None,
                has_conflicts=True,
                message="Conflict: both added different values",
            )

        if local is None and remote is None:
            return MergeResult(
                success=True,
                merged_value=None,
                has_conflicts=False,
                message="Both deleted",
            )

        if local is None:
            if remote == base:
                return MergeResult(
                    success=True,
                    merged_value=None,
                    has_conflicts=False,
                    message="Local deleted, remote unchanged",
                )
            return MergeResult(
                success=False,
                merged_value=None,
                has_conflicts=True,
                message="Conflict: local deleted, remote modified",
            )

        if remote is None:
            if local == base:
                return MergeResult(
                    success=True,
                    merged_value=None,
                    has_conflicts=False,
                    message="Remote deleted, local unchanged",
                )
            return MergeResult(
                success=False,
                merged_value=None,
                has_conflicts=True,
                message="Conflict: remote deleted, local modified",
            )

        if local == remote:
            return MergeResult(
                success=True,
                merged_value=local,
                has_conflicts=False,
                message="Same modifications",
            )

        if local == base:
            return MergeResult(
                success=True,
                merged_value=remote,
                has_conflicts=False,
                message="Local unchanged, use remote",
            )

        if remote == base:
            return MergeResult(
                success=True,
                merged_value=local,
                has_conflicts=False,
                message="Remote unchanged, use local",
            )

        return ThreeWayMerger._deep_merge(base, local, remote)

    @staticmethod
    def _deep_merge(
        base: dict[str, Any],
        local: dict[str, Any],
        remote: dict[str, Any],
    ) -> MergeResult:
        """深度合并字典

        Args:
            base: 基础字典
            local: 本地字典
            remote: 远程字典

        Returns:
            MergeResult: 合并结果
        """
        merged: dict[str, Any] = {}
        conflicts: list[dict[str, Any]] = []
        all_keys = set(base.keys()) | set(local.keys()) | set(remote.keys())

        for key in all_keys:
            base_val = base.get(key)
            local_val = local.get(key)
            remote_val = remote.get(key)

            if isinstance(base_val, dict) and isinstance(local_val, dict) and isinstance(remote_val, dict):
                sub_result = ThreeWayMerger._deep_merge(base_val, local_val, remote_val)
                if sub_result.success:
                    if sub_result.merged_value is not None:
                        merged[key] = sub_result.merged_value
                else:
                    conflicts.extend(sub_result.conflicts)
                    merged[key] = {
                        "CONFLICT": True,
                        "local": local_val,
                        "remote": remote_val,
                        "base": base_val,
                    }
            elif isinstance(local_val, list) and isinstance(remote_val, list):
                merged[key] = ThreeWayMerger._merge_lists(base_val, local_val, remote_val)
            else:
                key_result = ThreeWayMerger.merge(
                    base_val if isinstance(base_val, dict) else None,
                    local_val if isinstance(local_val, dict) else None,
                    remote_val if isinstance(remote_val, dict) else None,
                )

                if key_result.success:
                    if key_result.merged_value is not None:
                        merged[key] = key_result.merged_value
                else:
                    conflicts.append({
                        "key": key,
                        "local": local_val,
                        "remote": remote_val,
                        "base": base_val,
                    })
                    merged[key] = {
                        "CONFLICT": True,
                        "local": local_val,
                        "remote": remote_val,
                        "base": base_val,
                    }

        if conflicts:
            return MergeResult(
                success=False,
                merged_value=merged,
                has_conflicts=True,
                conflicts=conflicts,
                message=f"Found {len(conflicts)} conflicts",
            )

        return MergeResult(
            success=True,
            merged_value=merged,
            has_conflicts=False,
            message="Successfully merged",
        )

    @staticmethod
    def _merge_lists(
        base: list[Any],
        local: list[Any],
        remote: list[Any],
    ) -> list[Any]:
        """合并列表

        Args:
            base: 基础列表
            local: 本地列表
            remote: 远程列表

        Returns:
            list[Any]: 合并后的列表
        """
        if local == remote:
            return local

        if local == base:
            return remote

        if remote == base:
            return local

        base_set = {str(x) for x in base}
        local_set = {str(x) for x in local}
        remote_set = {str(x) for x in remote}

        added_local = local_set - base_set
        added_remote = remote_set - base_set
        removed_local = base_set - local_set
        removed_remote = base_set - remote_set

        result_set = (base_set - removed_local - removed_remote) | added_local | added_remote

        result: list[Any] = []
        seen = set()
        for item in local + remote:
            item_str = str(item)
            if item_str in result_set and item_str not in seen:
                result.append(item)
                seen.add(item_str)

        return result


class ConflictResolver:
    """冲突解决器

    实现冲突检测、标记和解决功能。
    """

    def __init__(self, data_dir: str = "data/conflicts"):
        self.data_dir = Path(data_dir)
        self.conflicts_dir = self.data_dir / "records"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.conflicts_dir.mkdir(parents=True, exist_ok=True)

        self._merger = ThreeWayMerger()
        self._conflicts: dict[str, Conflict] = {}
        self._resolution_handlers: dict[str, Callable[[Conflict], dict[str, Any] | None]] = {}

        self._load_conflicts()

    def _load_conflicts(self) -> None:
        """加载冲突记录"""
        for conflict_file in self.conflicts_dir.glob("*.json"):
            try:
                with open(conflict_file, encoding="utf-8") as f:
                    data = json.load(f)
                    conflict = Conflict.from_dict(data)
                    self._conflicts[conflict.conflict_id] = conflict
            except Exception:
                pass

    def _save_conflict(self, conflict: Conflict) -> None:
        """保存冲突记录"""
        conflict_file = self.conflicts_dir / f"{conflict.conflict_id}.json"
        try:
            with open(conflict_file, "w", encoding="utf-8") as f:
                json.dump(conflict.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def detect_conflict(
        self,
        local_change: DataChange,
        remote_change: DataChange,
        base_value: dict[str, Any] | None,
    ) -> Conflict | None:
        """检测两个变更之间是否存在冲突

        Args:
            local_change: 本地变更
            remote_change: 远程变更
            base_value: 基础值

        Returns:
            Conflict | None: 冲突记录，无冲突返回None
        """
        if local_change.data_key != remote_change.data_key:
            return None

        if local_change.change_type == "create" and remote_change.change_type == "create":
            if local_change.new_value == remote_change.new_value:
                return None
            conflict_type = ConflictType.UPDATE_UPDATE.value
        elif local_change.change_type == "delete" and remote_change.change_type == "update":
            conflict_type = ConflictType.DELETE_UPDATE.value
        elif local_change.change_type == "update" and remote_change.change_type == "delete":
            conflict_type = ConflictType.UPDATE_DELETE.value
        elif local_change.change_type == "update" and remote_change.change_type == "update":
            if local_change.new_value == remote_change.new_value:
                return None
            conflict_type = ConflictType.UPDATE_UPDATE.value
        else:
            return None

        conflict = Conflict(
            conflict_id=str(uuid4()),
            conflict_type=conflict_type,
            data_type=local_change.data_type,
            data_key=local_change.data_key,
            local_change=local_change.to_dict(),
            remote_change=remote_change.to_dict(),
            base_value=base_value,
            status=ConflictStatus.DETECTED.value,
            detected_at=datetime.now().isoformat(),
        )

        self._conflicts[conflict.conflict_id] = conflict
        self._save_conflict(conflict)

        return conflict

    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: ResolutionStrategy,
        resolved_value: dict[str, Any] | None = None,
        resolved_by: str = "",
    ) -> bool:
        """解决冲突

        Args:
            conflict_id: 冲突ID
            strategy: 解决策略
            resolved_value: 手动解决时的值
            resolved_by: 解决者设备ID

        Returns:
            bool: 是否成功解决
        """
        if conflict_id not in self._conflicts:
            return False

        conflict = self._conflicts[conflict_id]

        if conflict.status == ConflictStatus.RESOLVED.value:
            return True

        conflict.status = ConflictStatus.RESOLVING.value
        self._save_conflict(conflict)

        final_value: dict[str, Any] | None = None

        if strategy == ResolutionStrategy.KEEP_LOCAL:
            final_value = conflict.local_change.get("new_value")
        elif strategy == ResolutionStrategy.KEEP_REMOTE:
            final_value = conflict.remote_change.get("new_value")
        elif strategy == ResolutionStrategy.KEEP_BOTH:
            local_val = conflict.local_change.get("new_value", {})
            remote_val = conflict.remote_change.get("new_value", {})
            if isinstance(local_val, dict) and isinstance(remote_val, dict):
                final_value = {**remote_val, **local_val}
            else:
                final_value = {"local": local_val, "remote": remote_val}
        elif strategy == ResolutionStrategy.MERGE:
            base = conflict.base_value
            local = conflict.local_change.get("new_value")
            remote = conflict.remote_change.get("new_value")

            if isinstance(base, dict) and isinstance(local, dict) and isinstance(remote, dict):
                result = self._merger.merge(base, local, remote)
                if result.success:
                    final_value = result.merged_value
                else:
                    conflict.status = ConflictStatus.DETECTED.value
                    self._save_conflict(conflict)
                    return False
            else:
                final_value = remote
        elif strategy == ResolutionStrategy.MANUAL:
            final_value = resolved_value

        conflict.status = ConflictStatus.RESOLVED.value
        conflict.resolution_strategy = strategy.value
        conflict.resolved_value = final_value
        conflict.resolved_at = datetime.now().isoformat()
        conflict.resolved_by = resolved_by

        self._save_conflict(conflict)
        return True

    def auto_resolve(self, conflict_id: str) -> bool:
        """自动解决冲突

        Args:
            conflict_id: 冲突ID

        Returns:
            bool: 是否成功解决
        """
        if conflict_id not in self._conflicts:
            return False

        conflict = self._conflicts[conflict_id]

        if conflict.conflict_type == ConflictType.UPDATE_UPDATE.value:
            base = conflict.base_value
            local = conflict.local_change.get("new_value")
            remote = conflict.remote_change.get("new_value")

            if isinstance(base, dict) and isinstance(local, dict) and isinstance(remote, dict):
                result = self._merger.merge(base, local, remote)
                if result.success:
                    return self.resolve_conflict(
                        conflict_id,
                        ResolutionStrategy.MERGE,
                        result.merged_value,
                        "auto",
                    )

        return self.resolve_conflict(
            conflict_id,
            ResolutionStrategy.KEEP_REMOTE,
            None,
            "auto",
        )

    def get_conflict(self, conflict_id: str) -> Conflict | None:
        """获取冲突记录

        Args:
            conflict_id: 冲突ID

        Returns:
            Conflict | None: 冲突记录
        """
        return self._conflicts.get(conflict_id)

    def get_pending_conflicts(self) -> list[Conflict]:
        """获取待解决的冲突列表

        Returns:
            list[Conflict]: 冲突列表
        """
        return [
            c for c in self._conflicts.values()
            if c.status == ConflictStatus.DETECTED.value
        ]

    def get_all_conflicts(self) -> list[Conflict]:
        """获取所有冲突记录

        Returns:
            list[Conflict]: 冲突列表
        """
        return list(self._conflicts.values())

    def get_conflicts_by_status(self, status: ConflictStatus) -> list[Conflict]:
        """按状态获取冲突记录

        Args:
            status: 冲突状态

        Returns:
            list[Conflict]: 冲突列表
        """
        return [c for c in self._conflicts.values() if c.status == status.value]

    def register_resolution_handler(
        self,
        data_type: str,
        handler: Callable[[Conflict], dict[str, Any] | None],
    ) -> None:
        """注册自定义冲突解决处理器

        Args:
            data_type: 数据类型
            handler: 处理函数
        """
        self._resolution_handlers[data_type] = handler

    def unregister_resolution_handler(self, data_type: str) -> None:
        """注销自定义冲突解决处理器

        Args:
            data_type: 数据类型
        """
        if data_type in self._resolution_handlers:
            del self._resolution_handlers[data_type]

    def resolve_with_handler(self, conflict_id: str) -> bool:
        """使用注册的处理器解决冲突

        Args:
            conflict_id: 冲突ID

        Returns:
            bool: 是否成功解决
        """
        if conflict_id not in self._conflicts:
            return False

        conflict = self._conflicts[conflict_id]

        if conflict.data_type not in self._resolution_handlers:
            return self.auto_resolve(conflict_id)

        handler = self._resolution_handlers[conflict.data_type]
        try:
            resolved_value = handler(conflict)
            if resolved_value is not None:
                return self.resolve_conflict(
                    conflict_id,
                    ResolutionStrategy.MANUAL,
                    resolved_value,
                    "handler",
                )
        except Exception:
            pass

        return self.auto_resolve(conflict_id)

    def merge_commits(
        self,
        local_commit: Commit,
        remote_commit: Commit,
        base_commit: Commit | None,
    ) -> MergeResult:
        """合并两个提交

        Args:
            local_commit: 本地提交
            remote_commit: 远程提交
            base_commit: 共同祖先提交

        Returns:
            MergeResult: 合并结果
        """
        local_changes = {c["data_key"]: c for c in local_commit.changes}
        remote_changes = {c["data_key"]: c for c in remote_commit.changes}

        base_values: dict[str, dict[str, Any] | None] = {}
        if base_commit:
            for change in base_commit.changes:
                base_values[change["data_key"]] = change.get("new_value")

        merged_changes: list[dict[str, Any]] = []
        all_keys = set(local_changes.keys()) | set(remote_changes.keys())
        conflicts: list[dict[str, Any]] = []

        for key in all_keys:
            local_change = local_changes.get(key)
            remote_change = remote_changes.get(key)
            base_value = base_values.get(key)

            if local_change and not remote_change:
                merged_changes.append(local_change)
            elif remote_change and not local_change:
                merged_changes.append(remote_change)
            elif local_change and remote_change:
                conflict = self.detect_conflict(
                    DataChange.from_dict(local_change),
                    DataChange.from_dict(remote_change),
                    base_value,
                )

                if conflict:
                    conflicts.append(conflict.to_dict())
                    if conflict.resolved_value is not None:
                        merged_change = local_change.copy()
                        merged_change["new_value"] = conflict.resolved_value
                        merged_changes.append(merged_change)
                else:
                    merged_changes.append(local_change)

        return MergeResult(
            success=len(conflicts) == 0,
            merged_value={"changes": merged_changes} if merged_changes else None,
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts,
            message=f"Merged {len(merged_changes)} changes with {len(conflicts)} conflicts",
        )

    def get_statistics(self) -> dict[str, Any]:
        """获取冲突统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        total = len(self._conflicts)
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}

        for conflict in self._conflicts.values():
            by_status[conflict.status] = by_status.get(conflict.status, 0) + 1
            by_type[conflict.conflict_type] = by_type.get(conflict.conflict_type, 0) + 1

        return {
            "total_conflicts": total,
            "by_status": by_status,
            "by_type": by_type,
            "pending_count": len(self.get_pending_conflicts()),
        }

    def clear_resolved_conflicts(self) -> int:
        """清除已解决的冲突记录

        Returns:
            int: 清除的记录数
        """
        resolved_ids = [
            cid for cid, c in self._conflicts.items()
            if c.status == ConflictStatus.RESOLVED.value
        ]

        for conflict_id in resolved_ids:
            del self._conflicts[conflict_id]
            conflict_file = self.conflicts_dir / f"{conflict_id}.json"
            if conflict_file.exists():
                try:
                    conflict_file.unlink()
                except Exception:
                    pass

        return len(resolved_ids)
