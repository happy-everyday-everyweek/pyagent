"""
PyAgent DOCX 文档处理模块

提供 Word 文档的创建、编辑、批注、修订跟踪和格式转换功能。
支持 OOXML 标准的完整操作。

主要功能:
- 文档编辑器: 基于 XML 的底层编辑能力
- 批注管理: 添加、回复、删除批注
- 修订跟踪: 跟踪文档修改历史
- 格式转换: 支持多种格式互转
- 文档创建: 从模板创建新文档
"""

from src.document.docx.comment import CommentManager
from src.document.docx.converter import DocxConverter
from src.document.docx.creator import DocxCreator
from src.document.docx.editor import Document, DocxXMLEditor
from src.document.docx.revision import RevisionManager
from src.document.docx.utilities import XMLEditor

__all__ = [
    "CommentManager",
    "Document",
    "DocxConverter",
    "DocxCreator",
    "DocxXMLEditor",
    "RevisionManager",
    "XMLEditor",
]
