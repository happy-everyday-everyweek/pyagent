"""
PyAgent 记忆系统 - 记忆存储

参考MaiBot的memory_retrieval设计，实现记忆存储和检索。
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    content: str
    timestamp: float = field(default_factory=time.time)
    memory_type: str = "general"
    importance: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    access_count: int = 0


class MemoryStorage:
    """记忆存储"""

    def __init__(self, data_dir: str = "data/memory"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._short_term: dict[str, MemoryEntry] = {}
        self._long_term: dict[str, MemoryEntry] = {}

        self.max_short_term = 100
        self.max_long_term = 1000

        self._load_long_term()

    def _get_long_term_file(self) -> Path:
        """获取长期记忆文件"""
        return self.data_dir / "long_term.json"

    def _load_long_term(self) -> None:
        """加载长期记忆"""
        file_path = self._get_long_term_file()
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self._long_term = {
                        k: MemoryEntry(**v) for k, v in data.items()
                    }
            except Exception:
                pass

    def _save_long_term(self) -> None:
        """保存长期记忆"""
        file_path = self._get_long_term_file()
        try:
            data = {
                k: {
                    "key": v.key,
                    "content": v.content,
                    "timestamp": v.timestamp,
                    "memory_type": v.memory_type,
                    "importance": v.importance,
                    "metadata": v.metadata,
                    "access_count": v.access_count
                }
                for k, v in self._long_term.items()
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    async def store(
        self,
        key: str,
        content: str,
        memory_type: str = "general",
        importance: int = 1,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """存储记忆"""
        entry = MemoryEntry(
            key=key,
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )

        if memory_type == "short_term":
            self._short_term[key] = entry
            self._cleanup_short_term()
        else:
            self._long_term[key] = entry
            self._cleanup_long_term()
            self._save_long_term()

        return True

    async def retrieve(self, key: str) -> str | None:
        """检索记忆"""
        if key in self._short_term:
            entry = self._short_term[key]
            entry.access_count += 1
            return entry.content

        if key in self._long_term:
            entry = self._long_term[key]
            entry.access_count += 1
            self._save_long_term()
            return entry.content

        return None

    async def forget(self, key: str) -> bool:
        """遗忘记忆"""
        forgotten = False

        if key in self._short_term:
            del self._short_term[key]
            forgotten = True

        if key in self._long_term:
            del self._long_term[key]
            self._save_long_term()
            forgotten = True

        return forgotten

    async def search(
        self,
        query: str,
        memory_type: str | None = None,
        limit: int = 10
    ) -> list[MemoryEntry]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()

        memories = []
        if memory_type == "short_term" or memory_type is None:
            memories.extend(self._short_term.values())
        if memory_type == "long_term" or memory_type is None:
            memories.extend(self._long_term.values())

        for entry in memories:
            if query_lower in entry.content.lower():
                results.append(entry)

        results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
        return results[:limit]

    async def list_all(
        self,
        memory_type: str | None = None
    ) -> list[MemoryEntry]:
        """列出所有记忆"""
        memories = []

        if memory_type == "short_term" or memory_type is None:
            memories.extend(self._short_term.values())
        if memory_type == "long_term" or memory_type is None:
            memories.extend(self._long_term.values())

        return memories

    def _cleanup_short_term(self) -> None:
        """清理短期记忆"""
        if len(self._short_term) > self.max_short_term:
            sorted_entries = sorted(
                self._short_term.items(),
                key=lambda x: x[1].access_count
            )
            for key, _ in sorted_entries[:len(self._short_term) - self.max_short_term]:
                del self._short_term[key]

    def _cleanup_long_term(self) -> None:
        """清理长期记忆"""
        if len(self._long_term) > self.max_long_term:
            sorted_entries = sorted(
                self._long_term.items(),
                key=lambda x: (x[1].importance, x[1].access_count)
            )
            for key, _ in sorted_entries[:len(self._long_term) - self.max_long_term]:
                del self._long_term[key]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
            "total_count": len(self._short_term) + len(self._long_term)
        }


memory_storage = MemoryStorage()
