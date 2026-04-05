"""
PyAgent 记忆系统 - 统一存储

协调聊天智能体记忆和工作智能体记忆：
- 聊天智能体记忆：四级记忆架构（初级/周级/月级/季度级）
- 工作智能体记忆：项目记忆 + 偏好记忆
"""

from typing import Any

from .chat_memory import ChatMemoryStorage
from .types import (
    ChatMemoryEntry,
    MemoryConsolidationResult,
    MemoryLevel,
    MemoryPriority,
    PreferenceMemory,
    ProjectMemoryDomain,
    ProjectMemoryEntry,
)
from .work_memory import WorkMemoryStorage


class UnifiedMemoryStore:
    """统一记忆存储"""

    def __init__(
        self,
        chat_data_dir: str = "data/memory/chat",
        work_data_dir: str = "data/memory/work",
    ):
        self.chat_memory = ChatMemoryStorage(chat_data_dir)
        self.work_memory = WorkMemoryStorage(work_data_dir)

    async def store_chat_memory(
        self,
        content: str,
        level: MemoryLevel = MemoryLevel.DAILY,
        source: str = "",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMemoryEntry:
        return await self.chat_memory.store(
            content=content,
            level=level,
            source=source,
            importance=importance,
            metadata=metadata,
        )

    async def recall_all_chat_memories(self) -> list[ChatMemoryEntry]:
        return await self.chat_memory.recall_all()

    async def search_chat_memories(
        self,
        query: str,
        levels: list[MemoryLevel] | None = None,
        limit: int = 20,
    ) -> list[ChatMemoryEntry]:
        return await self.chat_memory.search(query, levels, limit)

    async def consolidate_chat_memories(
        self,
        llm_client: Any | None = None,
    ) -> dict[str, MemoryConsolidationResult]:
        results = {}

        daily_result = await self.chat_memory.consolidate_daily_to_weekly(
            llm_client=llm_client
        )
        results["daily_to_weekly"] = daily_result

        weekly_result = await self.chat_memory.consolidate_weekly_to_monthly(
            llm_client=llm_client
        )
        results["weekly_to_monthly"] = weekly_result

        monthly_result = await self.chat_memory.consolidate_monthly_to_quarterly(
            llm_client=llm_client
        )
        results["monthly_to_quarterly"] = monthly_result

        return results

    async def create_project_domain(
        self,
        name: str,
        description: str = "",
        project_path: str = "",
        keywords: list[str] | None = None,
    ) -> ProjectMemoryDomain:
        return await self.work_memory.create_project_domain(
            name=name,
            description=description,
            project_path=project_path,
            keywords=keywords,
        )

    async def match_project_domains(
        self,
        context: str,
        project_path: str | None = None,
    ) -> list[ProjectMemoryDomain]:
        return await self.work_memory.match_project_domains(
            context=context,
            project_path=project_path,
        )

    async def add_project_memory(
        self,
        domain_id: str,
        content: str,
        memory_type: str = "fact",
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ProjectMemoryEntry | None:
        return await self.work_memory.add_project_memory(
            domain_id=domain_id,
            content=content,
            memory_type=memory_type,
            priority=priority,
            importance=importance,
            metadata=metadata,
        )

    async def add_preference(
        self,
        content: str,
        category: str = "general",
        priority: MemoryPriority = MemoryPriority.HIGH,
        importance: float = 0.8,
        metadata: dict[str, Any] | None = None,
    ) -> PreferenceMemory:
        return await self.work_memory.add_preference(
            content=content,
            category=category,
            priority=priority,
            importance=importance,
            metadata=metadata,
        )

    async def cleanup_work_memories(self) -> dict[str, int]:
        expired = await self.work_memory.cleanup_expired_project_memories()
        decayed = await self.work_memory.apply_decay_to_project_memories()

        return {
            "expired_deleted": expired,
            "decayed": decayed,
        }

    def build_system_prompt_context(
        self,
        project_context: str | None = None,
        project_path: str | None = None,
        include_chat_memories: bool = True,
        include_preferences: bool = True,
        include_project_memories: bool = True,
    ) -> str:
        sections = []

        if include_preferences:
            prefs = self.work_memory.format_preferences_for_prompt()
            if prefs:
                sections.append(prefs)

        if include_project_memories and project_context:
            matched_domains = []
            for domain in self.work_memory._project_domains.values():
                score = 0
                context_lower = project_context.lower()

                if project_path and domain.project_path:
                    if project_path == domain.project_path:
                        score += 10
                    elif project_path.startswith(domain.project_path):
                        score += 5

                for keyword in domain.keywords:
                    if keyword.lower() in context_lower:
                        score += 2

                if domain.name.lower() in context_lower:
                    score += 3

                if score > 0:
                    matched_domains.append((domain, score))

            if matched_domains:
                matched_domains.sort(key=lambda x: x[1], reverse=True)
                domain_ids = [d.id for d, _ in matched_domains[:3]]
                proj_mem = self.work_memory.format_project_memories_for_prompt(domain_ids)
                if proj_mem:
                    sections.append(proj_mem)

        if include_chat_memories:
            chat_mem = self.chat_memory.format_for_prompt()
            if chat_mem and chat_mem != "## 聊天记忆":
                sections.append(chat_mem)

        return "\n\n".join(sections)

    def get_statistics(self) -> dict[str, Any]:
        chat_stats = self.chat_memory.get_statistics()
        work_stats = self.work_memory.get_statistics()

        return {
            "chat_memory": chat_stats,
            "work_memory": work_stats,
        }


unified_memory_store = UnifiedMemoryStore()
