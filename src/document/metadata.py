"""
PyAgent 文档编辑器模块 - 文档元数据

定义文档元数据数据类。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.document.types import DocumentStatus, DocumentType


@dataclass
class DocumentMetadata:
    """文档元数据"""
    document_id: str
    document_type: DocumentType
    name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: DocumentStatus = DocumentStatus.DRAFT
    version: int = 1
    domain_id: str | None = None
    file_path: str | None = None
    size: int = 0
    author: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "version": self.version,
            "domain_id": self.domain_id,
            "file_path": self.file_path,
            "size": self.size,
            "author": self.author,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentMetadata":
        return cls(
            document_id=data["document_id"],
            document_type=DocumentType(data.get("document_type", "word")),
            name=data["name"],
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            status=DocumentStatus(data.get("status", "draft")),
            version=data.get("version", 1),
            domain_id=data.get("domain_id"),
            file_path=data.get("file_path"),
            size=data.get("size", 0),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now().isoformat()

    def increment_version(self) -> None:
        self.version += 1
        self.update_timestamp()
