"""Knowledge base system for PyAgent.

This module provides LPMM (Long-term Personal Memory Management)
functionality for storing and retrieving knowledge.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """A single knowledge entry."""

    id: str
    content: str
    source: str
    category: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    relevance_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            category=data["category"],
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            access_count=data.get("access_count", 0),
            relevance_score=data.get("relevance_score", 0.0),
        )


class KnowledgeIndex:
    """Inverted index for knowledge search."""

    def __init__(self):
        self._index: dict[str, set[str]] = {}
        self._entries: dict[str, KnowledgeEntry] = {}

    def add(self, entry: KnowledgeEntry) -> None:
        self._entries[entry.id] = entry
        tokens = self._tokenize(entry.content)
        for token in tokens:
            if token not in self._index:
                self._index[token] = set()
            self._index[token].add(entry.id)

    def remove(self, entry_id: str) -> None:
        if entry_id not in self._entries:
            return
        entry = self._entries[entry_id]
        tokens = self._tokenize(entry.content)
        for token in tokens:
            if token in self._index:
                self._index[token].discard(entry_id)
        del self._entries[entry_id]

    def search(self, query: str, limit: int = 10) -> list[KnowledgeEntry]:
        tokens = self._tokenize(query)
        entry_scores: dict[str, float] = {}

        for token in tokens:
            if token in self._index:
                for entry_id in self._index[token]:
                    entry_scores[entry_id] = entry_scores.get(entry_id, 0) + 1

        sorted_ids = sorted(entry_scores.keys(), key=lambda x: entry_scores[x], reverse=True)[:limit]
        return [self._entries[eid] for eid in sorted_ids if eid in self._entries]

    def _tokenize(self, text: str) -> set[str]:
        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)
        return set(t for t in tokens if len(t) > 2)


class KnowledgeBase:
    """Knowledge base manager with LPMM support."""

    def __init__(self, storage_path: str = "data/knowledge"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._index = KnowledgeIndex()
        self._categories: dict[str, list[str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        for category_file in self._storage_path.glob("*.json"):
            with open(category_file, encoding="utf-8") as f:
                data = json.load(f)
                for entry_data in data.get("entries", []):
                    entry = KnowledgeEntry.from_dict(entry_data)
                    self._index.add(entry)
                    if entry.category not in self._categories:
                        self._categories[entry.category] = []
                    self._categories[entry.category].append(entry.id)

    def add_entry(
        self,
        content: str,
        source: str,
        category: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeEntry:
        import uuid

        entry = KnowledgeEntry(
            id=str(uuid.uuid4()),
            content=content,
            source=source,
            category=category,
            tags=tags or [],
            metadata=metadata or {},
        )
        self._index.add(entry)

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(entry.id)

        self._save_category(category)
        logger.info("Added knowledge entry: %s", entry.id)
        return entry

    def update_entry(self, entry_id: str, **kwargs: Any) -> KnowledgeEntry | None:
        entry = self._index._entries.get(entry_id)
        if not entry:
            return None

        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        entry.updated_at = datetime.now()

        self._save_category(entry.category)
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        entry = self._index._entries.get(entry_id)
        if not entry:
            return False

        category = entry.category
        self._index.remove(entry_id)

        if category in self._categories and entry_id in self._categories[category]:
            self._categories[category].remove(entry_id)

        self._save_category(category)
        return True

    def search(self, query: str, limit: int = 10) -> list[KnowledgeEntry]:
        results = self._index.search(query, limit)
        for entry in results:
            entry.access_count += 1
        return results

    def get_by_category(self, category: str) -> list[KnowledgeEntry]:
        entry_ids = self._categories.get(category, [])
        return [self._index._entries[eid] for eid in entry_ids if eid in self._index._entries]

    def get_by_tags(self, tags: list[str]) -> list[KnowledgeEntry]:
        results = []
        for entry in self._index._entries.values():
            if any(tag in entry.tags for tag in tags):
                results.append(entry)
        return results

    def get_entry(self, entry_id: str) -> KnowledgeEntry | None:
        return self._index._entries.get(entry_id)

    def list_categories(self) -> list[str]:
        return list(self._categories.keys())

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_entries": len(self._index._entries),
            "total_categories": len(self._categories),
            "categories": {cat: len(ids) for cat, ids in self._categories.items()},
        }

    def _save_category(self, category: str) -> None:
        entries = self.get_by_category(category)
        data = {
            "category": category,
            "entries": [e.to_dict() for e in entries],
            "updated_at": datetime.now().isoformat(),
        }
        filepath = self._storage_path / f"{category}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


_knowledge_base: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
