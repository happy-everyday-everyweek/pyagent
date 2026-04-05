"""
PyAgent 文档模块 - PDF文本和表格提取器

使用pdfplumber实现PDF文档的文本和表格提取功能。
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """文本块数据结构"""
    x: float
    y: float
    width: float
    height: float
    text: str
    font_name: str = ""
    font_size: float = 0.0


@dataclass
class TableData:
    """表格数据结构"""
    page_num: int
    bbox: tuple[float, float, float, float]
    rows: int
    cols: int
    data: list[list[str]]


@dataclass
class ExtractionResult:
    """提取结果数据结构"""
    text: str
    text_by_page: dict[int, str]
    tables: list[TableData]
    blocks: list[TextBlock]
    metadata: dict[str, Any]


class TextExtractor:
    """PDF文本提取器"""

    def __init__(self):
        self._pdfplumber_available = self._check_pdfplumber()

    def _check_pdfplumber(self) -> bool:
        try:
            import pdfplumber
            return True
        except ImportError:
            logger.warning("pdfplumber未安装，文本提取功能不可用")
            return False

    def extract_text(self, pdf_path: str, pages: list[int] | None = None) -> str:
        """
        提取PDF文本内容
        
        Args:
            pdf_path: PDF文件路径
            pages: 要提取的页码列表，None表示提取所有页
            
        Returns:
            提取的文本内容
        """
        if not self._pdfplumber_available:
            logger.error("pdfplumber未安装")
            return ""

        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                page_indices = pages if pages else range(len(pdf.pages))

                for page_idx in page_indices:
                    if 0 <= page_idx < len(pdf.pages):
                        page = pdf.pages[page_idx]
                        page_text = page.extract_text() or ""
                        text_parts.append(page_text)

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            return ""

    def extract_text_by_page(self, pdf_path: str) -> dict[int, str]:
        """
        按页提取PDF文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            页码到文本的映射字典
        """
        if not self._pdfplumber_available:
            logger.error("pdfplumber未安装")
            return {}

        try:
            import pdfplumber

            result = {}
            with pdfplumber.open(pdf_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    result[page_idx + 1] = page_text

            return result
        except Exception as e:
            logger.error(f"按页提取文本失败: {e}")
            return {}

    def extract_blocks(self, pdf_path: str, page_num: int) -> list[TextBlock]:
        """
        提取指定页的文本块
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页码（从1开始）
            
        Returns:
            文本块列表
        """
        if not self._pdfplumber_available:
            logger.error("pdfplumber未安装")
            return []

        try:
            import pdfplumber

            blocks = []
            with pdfplumber.open(pdf_path) as pdf:
                if 0 < page_num <= len(pdf.pages):
                    page = pdf.pages[page_num - 1]
                    chars = page.chars

                    if not chars:
                        return blocks

                    current_block = []
                    current_y = None
                    y_tolerance = 2.0

                    for char in chars:
                        if current_y is None:
                            current_y = char["top"]
                            current_block.append(char)
                        elif abs(char["top"] - current_y) <= y_tolerance:
                            current_block.append(char)
                        else:
                            if current_block:
                                block = self._create_text_block(current_block)
                                if block:
                                    blocks.append(block)

                            current_block = [char]
                            current_y = char["top"]

                    if current_block:
                        block = self._create_text_block(current_block)
                        if block:
                            blocks.append(block)

            return blocks
        except Exception as e:
            logger.error(f"提取文本块失败: {e}")
            return []

    def _create_text_block(self, chars: list[dict]) -> TextBlock | None:
        """从字符列表创建文本块"""
        if not chars:
            return None

        text = "".join([c["text"] for c in chars])
        x0 = min([c["x0"] for c in chars])
        y0 = min([c["top"] for c in chars])
        x1 = max([c["x1"] for c in chars])
        y1 = max([c["bottom"] for c in chars])

        return TextBlock(
            x=x0,
            y=y0,
            width=x1 - x0,
            height=y1 - y0,
            text=text,
            font_name=chars[0].get("fontname", ""),
            font_size=chars[0].get("size", 0.0),
        )


class TableExtractor:
    """PDF表格提取器"""

    def __init__(self):
        self._pdfplumber_available = self._check_pdfplumber()

    def _check_pdfplumber(self) -> bool:
        try:
            import pdfplumber
            return True
        except ImportError:
            logger.warning("pdfplumber未安装，表格提取功能不可用")
            return False

    def extract_tables(self, pdf_path: str, pages: list[int] | None = None) -> list[TableData]:
        """
        提取PDF表格
        
        Args:
            pdf_path: PDF文件路径
            pages: 要提取的页码列表，None表示提取所有页
            
        Returns:
            表格数据列表
        """
        if not self._pdfplumber_available:
            logger.error("pdfplumber未安装")
            return []

        try:
            import pdfplumber

            tables = []
            with pdfplumber.open(pdf_path) as pdf:
                page_indices = pages if pages else range(len(pdf.pages))

                for page_idx in page_indices:
                    if 0 <= page_idx < len(pdf.pages):
                        page = pdf.pages[page_idx]
                        page_tables = page.extract_tables()

                        for table_data in page_tables:
                            if table_data:
                                bbox = page.bbox if page.bbox else (0, 0, page.width, page.height)
                                rows = len(table_data)
                                cols = len(table_data[0]) if table_data else 0

                                tables.append(TableData(
                                    page_num=page_idx + 1,
                                    bbox=bbox,
                                    rows=rows,
                                    cols=cols,
                                    data=table_data,
                                ))

            logger.info(f"成功提取 {len(tables)} 个表格")
            return tables
        except Exception as e:
            logger.error(f"提取表格失败: {e}")
            return []

    def extract_tables_to_dataframe(self, pdf_path: str, pages: list[int] | None = None) -> list[Any]:
        """
        提取PDF表格并转换为pandas DataFrame
        
        Args:
            pdf_path: PDF文件路径
            pages: 要提取的页码列表，None表示提取所有页
            
        Returns:
            DataFrame列表
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas未安装，无法转换为DataFrame")
            return []

        tables = self.extract_tables(pdf_path, pages)
        dataframes = []

        for table in tables:
            if table.data and len(table.data) > 1:
                df = pd.DataFrame(table.data[1:], columns=table.data[0])
                dataframes.append(df)

        return dataframes

    def save_tables_to_excel(self, pdf_path: str, output_path: str, pages: list[int] | None = None) -> bool:
        """
        提取PDF表格并保存为Excel文件
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出Excel文件路径
            pages: 要提取的页码列表，None表示提取所有页
            
        Returns:
            是否成功
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas未安装，无法保存为Excel")
            return False

        dataframes = self.extract_tables_to_dataframe(pdf_path, pages)

        if not dataframes:
            logger.warning("没有提取到表格数据")
            return False

        try:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for idx, df in enumerate(dataframes):
                    sheet_name = f"表格{idx + 1}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            logger.info(f"成功保存表格到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存Excel失败: {e}")
            return False


class PDFExtractor:
    """PDF内容提取器（统一接口）"""

    def __init__(self):
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()

    def extract(self, pdf_path: str, extract_text: bool = True, extract_tables: bool = True) -> ExtractionResult:
        """
        提取PDF内容
        
        Args:
            pdf_path: PDF文件路径
            extract_text: 是否提取文本
            extract_tables: 是否提取表格
            
        Returns:
            提取结果
        """
        text = ""
        text_by_page = {}
        tables = []
        blocks = []
        metadata = {}

        if extract_text:
            text = self.text_extractor.extract_text(pdf_path)
            text_by_page = self.text_extractor.extract_text_by_page(pdf_path)

        if extract_tables:
            tables = self.table_extractor.extract_tables(pdf_path)

        metadata = self._extract_metadata(pdf_path)

        return ExtractionResult(
            text=text,
            text_by_page=text_by_page,
            tables=tables,
            blocks=blocks,
            metadata=metadata,
        )

    def _extract_metadata(self, pdf_path: str) -> dict[str, Any]:
        """提取PDF元数据"""
        try:
            import pdfplumber

            metadata = {}
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.metadata:
                    metadata = {
                        "title": pdf.metadata.get("Title", ""),
                        "author": pdf.metadata.get("Author", ""),
                        "subject": pdf.metadata.get("Subject", ""),
                        "creator": pdf.metadata.get("Creator", ""),
                        "producer": pdf.metadata.get("Producer", ""),
                        "creationDate": pdf.metadata.get("CreationDate", ""),
                        "modDate": pdf.metadata.get("ModDate", ""),
                        "page_count": len(pdf.pages),
                    }

            return metadata
        except Exception as e:
            logger.warning(f"提取元数据失败: {e}")
            return {}

    def extract_page(self, pdf_path: str, page_num: int) -> dict[str, Any]:
        """
        提取指定页的内容
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页码（从1开始）
            
        Returns:
            页面内容字典
        """
        text = self.text_extractor.extract_text(pdf_path, pages=[page_num - 1])
        tables = self.table_extractor.extract_tables(pdf_path, pages=[page_num - 1])
        blocks = self.text_extractor.extract_blocks(pdf_path, page_num)

        return {
            "page_num": page_num,
            "text": text,
            "tables": tables,
            "blocks": blocks,
        }
