"""
PyAgent OOXML 工具模块

提供 OOXML 文档的底层操作工具，包括打包、解包、验证等功能。
支持 DOCX、PPTX、XLSX 等 Office 文档格式。

主要功能:
- 打包工具: 将解压后的目录打包为 Office 文档
- 解包工具: 将 Office 文档解压为 XML 文件
- 验证工具: 验证文档的 XML 模式合规性
- XML 编辑器: 提供底层 XML 操作能力
"""

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document
from src.document.ooxml.validate import validate_document

__all__ = [
    "pack_document",
    "unpack_document",
    "validate_document",
]
