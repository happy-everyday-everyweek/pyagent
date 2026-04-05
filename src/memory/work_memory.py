"""
PyAgent 记忆系统 - 工作智能体记忆存储

实现工作智能体记忆：
- 项目记忆：创建项目记忆域，任务时匹配对应项目记忆域
- 偏好记忆：每次都加入到系统提示词中

参考OpenAkita的记忆删除机制
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .types import (
    MemoryPriority,
    PreferenceMemory,
    ProjectMemoryDomain,
    ProjectMemoryEntry,
)


class WorkMemoryStorage:
    """工作智能体记忆存储"""

    def __init__(self, data_dir: str = "data/memory/work"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._project_domains: dict[str, ProjectMemoryDomain] = {}
        self._preferences: dict[str, PreferenceMemory] = {}

        self._load_memories()

    def _get_project_file(self) -> Path:
        return self.data_dir / "project_memories.json"

    def _get_preference_file(self) -> Path:
        return self.data_dir / "preferences.json"

    def _load_memories(self) -> None:
        project_file = self._get_project_file()
        if project_file.exists():
            try:
                with open(project_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("domains", []):
                        domain = ProjectMemoryDomain.from_dict(item)
                        self._project_domains[domain.id] = domain
            except Exception:
                pass

        preference_file = self._get_preference_file()
        if preference_file.exists():
            try:
                with open(preference_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("preferences", []):
                        pref = PreferenceMemory.from_dict(item)
                        self._preferences[pref.id] = pref
            except Exception:
                pass

    def _save_project_memories(self) -> None:
        file_path = self._get_project_file()
        try:
            data = {
                "domains": [d.to_dict() for d in self._project_domains.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_preferences(self) -> None:
        file_path = self._get_preference_file()
        try:
            data = {
                "preferences": [p.to_dict() for p in self._preferences.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_domain_id(self) -> str:
        return f"domain_{uuid.uuid4().hex[:12]}"

    def _generate_memory_id(self) -> str:
        return f"proj_mem_{uuid.uuid4().hex[:12]}"

    def _generate_preference_id(self) -> str:
        return f"pref_{uuid.uuid4().hex[:12]}"

    async def create_project_domain(
        self,
        name: str,
        description: str = "",
        project_path: str = "",
        keywords: list[str] | None = None,
    ) -> ProjectMemoryDomain:
        domain = ProjectMemoryDomain(
            id=self._generate_domain_id(),
            name=name,
            description=description,
            project_path=project_path,
            keywords=keywords or [],
        )

        self._project_domains[domain.id] = domain
        self._save_project_memories()

        return domain

    async def get_project_domain(self, domain_id: str) -> ProjectMemoryDomain | None:
        return self._project_domains.get(domain_id)

    async def list_project_domains(self) -> list[ProjectMemoryDomain]:
        return list(self._project_domains.values())

    async def match_project_domains(
        self,
        context: str,
        project_path: str | None = None,
    ) -> list[ProjectMemoryDomain]:
        matched = []
        context_lower = context.lower()

        for domain in self._project_domains.values():
            score = 0

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

            if domain.description and domain.description.lower() in context_lower:
                score += 1

            if score > 0:
                matched.append((domain, score))

        matched.sort(key=lambda x: x[1], reverse=True)
        return [d for d, _ in matched]

    async def add_project_memory(
        self,
        domain_id: str,
        content: str,
        memory_type: str = "fact",
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ProjectMemoryEntry | None:
        domain = self._project_domains.get(domain_id)
        if not domain:
            return None

        entry = ProjectMemoryEntry(
            id=self._generate_memory_id(),
            domain_id=domain_id,
            content=content,
            memory_type=memory_type,
            priority=priority,
            importance=importance,
            metadata=metadata or {},
        )

        domain.memories.append(entry)
        domain.updated_at = datetime.now().timestamp()
        self._save_project_memories()

        return entry

    async def get_project_memories(
        self,
        domain_id: str,
        memory_type: str | None = None,
    ) -> list[ProjectMemoryEntry]:
        domain = self._project_domains.get(domain_id)
        if not domain:
            return []

        memories = domain.memories
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        return memories

    async def update_project_memory(
        self,
        memory_id: str,
        updates: dict[str, Any],
    ) -> bool:
        for domain in self._project_domains.values():
            for mem in domain.memories:
                if mem.id == memory_id:
                    for key, value in updates.items():
                        if hasattr(mem, key):
                            setattr(mem, key, value)
                    domain.updated_at = datetime.now().timestamp()
                    self._save_project_memories()
                    return True
        return False

    async def delete_project_memory(self, memory_id: str) -> bool:
        for domain in self._project_domains.values():
            for i, mem in enumerate(domain.memories):
                if mem.id == memory_id:
                    domain.memories.pop(i)
                    domain.updated_at = datetime.now().timestamp()
                    self._save_project_memories()
                    return True
        return False

    async def delete_project_domain(self, domain_id: str) -> bool:
        if domain_id in self._project_domains:
            del self._project_domains[domain_id]
            self._save_project_memories()
            return True
        return False

    async def cleanup_expired_project_memories(self) -> int:
        now = datetime.now().timestamp()
        deleted = 0

        for domain in self._project_domains.values():
            original_count = len(domain.memories)
            domain.memories = [
                m for m in domain.memories
                if m.expires_at is None or m.expires_at > now
            ]
            deleted += original_count - len(domain.memories)

        if deleted > 0:
            self._save_project_memories()

        return deleted

    async def apply_decay_to_project_memories(self) -> int:
        now = datetime.now().timestamp()
        decayed = 0

        for domain in self._project_domains.values():
            for mem in domain.memories:
                if mem.priority == MemoryPriority.PERMANENT:
                    continue

                if mem.last_accessed_at:
                    days_since = (now - mem.last_accessed_at) / 86400
                    decay_factor = (1 - mem.decay_rate) ** days_since
                    effective_score = mem.importance * decay_factor

                    if effective_score < 0.1 and mem.access_count < 3:
                        await self.delete_project_memory(mem.id)
                        decayed += 1
                    elif effective_score < 0.3:
                        mem.priority = MemoryPriority.LOW
                        mem.importance = effective_score
                        decayed += 1

        if decayed > 0:
            self._save_project_memories()

        return decayed

    async def add_preference(
        self,
        content: str,
        category: str = "general",
        priority: MemoryPriority = MemoryPriority.HIGH,
        importance: float = 0.8,
        metadata: dict[str, Any] | None = None,
    ) -> PreferenceMemory:
        pref = PreferenceMemory(
            id=self._generate_preference_id(),
            content=content,
            category=category,
            priority=priority,
            importance=importance,
            metadata=metadata or {},
        )

        self._preferences[pref.id] = pref
        self._save_preferences()

        return pref

    async def get_preference(self, pref_id: str) -> PreferenceMemory | None:
        pref = self._preferences.get(pref_id)
        if pref:
            pref.access_count += 1
            self._save_preferences()
        return pref

    async def list_preferences(
        self,
        category: str | None = None,
    ) -> list[PreferenceMemory]:
        prefs = list(self._preferences.values())
        if category:
            prefs = [p for p in prefs if p.category == category]
        return prefs

    async def update_preference(
        self,
        pref_id: str,
        updates: dict[str, Any],
    ) -> bool:
        pref = self._preferences.get(pref_id)
        if pref:
            for key, value in updates.items():
                if hasattr(pref, key):
                    setattr(pref, key, value)
            self._save_preferences()
            return True
        return False

    async def delete_preference(self, pref_id: str) -> bool:
        if pref_id in self._preferences:
            del self._preferences[pref_id]
            self._save_preferences()
            return True
        return False

    def format_preferences_for_prompt(self) -> str:
        if not self._preferences:
            return ""

        lines = ["## 用户偏好"]

        by_category: dict[str, list[PreferenceMemory]] = {}
        for pref in self._preferences.values():
            if pref.category not in by_category:
                by_category[pref.category] = []
            by_category[pref.category].append(pref)

        category_names = {
            "general": "通用偏好",
            "coding": "编码偏好",
            "communication": "沟通偏好",
            "workflow": "工作流偏好",
        }

        for category, prefs in by_category.items():
            name = category_names.get(category, category)
            lines.append(f"\n### {name}")
            prefs.sort(key=lambda x: x.importance, reverse=True)
            for pref in prefs:
                lines.append(f"- {pref.content}")

        return "\n".join(lines)

    def format_project_memories_for_prompt(
        self,
        domain_ids: list[str] | None = None,
    ) -> str:
        if not self._project_domains:
            return ""

        lines = ["## 项目记忆"]

        domains = []
        if domain_ids:
            for did in domain_ids:
                if did in self._project_domains:
                    domains.append(self._project_domains[did])
        else:
            domains = list(self._project_domains.values())

        for domain in domains:
            lines.append(f"\n### {domain.name}")
            if domain.description:
                lines.append(f"描述: {domain.description}")

            memories = sorted(
                domain.memories,
                key=lambda x: (x.priority.value, x.importance),
                reverse=True,
            )

            for mem in memories[:20]:
                lines.append(f"- [{mem.memory_type}] {mem.content}")

        return "\n".join(lines)

    def get_statistics(self) -> dict[str, Any]:
        total_project_memories = sum(
            len(d.memories) for d in self._project_domains.values()
        )

        return {
            "project_domains": len(self._project_domains),
            "project_memories": total_project_memories,
            "preferences": len(self._preferences),
        }


work_memory_storage = WorkMemoryStorage()
