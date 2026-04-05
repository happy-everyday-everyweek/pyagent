"""
PyAgent 文档编辑器模块 - 类型定义

定义文档类型和状态枚举。
"""

from enum import Enum


class DocumentType(Enum):
    """文档类型"""
    WORD = "word"
    EXCEL = "excel"
    PPT = "ppt"


class DocumentStatus(Enum):
    """文档状态"""
    DRAFT = "draft"
    EDITING = "editing"
    SAVED = "saved"
    EXPORTED = "exported"


DOCUMENT_EXTENSIONS: dict[DocumentType, str] = {
    DocumentType.WORD: ".docx",
    DocumentType.EXCEL: ".xlsx",
    DocumentType.PPT: ".pptx",
}

DOCUMENT_MIME_TYPES: dict[DocumentType, str] = {
    DocumentType.WORD: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    DocumentType.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    DocumentType.PPT: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
