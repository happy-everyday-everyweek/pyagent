"""
PyAgent 文档编辑器模块

实现文档创建、编辑、分析和AI辅助功能。
支持Word、Excel、PPT、PDF四种文档类型。
集成ONLYOFFICE Docs服务进行在线编辑。

模块结构:
- manager: 文档管理器（CRUD、格式转换、版本管理）
- docx: Word文档处理（创建、编辑、批注、修订）
- xlsx: Excel处理（创建、编辑、工作表管理、图表）
- pptx: PowerPoint处理（创建、编辑、幻灯片管理、缩略图）
- pdf: PDF处理（提取、合并、拆分、表单、OCR）
- ooxml: OOXML工具（打包、解包、验证）
"""

from src.document.connector import OnlyOfficeConnector
from src.document.docx import (
    CommentManager,
    Document,
    DocxConverter,
    DocxCreator,
    DocxXMLEditor,
    RevisionManager,
    XMLEditor,
)
from src.document.manager import DocumentManager
from src.document.metadata import DocumentMetadata
from src.document.ooxml import (
    pack_document,
    unpack_document,
    validate_document,
)
from src.document.pdf import (
    FormFieldInfo,
    PDFExtractor,
    PDFFormFiller,
    PDFMerger,
    PDFOCRProcessor,
    PDFSplitter,
    TableExtractor,
    TextExtractor,
)
from src.document.pptx import (
    PptxCreator,
    PptxEditor,
    SlideManager,
    ThumbnailGenerator,
)
from src.document.tools import DocumentTool
from src.document.types import DocumentStatus, DocumentType
from src.document.xlsx import (
    ChartManager,
    SheetManager,
    XlsxCreator,
    XlsxEditor,
)

__all__ = [
    "ChartManager",
    "CommentManager",
    "Document",
    "DocumentManager",
    "DocumentMetadata",
    "DocumentStatus",
    "DocumentTool",
    "DocumentType",
    "DocxConverter",
    "DocxCreator",
    "DocxXMLEditor",
    "FormFieldInfo",
    "OnlyOfficeConnector",
    "PDFExtractor",
    "PDFFormFiller",
    "PDFMerger",
    "PDFOCRProcessor",
    "PDFSplitter",
    "PptxCreator",
    "PptxEditor",
    "RevisionManager",
    "SheetManager",
    "SlideManager",
    "TableExtractor",
    "TextExtractor",
    "ThumbnailGenerator",
    "XMLEditor",
    "XlsxCreator",
    "XlsxEditor",
    "pack_document",
    "unpack_document",
    "validate_document",
]
