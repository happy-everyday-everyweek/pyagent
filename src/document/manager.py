"""
PyAgent 文档编辑器模块 - 文档管理器

实现文档的创建、读取、更新、删除和导出功能。
采用单例模式管理所有文档。
支持格式转换、批注管理、修订跟踪等高级功能。
"""

import json
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.document.metadata import DocumentMetadata
from src.document.types import DOCUMENT_EXTENSIONS, DocumentStatus, DocumentType


class DocumentManager:
    """文档管理器（单例模式）

    负责文档的CRUD操作和持久化存储。
    """

    _instance: "DocumentManager | None" = None

    def __new__(cls, data_dir: str = "data/documents") -> "DocumentManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = "data/documents"):
        if self._initialized:
            return

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._documents: dict[str, DocumentMetadata] = {}
        self._storage_file = self.data_dir / "documents.json"

        self._load_documents()
        self._initialized = True

    def _load_documents(self) -> None:
        if self._storage_file.exists():
            try:
                with open(self._storage_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self._documents = {
                        doc_id: DocumentMetadata.from_dict(doc_data)
                        for doc_id, doc_data in data.items()
                    }
            except Exception:
                self._documents = {}

    def _save_documents(self) -> None:
        try:
            with open(self._storage_file, "w", encoding="utf-8") as f:
                json.dump(
                    {doc_id: doc.to_dict() for doc_id, doc in self._documents.items()},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

    def _generate_document_id(self) -> str:
        return f"doc_{uuid.uuid4().hex[:12]}"

    def _get_document_path(self, document_id: str, document_type: DocumentType) -> Path:
        return self.data_dir / f"{document_id}{DOCUMENT_EXTENSIONS[document_type]}"

    def create_document(
        self,
        document_type: DocumentType,
        name: str,
        content: bytes | None = None,
        domain_id: str | None = None,
        author: str = "",
        tags: list[str] | None = None,
    ) -> DocumentMetadata:
        document_id = self._generate_document_id()
        file_path = self._get_document_path(document_id, document_type)

        metadata = DocumentMetadata(
            document_id=document_id,
            document_type=document_type,
            name=name,
            status=DocumentStatus.DRAFT,
            domain_id=domain_id,
            file_path=str(file_path),
            author=author,
            tags=tags or [],
        )

        if content:
            with open(file_path, "wb") as f:
                f.write(content)
            metadata.size = len(content)
            metadata.status = DocumentStatus.SAVED
        else:
            self._create_empty_document(file_path, document_type)

        self._documents[document_id] = metadata
        self._save_documents()

        return metadata

    def _create_empty_document(self, file_path: Path, document_type: DocumentType) -> None:
        templates_dir = Path("config/document_templates")
        template_name = {
            DocumentType.WORD: "empty.docx",
            DocumentType.EXCEL: "empty.xlsx",
            DocumentType.PPT: "empty.pptx",
        }.get(document_type)

        if template_name:
            template_path = templates_dir / template_name
            if template_path.exists():
                shutil.copy(template_path, file_path)
                return

        with open(file_path, "wb") as f:
            f.write(b"")

    def get_document(self, document_id: str) -> DocumentMetadata | None:
        return self._documents.get(document_id)

    def get_document_content(self, document_id: str) -> bytes | None:
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return None

        file_path = Path(metadata.file_path)
        if not file_path.exists():
            return None

        with open(file_path, "rb") as f:
            return f.read()

    def update_document(
        self,
        document_id: str,
        content: bytes | None = None,
        name: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        doc = self._documents.get(document_id)
        if doc is None:
            return False

        if content is not None and doc.file_path:
            with open(doc.file_path, "wb") as f:
                f.write(content)
            doc.size = len(content)
            doc.status = DocumentStatus.SAVED

        if name is not None:
            doc.name = name

        if tags is not None:
            doc.tags = tags

        if metadata is not None:
            doc.metadata.update(metadata)

        doc.increment_version()
        self._save_documents()

        return True

    def delete_document(self, document_id: str) -> bool:
        doc = self._documents.get(document_id)
        if doc is None:
            return False

        if doc.file_path:
            file_path = Path(doc.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass

        del self._documents[document_id]
        self._save_documents()

        return True

    def list_documents(
        self,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        domain_id: str | None = None,
        tags: list[str] | None = None,
    ) -> list[DocumentMetadata]:
        results = list(self._documents.values())

        if document_type is not None:
            results = [d for d in results if d.document_type == document_type]

        if status is not None:
            results = [d for d in results if d.status == status]

        if domain_id is not None:
            results = [d for d in results if d.domain_id == domain_id]

        if tags:
            results = [d for d in results if any(tag in d.tags for tag in tags)]

        results.sort(key=lambda x: x.updated_at, reverse=True)
        return results

    def export_document(
        self,
        document_id: str,
        format: str = "original",
        output_path: str | None = None,
    ) -> str:
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            raise ValueError(f"Document not found: {document_id}")

        source_path = Path(metadata.file_path)
        if not source_path.exists():
            raise ValueError(f"Document file not found: {metadata.file_path}")

        if output_path is None:
            export_dir = self.data_dir / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(export_dir / f"{metadata.name}_{timestamp}{source_path.suffix}")

        shutil.copy(source_path, output_path)

        metadata.status = DocumentStatus.EXPORTED
        metadata.update_timestamp()
        self._save_documents()

        return output_path

    def search_documents(self, query: str) -> list[DocumentMetadata]:
        query_lower = query.lower()
        results = []

        for doc in self._documents.values():
            if (
                query_lower in doc.name.lower()
                or query_lower in doc.author.lower()
                or any(query_lower in tag.lower() for tag in doc.tags)
            ):
                results.append(doc)

        results.sort(key=lambda x: x.updated_at, reverse=True)
        return results

    def get_statistics(self) -> dict[str, Any]:
        total = len(self._documents)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for doc in self._documents.values():
            type_key = doc.document_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            status_key = doc.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

        total_size = sum(doc.size for doc in self._documents.values())

        return {
            "total": total,
            "by_type": by_type,
            "by_status": by_status,
            "total_size": total_size,
        }

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def convert_document(
        self,
        document_id: str,
        target_format: str,
        output_path: str | None = None,
    ) -> str | None:
        """
        转换文档格式。

        支持的转换:
        - docx -> pdf, html, txt
        - pptx -> pdf, html
        - xlsx -> pdf, csv, html
        - pdf -> txt, html

        参数:
            document_id: 文档ID
            target_format: 目标格式 (pdf, html, txt, csv)
            output_path: 输出路径 (可选)

        返回:
            str: 转换后的文件路径，失败返回 None

        示例:
            output = manager.convert_document("doc_xxx", "pdf")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return None

        source_path = Path(metadata.file_path)
        if not source_path.exists():
            return None

        if output_path is None:
            export_dir = self.data_dir / "conversions"
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(export_dir / f"{metadata.name}_{timestamp}.{target_format}")

        output_path = Path(output_path)

        try:
            if target_format == "pdf":
                return self._convert_to_pdf(source_path, output_path)
            if target_format == "html":
                return self._convert_to_html(source_path, output_path)
            if target_format == "txt":
                return self._convert_to_txt(source_path, output_path)
            if target_format == "csv":
                return self._convert_to_csv(source_path, output_path)
            return None
        except Exception as e:
            print(f"转换错误: {e}")
            return None

    def _convert_to_pdf(self, source_path: Path, output_path: Path) -> str | None:
        """使用 LibreOffice 转换为 PDF。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                result = subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        temp_dir,
                        str(source_path),
                    ],
                    capture_output=True,
                    timeout=60,
                    text=True,
                )

                pdf_path = Path(temp_dir) / f"{source_path.stem}.pdf"
                if pdf_path.exists():
                    shutil.copy(pdf_path, output_path)
                    return str(output_path)
                return None
            except FileNotFoundError:
                print("警告: 未找到 LibreOffice (soffice)")
                return None
            except subprocess.TimeoutExpired:
                print("错误: 转换超时")
                return None

    def _convert_to_html(self, source_path: Path, output_path: Path) -> str | None:
        """使用 LibreOffice 转换为 HTML。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                result = subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "html",
                        "--outdir",
                        temp_dir,
                        str(source_path),
                    ],
                    capture_output=True,
                    timeout=60,
                    text=True,
                )

                html_path = Path(temp_dir) / f"{source_path.stem}.html"
                if html_path.exists():
                    shutil.copy(html_path, output_path)
                    return str(output_path)
                return None
            except FileNotFoundError:
                print("警告: 未找到 LibreOffice (soffice)")
                return None
            except subprocess.TimeoutExpired:
                print("错误: 转换超时")
                return None

    def _convert_to_txt(self, source_path: Path, output_path: Path) -> str | None:
        """转换为纯文本。"""
        suffix = source_path.suffix.lower()

        if suffix == ".pdf":
            try:
                import pdfplumber

                text_parts = []
                with pdfplumber.open(source_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)

                output_path.write_text("\n\n".join(text_parts), encoding="utf-8")
                return str(output_path)
            except ImportError:
                print("警告: 未安装 pdfplumber")
                return None
        elif suffix == ".docx":
            try:
                from src.document.docx import DocxEditor

                editor = DocxEditor(source_path)
                text = editor.get_all_text()
                output_path.write_text(text, encoding="utf-8")
                return str(output_path)
            except Exception:
                return None
        else:
            return None

    def _convert_to_csv(self, source_path: Path, output_path: Path) -> str | None:
        """转换为 CSV（仅支持 Excel）。"""
        if source_path.suffix.lower() not in {".xlsx", ".xls"}:
            return None

        try:
            import pandas as pd

            xlsx = pd.ExcelFile(source_path)
            all_dfs = []

            for sheet_name in xlsx.sheet_names:
                df = pd.read_excel(xlsx, sheet_name=sheet_name)
                all_dfs.append(f"# Sheet: {sheet_name}")
                all_dfs.append(df.to_csv(index=False))

            output_path.write_text("\n".join(all_dfs), encoding="utf-8")
            return str(output_path)
        except ImportError:
            print("警告: 未安装 pandas")
            return None

    def get_document_comments(
        self,
        document_id: str,
    ) -> list[dict]:
        """
        获取文档中的批注列表。

        参数:
            document_id: 文档ID

        返回:
            list[dict]: 批注列表，每个元素包含:
                - id: 批注ID
                - author: 作者
                - date: 日期
                - text: 批注内容
                - replies: 回复列表

        示例:
            comments = manager.get_document_comments("doc_xxx")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return []

        if metadata.document_type != DocumentType.WORD:
            return []

        try:
            from src.document.docx import DocxEditor

            editor = DocxEditor(metadata.file_path)
            return editor.get_comments()
        except Exception:
            return []

    def add_document_comment(
        self,
        document_id: str,
        text: str,
        author: str = "System",
        target_text: str | None = None,
    ) -> str | None:
        """
        向文档添加批注。

        参数:
            document_id: 文档ID
            text: 批注内容
            author: 作者 (默认: System)
            target_text: 目标文本 (可选，用于定位批注位置)

        返回:
            str: 批注ID，失败返回 None

        示例:
            comment_id = manager.add_document_comment("doc_xxx", "这是批注内容")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return None

        if metadata.document_type != DocumentType.WORD:
            return None

        try:
            from src.document.docx import DocxEditor

            editor = DocxEditor(metadata.file_path)
            comment_id = editor.add_comment(text, author, target_text)
            editor.save(metadata.file_path)
            return comment_id
        except Exception:
            return None

    def get_document_revisions(
        self,
        document_id: str,
    ) -> list[dict]:
        """
        获取文档中的修订列表。

        参数:
            document_id: 文档ID

        返回:
            list[dict]: 修订列表，每个元素包含:
                - id: 修订ID
                - author: 作者
                - date: 日期
                - type: 类型 (insert/delete)
                - text: 修订内容

        示例:
            revisions = manager.get_document_revisions("doc_xxx")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return []

        if metadata.document_type != DocumentType.WORD:
            return []

        try:
            from src.document.docx import DocxEditor

            editor = DocxEditor(metadata.file_path)
            return editor.get_revisions()
        except Exception:
            return []

    def accept_revision(
        self,
        document_id: str,
        revision_id: str,
    ) -> bool:
        """
        接受指定修订。

        参数:
            document_id: 文档ID
            revision_id: 修订ID

        返回:
            bool: 成功返回 True

        示例:
            manager.accept_revision("doc_xxx", "r_1")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return False

        try:
            from src.document.docx import DocxEditor

            editor = DocxEditor(metadata.file_path)
            result = editor.accept_revision(revision_id)
            if result:
                editor.save(metadata.file_path)
            return result
        except Exception:
            return False

    def reject_revision(
        self,
        document_id: str,
        revision_id: str,
    ) -> bool:
        """
        拒绝指定修订。

        参数:
            document_id: 文档ID
            revision_id: 修订ID

        返回:
            bool: 成功返回 True

        示例:
            manager.reject_revision("doc_xxx", "r_1")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return False

        try:
            from src.document.docx import DocxEditor

            editor = DocxEditor(metadata.file_path)
            result = editor.reject_revision(revision_id)
            if result:
                editor.save(metadata.file_path)
            return result
        except Exception:
            return False

    def create_version_snapshot(
        self,
        document_id: str,
        description: str = "",
    ) -> str | None:
        """
        创建文档版本快照。

        参数:
            document_id: 文档ID
            description: 版本描述

        返回:
            str: 版本ID，失败返回 None

        示例:
            version_id = manager.create_version_snapshot("doc_xxx", "重要修改")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return None

        source_path = Path(metadata.file_path)
        if not source_path.exists():
            return None

        versions_dir = self.data_dir / "versions" / document_id
        versions_dir.mkdir(parents=True, exist_ok=True)

        version_id = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        version_path = versions_dir / f"{version_id}{source_path.suffix}"

        shutil.copy(source_path, version_path)

        version_info = {
            "version_id": version_id,
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "size": version_path.stat().st_size,
        }

        version_info_path = versions_dir / f"{version_id}.json"
        with open(version_info_path, "w", encoding="utf-8") as f:
            json.dump(version_info, f, ensure_ascii=False, indent=2)

        return version_id

    def list_versions(
        self,
        document_id: str,
    ) -> list[dict]:
        """
        列出文档的所有版本。

        参数:
            document_id: 文档ID

        返回:
            list[dict]: 版本列表

        示例:
            versions = manager.list_versions("doc_xxx")
        """
        versions_dir = self.data_dir / "versions" / document_id
        if not versions_dir.exists():
            return []

        versions = []
        for version_file in versions_dir.glob("v_*.json"):
            try:
                with open(version_file, encoding="utf-8") as f:
                    versions.append(json.load(f))
            except Exception:
                pass

        versions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return versions

    def restore_version(
        self,
        document_id: str,
        version_id: str,
    ) -> bool:
        """
        恢复到指定版本。

        参数:
            document_id: 文档ID
            version_id: 版本ID

        返回:
            bool: 成功返回 True

        示例:
            manager.restore_version("doc_xxx", "v_20240101_120000")
        """
        metadata = self.get_document(document_id)
        if metadata is None or metadata.file_path is None:
            return False

        versions_dir = self.data_dir / "versions" / document_id
        version_info_path = versions_dir / f"{version_id}.json"

        if not version_info_path.exists():
            return False

        try:
            with open(version_info_path, encoding="utf-8") as f:
                version_info = json.load(f)
        except Exception:
            return False

        source_path = Path(metadata.file_path)
        version_path = versions_dir / f"{version_id}{source_path.suffix}"

        if not version_path.exists():
            return False

        shutil.copy(version_path, source_path)

        metadata.increment_version()
        metadata.update_timestamp()
        self._save_documents()

        return True


document_manager = DocumentManager()
