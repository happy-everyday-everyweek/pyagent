"""
PyAgent 数据同步引擎 - 多设备数据同步

实现实时同步和定时同步模式，支持类Git的提交模型。
"""

import hashlib
import json
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


class SyncMode(Enum):
    """同步模式"""
    REALTIME = "realtime"
    INTERVAL = "interval"


class ChangeType(Enum):
    """变更类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class DataChange:
    """数据变更记录"""
    change_id: str
    change_type: str
    data_type: str
    data_key: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    device_id: str
    timestamp: str
    commit_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "change_type": self.change_type,
            "data_type": self.data_type,
            "data_key": self.data_key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "commit_id": self.commit_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataChange":
        return cls(
            change_id=data.get("change_id", ""),
            change_type=data.get("change_type", "update"),
            data_type=data.get("data_type", ""),
            data_key=data.get("data_key", ""),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            device_id=data.get("device_id", ""),
            timestamp=data.get("timestamp", ""),
            commit_id=data.get("commit_id", ""),
        )


@dataclass
class Commit:
    """提交记录"""
    commit_id: str
    parent_commit_id: str
    device_id: str
    timestamp: str
    message: str
    changes: list[dict[str, Any]] = field(default_factory=list)
    branch: str = "main"
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_id": self.commit_id,
            "parent_commit_id": self.parent_commit_id,
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "message": self.message,
            "changes": self.changes,
            "branch": self.branch,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Commit":
        return cls(
            commit_id=data.get("commit_id", ""),
            parent_commit_id=data.get("parent_commit_id", ""),
            device_id=data.get("device_id", ""),
            timestamp=data.get("timestamp", ""),
            message=data.get("message", ""),
            changes=data.get("changes", []),
            branch=data.get("branch", "main"),
            checksum=data.get("checksum", ""),
        )


@dataclass
class Branch:
    """分支信息"""
    name: str
    head_commit_id: str
    created_at: str
    created_by: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "head_commit_id": self.head_commit_id,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Branch":
        return cls(
            name=data.get("name", ""),
            head_commit_id=data.get("head_commit_id", ""),
            created_at=data.get("created_at", ""),
            created_by=data.get("created_by", ""),
        )


class SyncEngine:
    """数据同步引擎

    支持实时同步和定时同步模式，实现类Git的提交模型。
    """

    def __init__(
        self,
        data_dir: str = "data/sync",
        sync_mode: SyncMode = SyncMode.REALTIME,
        sync_interval: int = 5,
    ):
        self.data_dir = Path(data_dir)
        self.commits_dir = self.data_dir / "commits"
        self.branches_dir = self.data_dir / "branches"
        self.changes_dir = self.data_dir / "changes"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.commits_dir.mkdir(parents=True, exist_ok=True)
        self.branches_dir.mkdir(parents=True, exist_ok=True)
        self.changes_dir.mkdir(parents=True, exist_ok=True)

        self.sync_mode = sync_mode
        self.sync_interval = sync_interval

        self._pending_changes: list[DataChange] = []
        self._current_branch = "main"
        self._branches: dict[str, Branch] = {}
        self._commits: dict[str, Commit] = {}
        self._head_commit_id = ""
        self._device_id = ""

        self._sync_timer: threading.Timer | None = None
        self._sync_callbacks: list[Callable[[list[DataChange]], None]] = []
        self._lock = threading.Lock()

        self._load_state()

    def _load_state(self) -> None:
        """加载同步状态"""
        branches_file = self.data_dir / "branches.json"
        if branches_file.exists():
            try:
                with open(branches_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for branch_data in data.get("branches", []):
                        branch = Branch.from_dict(branch_data)
                        self._branches[branch.name] = branch
                    self._current_branch = data.get("current_branch", "main")
            except Exception:
                pass

        if "main" not in self._branches:
            self._branches["main"] = Branch(
                name="main",
                head_commit_id="",
                created_at=datetime.now().isoformat(),
                created_by=self._device_id,
            )

        head_file = self.data_dir / "head.json"
        if head_file.exists():
            try:
                with open(head_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self._head_commit_id = data.get("head_commit_id", "")
                    self._device_id = data.get("device_id", "")
            except Exception:
                pass

    def _save_state(self) -> None:
        """保存同步状态"""
        branches_file = self.data_dir / "branches.json"
        try:
            data = {
                "branches": [b.to_dict() for b in self._branches.values()],
                "current_branch": self._current_branch,
            }
            with open(branches_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        head_file = self.data_dir / "head.json"
        try:
            data = {
                "head_commit_id": self._head_commit_id,
                "device_id": self._device_id,
            }
            with open(head_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_device_id(self, device_id: str) -> None:
        """设置设备ID

        Args:
            device_id: 设备ID
        """
        self._device_id = device_id
        self._save_state()

    def track_change(
        self,
        change_type: ChangeType,
        data_type: str,
        data_key: str,
        old_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
    ) -> str:
        """追踪数据变更

        Args:
            change_type: 变更类型
            data_type: 数据类型
            data_key: 数据键
            old_value: 旧值
            new_value: 新值

        Returns:
            str: 变更ID
        """
        with self._lock:
            change = DataChange(
                change_id=str(uuid4()),
                change_type=change_type.value,
                data_type=data_type,
                data_key=data_key,
                old_value=old_value,
                new_value=new_value,
                device_id=self._device_id,
                timestamp=datetime.now().isoformat(),
                commit_id="",
            )

            self._pending_changes.append(change)

            if self.sync_mode == SyncMode.REALTIME:
                self._sync_now()

            return change.change_id

    def commit(self, message: str = "") -> str:
        """提交变更

        Args:
            message: 提交消息

        Returns:
            str: 提交ID
        """
        with self._lock:
            if not self._pending_changes:
                return ""

            commit_id = self._generate_commit_id()
            changes_data = [c.to_dict() for c in self._pending_changes]
            checksum = self._calculate_checksum(changes_data)

            commit = Commit(
                commit_id=commit_id,
                parent_commit_id=self._head_commit_id,
                device_id=self._device_id,
                timestamp=datetime.now().isoformat(),
                message=message or f"Commit {len(self._commits) + 1}",
                changes=changes_data,
                branch=self._current_branch,
                checksum=checksum,
            )

            for change in self._pending_changes:
                change.commit_id = commit_id
                self._save_change(change)

            self._save_commit(commit)
            self._commits[commit_id] = commit

            self._head_commit_id = commit_id
            if self._current_branch in self._branches:
                self._branches[self._current_branch].head_commit_id = commit_id

            committed_changes = self._pending_changes.copy()
            self._pending_changes.clear()
            self._save_state()

            for callback in self._sync_callbacks:
                try:
                    callback(committed_changes)
                except Exception:
                    pass

            return commit_id

    def _generate_commit_id(self) -> str:
        """生成提交ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid4())[:8]
        return f"c_{timestamp}_{random_suffix}"

    def _calculate_checksum(self, data: list[dict[str, Any]]) -> str:
        """计算数据校验和"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def _save_change(self, change: DataChange) -> None:
        """保存变更记录"""
        change_file = self.changes_dir / f"{change.change_id}.json"
        try:
            with open(change_file, "w", encoding="utf-8") as f:
                json.dump(change.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_commit(self, commit: Commit) -> None:
        """保存提交记录"""
        commit_file = self.commits_dir / f"{commit.commit_id}.json"
        try:
            with open(commit_file, "w", encoding="utf-8") as f:
                json.dump(commit.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _sync_now(self) -> None:
        """立即同步"""
        if self._pending_changes:
            self.commit("Auto sync")

    def start_interval_sync(self) -> None:
        """启动定时同步"""
        if self.sync_mode != SyncMode.INTERVAL:
            return

        self._stop_sync_timer()
        self._sync_timer = threading.Timer(
            self.sync_interval * 60,
            self._interval_sync_task
        )
        self._sync_timer.daemon = True
        self._sync_timer.start()

    def _stop_sync_timer(self) -> None:
        """停止同步定时器"""
        if self._sync_timer is not None:
            self._sync_timer.cancel()
            self._sync_timer = None

    def _interval_sync_task(self) -> None:
        """定时同步任务"""
        self._sync_now()
        self.start_interval_sync()

    def stop_sync(self) -> None:
        """停止同步"""
        self._stop_sync_timer()
        if self._pending_changes:
            self.commit("Final sync before stop")

    def create_branch(self, name: str) -> bool:
        """创建新分支

        Args:
            name: 分支名称

        Returns:
            bool: 是否成功创建
        """
        with self._lock:
            if name in self._branches:
                return False

            branch = Branch(
                name=name,
                head_commit_id=self._head_commit_id,
                created_at=datetime.now().isoformat(),
                created_by=self._device_id,
            )
            self._branches[name] = branch
            self._save_state()
            return True

    def switch_branch(self, name: str) -> bool:
        """切换分支

        Args:
            name: 分支名称

        Returns:
            bool: 是否成功切换
        """
        with self._lock:
            if name not in self._branches:
                return False

            if self._pending_changes:
                self.commit(f"Commit before switching to {name}")

            self._current_branch = name
            self._head_commit_id = self._branches[name].head_commit_id
            self._save_state()
            return True

    def get_current_branch(self) -> str:
        """获取当前分支名称

        Returns:
            str: 当前分支名称
        """
        return self._current_branch

    def get_branches(self) -> list[str]:
        """获取所有分支名称

        Returns:
            list[str]: 分支名称列表
        """
        return list(self._branches.keys())

    def get_commit_history(self, limit: int = 50) -> list[Commit]:
        """获取提交历史

        Args:
            limit: 最大返回数量

        Returns:
            list[Commit]: 提交列表（按时间倒序）
        """
        commits: list[Commit] = []
        current_id = self._head_commit_id

        while current_id and len(commits) < limit:
            commit_file = self.commits_dir / f"{current_id}.json"
            if not commit_file.exists():
                break

            try:
                with open(commit_file, encoding="utf-8") as f:
                    data = json.load(f)
                    commit = Commit.from_dict(data)
                    commits.append(commit)
                    current_id = commit.parent_commit_id
            except Exception:
                break

        return commits

    def get_pending_changes(self) -> list[DataChange]:
        """获取待提交的变更

        Returns:
            list[DataChange]: 变更列表
        """
        with self._lock:
            return self._pending_changes.copy()

    def has_pending_changes(self) -> bool:
        """检查是否有待提交的变更

        Returns:
            bool: 是否有待提交的变更
        """
        with self._lock:
            return len(self._pending_changes) > 0

    def register_sync_callback(self, callback: Callable[[list[DataChange]], None]) -> None:
        """注册同步回调函数

        Args:
            callback: 回调函数
        """
        self._sync_callbacks.append(callback)

    def unregister_sync_callback(self, callback: Callable[[list[DataChange]], None]) -> None:
        """注销同步回调函数

        Args:
            callback: 回调函数
        """
        if callback in self._sync_callbacks:
            self._sync_callbacks.remove(callback)

    def get_head_commit_id(self) -> str:
        """获取当前HEAD提交ID

        Returns:
            str: 提交ID
        """
        return self._head_commit_id

    def get_commit(self, commit_id: str) -> Commit | None:
        """获取指定提交

        Args:
            commit_id: 提交ID

        Returns:
            Commit | None: 提交对象
        """
        commit_file = self.commits_dir / f"{commit_id}.json"
        if not commit_file.exists():
            return None

        try:
            with open(commit_file, encoding="utf-8") as f:
                data = json.load(f)
                return Commit.from_dict(data)
        except Exception:
            return None

    def merge_branch(self, source_branch: str, message: str = "") -> str | None:
        """合并分支

        Args:
            source_branch: 源分支名称
            message: 合并提交消息

        Returns:
            str | None: 合并提交ID，失败返回None
        """
        with self._lock:
            if source_branch not in self._branches:
                return None

            if source_branch == self._current_branch:
                return None

            source_head = self._branches[source_branch].head_commit_id
            if not source_head:
                return None

            return self.commit(message or f"Merge branch '{source_branch}'")

    def get_sync_status(self) -> dict[str, Any]:
        """获取同步状态

        Returns:
            dict[str, Any]: 同步状态信息
        """
        return {
            "sync_mode": self.sync_mode.value,
            "sync_interval": self.sync_interval,
            "current_branch": self._current_branch,
            "head_commit_id": self._head_commit_id,
            "pending_changes_count": len(self._pending_changes),
            "branches_count": len(self._branches),
            "device_id": self._device_id,
        }
