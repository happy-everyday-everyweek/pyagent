"""Document conversion and versioning system."""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DocumentVersion:
    version_id: str
    document_id: str
    version_number: int
    created_at: datetime
    created_by: str = ""
    changes: str = ""
    file_path: str = ""
    size_bytes: int = 0
    checksum: str = ""


@dataclass
class Document:
    id: str
    name: str
    format: str
    current_version: int = 1
    versions: list[DocumentVersion] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentConverter:
    """Convert documents between formats."""

    SUPPORTED_CONVERSIONS = {
        "docx": ["pdf", "html", "txt", "md"],
        "pdf": ["docx", "txt", "html", "png"],
        "xlsx": ["csv", "pdf", "html"],
        "pptx": ["pdf", "png", "html"],
        "html": ["pdf", "docx", "txt"],
        "md": ["pdf", "html", "docx"],
        "txt": ["pdf", "html", "docx"],
    }

    def __init__(self, libreoffice_path: str | None = None):
        self._libreoffice_path = libreoffice_path or self._find_libreoffice()

    def _find_libreoffice(self) -> str | None:
        paths = [
            "libreoffice",
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
        ]
        for path in paths:
            if shutil.which(path):
                return path
        return None

    def can_convert(self, source_format: str, target_format: str) -> bool:
        source = source_format.lower().lstrip(".")
        target = target_format.lower().lstrip(".")
        return target in self.SUPPORTED_CONVERSIONS.get(source, [])

    async def convert(
        self,
        source_path: str,
        target_format: str,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        source = Path(source_path)
        if not source.exists():
            return {"success": False, "error": f"Source file not found: {source_path}"}

        source_format = source.suffix.lower().lstrip(".")
        target = target_format.lower().lstrip(".")

        if not self.can_convert(source_format, target):
            return {"success": False, "error": f"Cannot convert {source_format} to {target}"}

        if output_path is None:
            output_path = str(source.with_suffix(f".{target}"))

        try:
            if source_format == "md" and target in ["html", "pdf"]:
                result = await self._convert_markdown(source_path, output_path, target)
            elif source_format == "txt" and target in ["html", "pdf"]:
                result = await self._convert_text(source_path, output_path, target)
            elif self._libreoffice_path:
                result = await self._convert_with_libreoffice(source_path, output_path, target)
            else:
                return {"success": False, "error": "No converter available"}

            return {"success": True, "output_path": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _convert_markdown(self, source: str, output: str, target: str) -> str:
        with open(source, encoding="utf-8") as f:
            content = f.read()

        if target == "html":
            try:
                import markdown

                html = markdown.markdown(content, extensions=["tables", "fenced_code"])
                with open(output, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html><body>{html}</body></html>")
                return output
            except ImportError:
                html = f"<html><body><pre>{content}</pre></body></html>"
                with open(output, "w", encoding="utf-8") as f:
                    f.write(html)
                return output

        return output

    async def _convert_text(self, source: str, output: str, target: str) -> str:
        with open(source, encoding="utf-8") as f:
            content = f.read()

        if target == "html":
            html = f"<html><body><pre>{content}</pre></body></html>"
            with open(output, "w", encoding="utf-8") as f:
                f.write(html)
            return output

        return output

    async def _convert_with_libreoffice(self, source: str, output: str, target: str) -> str:
        import asyncio

        output_dir = str(Path(output).parent)
        cmd = [
            self._libreoffice_path,
            "--headless",
            "--convert-to",
            target,
            "--outdir",
            output_dir,
            source,
        ]

        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()

        expected_output = str(Path(output_dir) / f"{Path(source).stem}.{target}")
        if Path(expected_output).exists():
            if expected_output != output:
                shutil.move(expected_output, output)
            return output

        raise RuntimeError("Conversion failed")


class DocumentVersionControl:
    """Version control for documents."""

    def __init__(self, storage_path: str = "data/documents"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._documents: dict[str, Document] = {}
        self._load_documents()

    def _load_documents(self) -> None:
        index_file = self._storage_path / "index.json"
        if not index_file.exists():
            return

        with open(index_file, encoding="utf-8") as f:
            data = json.load(f)

        for doc_data in data.get("documents", []):
            versions = [
                DocumentVersion(
                    version_id=v["version_id"],
                    document_id=v["document_id"],
                    version_number=v["version_number"],
                    created_at=datetime.fromisoformat(v["created_at"]),
                    created_by=v.get("created_by", ""),
                    changes=v.get("changes", ""),
                    file_path=v.get("file_path", ""),
                    size_bytes=v.get("size_bytes", 0),
                    checksum=v.get("checksum", ""),
                )
                for v in doc_data.get("versions", [])
            ]

            doc = Document(
                id=doc_data["id"],
                name=doc_data["name"],
                format=doc_data["format"],
                current_version=doc_data.get("current_version", 1),
                versions=versions,
                created_at=datetime.fromisoformat(doc_data["created_at"]) if "created_at" in doc_data else datetime.now(),
                updated_at=datetime.fromisoformat(doc_data["updated_at"]) if "updated_at" in doc_data else datetime.now(),
                metadata=doc_data.get("metadata", {}),
            )
            self._documents[doc.id] = doc

    def _save_documents(self) -> None:
        index_file = self._storage_path / "index.json"
        data = {
            "documents": [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "format": doc.format,
                    "current_version": doc.current_version,
                    "versions": [
                        {
                            "version_id": v.version_id,
                            "document_id": v.document_id,
                            "version_number": v.version_number,
                            "created_at": v.created_at.isoformat(),
                            "created_by": v.created_by,
                            "changes": v.changes,
                            "file_path": v.file_path,
                            "size_bytes": v.size_bytes,
                            "checksum": v.checksum,
                        }
                        for v in doc.versions
                    ],
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat(),
                    "metadata": doc.metadata,
                }
                for doc in self._documents.values()
            ]
        }
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_document(self, name: str, source_path: str, created_by: str = "") -> Document:
        import hashlib
        import uuid

        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        doc_id = str(uuid.uuid4())
        doc_format = source.suffix.lower().lstrip(".")

        doc_dir = self._storage_path / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        file_content = source.read_bytes()
        checksum = hashlib.sha256(file_content).hexdigest()[:16]
        dest_path = doc_dir / f"v1_{source.name}"
        shutil.copy2(source, dest_path)

        version = DocumentVersion(
            version_id=str(uuid.uuid4()),
            document_id=doc_id,
            version_number=1,
            created_at=datetime.now(),
            created_by=created_by,
            file_path=str(dest_path),
            size_bytes=len(file_content),
            checksum=checksum,
        )

        doc = Document(
            id=doc_id,
            name=name,
            format=doc_format,
            current_version=1,
            versions=[version],
        )

        self._documents[doc_id] = doc
        self._save_documents()

        logger.info("Created document: %s (v1)", name)
        return doc

    def create_version(self, document_id: str, source_path: str, changes: str = "", created_by: str = "") -> DocumentVersion | None:
        import hashlib
        import uuid

        doc = self._documents.get(document_id)
        if not doc:
            return None

        source = Path(source_path)
        if not source.exists():
            return None

        new_version = doc.current_version + 1
        doc_dir = self._storage_path / document_id

        file_content = source.read_bytes()
        checksum = hashlib.sha256(file_content).hexdigest()[:16]
        dest_path = doc_dir / f"v{new_version}_{source.name}"
        shutil.copy2(source, dest_path)

        version = DocumentVersion(
            version_id=str(uuid.uuid4()),
            document_id=document_id,
            version_number=new_version,
            created_at=datetime.now(),
            created_by=created_by,
            changes=changes,
            file_path=str(dest_path),
            size_bytes=len(file_content),
            checksum=checksum,
        )

        doc.versions.append(version)
        doc.current_version = new_version
        doc.updated_at = datetime.now()
        self._save_documents()

        logger.info("Created version %d for document: %s", new_version, doc.name)
        return version

    def get_version(self, document_id: str, version_number: int | None = None) -> DocumentVersion | None:
        doc = self._documents.get(document_id)
        if not doc:
            return None

        target_version = version_number or doc.current_version
        for version in doc.versions:
            if version.version_number == target_version:
                return version
        return None

    def restore_version(self, document_id: str, version_number: int) -> bool:
        doc = self._documents.get(document_id)
        if not doc:
            return False

        version = self.get_version(document_id, version_number)
        if not version:
            return False

        source_path = Path(version.file_path)
        if not source_path.exists():
            return False

        return self.create_version(
            document_id,
            str(source_path),
            changes=f"Restored from version {version_number}",
        ) is not None

    def get_document(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    def list_documents(self, format: str | None = None) -> list[Document]:
        docs = list(self._documents.values())
        if format:
            docs = [d for d in docs if d.format == format.lower().lstrip(".")]
        return docs

    def delete_document(self, document_id: str) -> bool:
        if document_id not in self._documents:
            return False

        doc_dir = self._storage_path / document_id
        if doc_dir.exists():
            shutil.rmtree(doc_dir)

        del self._documents[document_id]
        self._save_documents()
        return True

    def compare_versions(self, document_id: str, version1: int, version2: int) -> dict[str, Any]:
        v1 = self.get_version(document_id, version1)
        v2 = self.get_version(document_id, version2)

        if not v1 or not v2:
            return {"error": "Version not found"}

        return {
            "version1": {"number": v1.version_number, "size": v1.size_bytes, "checksum": v1.checksum, "created_at": v1.created_at.isoformat()},
            "version2": {"number": v2.version_number, "size": v2.size_bytes, "checksum": v2.checksum, "created_at": v2.created_at.isoformat()},
            "size_diff": v2.size_bytes - v1.size_bytes,
            "same_content": v1.checksum == v2.checksum,
        }
