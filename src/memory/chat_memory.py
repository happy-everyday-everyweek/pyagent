"""
PyAgent 记忆系统 - 聊天智能体记忆存储

实现四级记忆架构：
- 初级记忆（daily）：日常对话记忆
- 周级记忆（weekly）：每周整理初级记忆形成
- 月级记忆（monthly）：每月整理周级记忆形成
- 季度级记忆（quarterly）：每季度整理月级记忆形成

特点：
- 四个级别内的所有记忆都全部召回
- 不设置删除机制
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .types import ChatMemoryEntry, MemoryConsolidationResult, MemoryLevel


class ChatMemoryStorage:
    """聊天智能体记忆存储"""

    def __init__(self, data_dir: str = "data/memory/chat"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._memories: dict[str, ChatMemoryEntry] = {}
        self._by_level: dict[MemoryLevel, list[str]] = {
            MemoryLevel.DAILY: [],
            MemoryLevel.WEEKLY: [],
            MemoryLevel.MONTHLY: [],
            MemoryLevel.QUARTERLY: [],
        }

        self._load_memories()

    def _get_storage_file(self) -> Path:
        return self.data_dir / "chat_memories.json"

    def _load_memories(self) -> None:
        file_path = self._get_storage_file()
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("memories", []):
                        entry = ChatMemoryEntry.from_dict(item)
                        self._memories[entry.id] = entry
                        self._by_level[entry.level].append(entry.id)
            except Exception:
                pass

    def _save_memories(self) -> None:
        file_path = self._get_storage_file()
        try:
            data = {
                "memories": [m.to_dict() for m in self._memories.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_id(self) -> str:
        return f"chat_mem_{uuid.uuid4().hex[:12]}"

    async def store(
        self,
        content: str,
        level: MemoryLevel = MemoryLevel.DAILY,
        source: str = "",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
        consolidated_from: list[str] | None = None,
    ) -> ChatMemoryEntry:
        entry = ChatMemoryEntry(
            id=self._generate_id(),
            content=content,
            level=level,
            source=source,
            importance=importance,
            metadata=metadata or {},
            consolidated_from=consolidated_from or [],
        )

        self._memories[entry.id] = entry
        self._by_level[level].append(entry.id)
        self._save_memories()

        return entry

    async def retrieve(self, memory_id: str) -> ChatMemoryEntry | None:
        entry = self._memories.get(memory_id)
        if entry:
            entry.access_count += 1
            self._save_memories()
        return entry

    async def recall_all(self) -> list[ChatMemoryEntry]:
        all_memories = []
        for level in [MemoryLevel.DAILY, MemoryLevel.WEEKLY, MemoryLevel.MONTHLY, MemoryLevel.QUARTERLY]:
            for mid in self._by_level[level]:
                if mid in self._memories:
                    all_memories.append(self._memories[mid])
        return all_memories

    async def recall_by_level(self, level: MemoryLevel) -> list[ChatMemoryEntry]:
        memories = []
        for mid in self._by_level[level]:
            if mid in self._memories:
                memories.append(self._memories[mid])
        return memories

    async def search(
        self,
        query: str,
        levels: list[MemoryLevel] | None = None,
        limit: int = 20,
    ) -> list[ChatMemoryEntry]:
        results = []
        query_lower = query.lower()

        search_levels = levels or list(MemoryLevel)

        for level in search_levels:
            for mid in self._by_level[level]:
                if mid in self._memories:
                    entry = self._memories[mid]
                    if query_lower in entry.content.lower():
                        results.append(entry)

        results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
        return results[:limit]

    async def consolidate_daily_to_weekly(
        self,
        days: int = 7,
        llm_client: Any | None = None,
    ) -> MemoryConsolidationResult:
        now = datetime.now()
        cutoff = (now - timedelta(days=days)).timestamp()

        daily_to_consolidate = []
        for mid in self._by_level[MemoryLevel.DAILY]:
            if mid in self._memories:
                entry = self._memories[mid]
                if entry.timestamp >= cutoff:
                    daily_to_consolidate.append(entry)

        if not daily_to_consolidate:
            return MemoryConsolidationResult(
                source_level=MemoryLevel.DAILY,
                target_level=MemoryLevel.WEEKLY,
                source_count=0,
                consolidated_count=0,
            )

        daily_to_consolidate.sort(key=lambda x: x.timestamp)

        consolidated_content = await self._consolidate_memories(
            daily_to_consolidate, "weekly", llm_client
        )

        if consolidated_content:
            new_entry = await self.store(
                content=consolidated_content,
                level=MemoryLevel.WEEKLY,
                source="consolidation",
                importance=0.7,
                consolidated_from=[e.id for e in daily_to_consolidate],
            )

            return MemoryConsolidationResult(
                source_level=MemoryLevel.DAILY,
                target_level=MemoryLevel.WEEKLY,
                source_count=len(daily_to_consolidate),
                consolidated_count=len(daily_to_consolidate),
                consolidated_ids=[e.id for e in daily_to_consolidate],
                new_entry_id=new_entry.id,
            )

        return MemoryConsolidationResult(
            source_level=MemoryLevel.DAILY,
            target_level=MemoryLevel.WEEKLY,
            source_count=len(daily_to_consolidate),
            consolidated_count=0,
        )

    async def consolidate_weekly_to_monthly(
        self,
        weeks: int = 4,
        llm_client: Any | None = None,
    ) -> MemoryConsolidationResult:
        now = datetime.now()
        cutoff = (now - timedelta(weeks=weeks)).timestamp()

        weekly_to_consolidate = []
        for mid in self._by_level[MemoryLevel.WEEKLY]:
            if mid in self._memories:
                entry = self._memories[mid]
                if entry.timestamp >= cutoff:
                    weekly_to_consolidate.append(entry)

        if not weekly_to_consolidate:
            return MemoryConsolidationResult(
                source_level=MemoryLevel.WEEKLY,
                target_level=MemoryLevel.MONTHLY,
                source_count=0,
                consolidated_count=0,
            )

        weekly_to_consolidate.sort(key=lambda x: x.timestamp)

        consolidated_content = await self._consolidate_memories(
            weekly_to_consolidate, "monthly", llm_client
        )

        if consolidated_content:
            new_entry = await self.store(
                content=consolidated_content,
                level=MemoryLevel.MONTHLY,
                source="consolidation",
                importance=0.8,
                consolidated_from=[e.id for e in weekly_to_consolidate],
            )

            return MemoryConsolidationResult(
                source_level=MemoryLevel.WEEKLY,
                target_level=MemoryLevel.MONTHLY,
                source_count=len(weekly_to_consolidate),
                consolidated_count=len(weekly_to_consolidate),
                consolidated_ids=[e.id for e in weekly_to_consolidate],
                new_entry_id=new_entry.id,
            )

        return MemoryConsolidationResult(
            source_level=MemoryLevel.WEEKLY,
            target_level=MemoryLevel.MONTHLY,
            source_count=len(weekly_to_consolidate),
            consolidated_count=0,
        )

    async def consolidate_monthly_to_quarterly(
        self,
        months: int = 3,
        llm_client: Any | None = None,
    ) -> MemoryConsolidationResult:
        now = datetime.now()
        cutoff = (now - timedelta(days=months * 30)).timestamp()

        monthly_to_consolidate = []
        for mid in self._by_level[MemoryLevel.MONTHLY]:
            if mid in self._memories:
                entry = self._memories[mid]
                if entry.timestamp >= cutoff:
                    monthly_to_consolidate.append(entry)

        if not monthly_to_consolidate:
            return MemoryConsolidationResult(
                source_level=MemoryLevel.MONTHLY,
                target_level=MemoryLevel.QUARTERLY,
                source_count=0,
                consolidated_count=0,
            )

        monthly_to_consolidate.sort(key=lambda x: x.timestamp)

        consolidated_content = await self._consolidate_memories(
            monthly_to_consolidate, "quarterly", llm_client
        )

        if consolidated_content:
            new_entry = await self.store(
                content=consolidated_content,
                level=MemoryLevel.QUARTERLY,
                source="consolidation",
                importance=0.9,
                consolidated_from=[e.id for e in monthly_to_consolidate],
            )

            return MemoryConsolidationResult(
                source_level=MemoryLevel.MONTHLY,
                target_level=MemoryLevel.QUARTERLY,
                source_count=len(monthly_to_consolidate),
                consolidated_count=len(monthly_to_consolidate),
                consolidated_ids=[e.id for e in monthly_to_consolidate],
                new_entry_id=new_entry.id,
            )

        return MemoryConsolidationResult(
            source_level=MemoryLevel.MONTHLY,
            target_level=MemoryLevel.QUARTERLY,
            source_count=len(monthly_to_consolidate),
            consolidated_count=0,
        )

    async def _consolidate_memories(
        self,
        memories: list[ChatMemoryEntry],
        target_level: str,
        llm_client: Any | None = None,
    ) -> str | None:
        if not memories:
            return None

        if llm_client:
            try:
                memory_texts = "\n".join([
                    f"- [{m.timestamp}] {m.content}"
                    for m in memories
                ])

                prompt = f"""请将以下记忆条目整理为一条简洁的{target_level}级记忆摘要。

记忆条目：
{memory_texts}

要求：
1. 提取关键信息和重要事件
2. 去除重复内容
3. 保持时间顺序
4. 输出一条完整的摘要

请直接输出摘要内容："""

                response = await llm_client.generate(prompt)
                return response.strip() if response else None
            except Exception:
                pass

        unique_contents = []
        seen = set()
        for m in memories:
            content = m.content.strip()
            if content and content not in seen:
                unique_contents.append(content)
                seen.add(content)

        return f"[{target_level}级记忆摘要] " + " | ".join(unique_contents[:10])

    def get_statistics(self) -> dict[str, Any]:
        stats = {
            "total_count": len(self._memories),
            "by_level": {},
        }

        for level in MemoryLevel:
            stats["by_level"][level.value] = len(self._by_level[level])

        return stats

    def format_for_prompt(self, max_entries_per_level: int = 10) -> str:
        lines = ["## 聊天记忆"]

        level_names = {
            MemoryLevel.QUARTERLY: "季度记忆",
            MemoryLevel.MONTHLY: "月度记忆",
            MemoryLevel.WEEKLY: "周度记忆",
            MemoryLevel.DAILY: "日常记忆",
        }

        for level, name in level_names.items():
            entries = []
            for mid in self._by_level[level]:
                if mid in self._memories:
                    entries.append(self._memories[mid])

            if entries:
                lines.append(f"\n### {name}")
                entries.sort(key=lambda x: x.timestamp, reverse=True)
                for entry in entries[:max_entries_per_level]:
                    lines.append(f"- {entry.content}")

        return "\n".join(lines)


chat_memory_storage = ChatMemoryStorage()
