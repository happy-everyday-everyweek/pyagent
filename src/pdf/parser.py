"""
PyAgent PDF模块 - PDF解析器
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    x: float
    y: float
    width: float
    height: float
    text: str
    font_name: str = ""
    font_size: float = 0.0


@dataclass
class Table:
    page_num: int
    x: int
    y: int
    rows: int
    cols: int
    data: list[list[str]]
    bbox: tuple[float, float, float, float]


@dataclass
class Image:
    page_num: int
    x: int
    y: int
    width: int
    height: int
    format: str
    data: bytes | None = None


@dataclass
class OutlineItem:
    title: str
    level: int
    page_num: int
    children: list["OutlineItem"] = field(default_factory=list)


@dataclass
class PDFPage:
    page_num: int
    width: float
    height: float
    text: str
    blocks: list[TextBlock] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)


    def to_dict(self) -> dict[str, Any]:
        return {
            "page_num": self.page_num,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "blocks": [b.to_dict() for b in self.blocks],
            "tables": [t.to_dict() for t in self.tables],
            "images": [i.to_dict() for i in self.images],
        }


@dataclass
class PDFDocument:
    file_path: str
    page_count: int
    metadata: dict[str, Any] = field(default_factory=dict)
    pages: list[PDFPage] = field(default_factory=list)
    outline: list[OutlineItem] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "page_count": self.page_count,
            "metadata": self.metadata,
            "pages": [p.to_dict() for p in self.pages],
            "outline": [o.to_dict() for o in self.outline],
            "tables": [t.to_dict() for t in self.tables],
            "images": [i.to_dict() for i in self.images],
        }


class PDFParser:
    """PDF解析器"""

    def __init__(self):
        self._document: PDFDocument | None = None
        self._fitz_available = self._check_fitz()
        self._pdfplumber_available = self._check_pdfplumber()
        self._pypdf2_available = self._check_pypdf2()

    def _check_fitz(self) -> bool:
        try:
            import fitz
            return True
        except ImportError:
            logger.debug("fitz (PyMuPDF) not available")
            return False

    def _check_pdfplumber(self) -> bool:
        try:
            import pdfplumber
            return True
        except ImportError:
            logger.debug("pdfplumber not available")
            return False

    def _check_pypdf2(self) -> bool:
        try:
            import PyPDF2
            return True
        except ImportError:
            logger.debug("PyPDF2 not available")
            return False

    def parse(self, file_path: str) -> PDFDocument | None:
        if self._fitz_available:
            logger.info(f"Parsing PDF with fitz (PyMuPDF): {file_path}")
            return self._parse_with_fitz(file_path)
        if self._pdfplumber_available:
            logger.info(f"Parsing PDF with pdfplumber: {file_path}")
            return self._parse_with_pdfplumber(file_path)
        if self._pypdf2_available:
            logger.info(f"Parsing PDF with PyPDF2: {file_path}")
            return self._parse_with_pypdf2(file_path)
        logger.error("No PDF parsing library available (fitz, pdfplumber, or PyPDF2)")
        return None

    def parse_bytes(self, data: bytes) -> PDFDocument | None:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(data)
            f.flush()
            result = self.parse(f.name)
        return result

    def _parse_with_fitz(self, file_path: str) -> PDFDocument | None:
        try:
            import fitz

            doc = fitz.open(file_path)
            pages: list[PDFPage] = []
            tables: list[Table] = []
            images: list[Image] = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                blocks = self._extract_blocks(page)
                page_tables = self._extract_tables(page)
                page_images = self._extract_images(page, page_num)

                pages.append(PDFPage(
                    page_num=page_num + 1,
                    width=page.rect.width,
                    height=page.rect.height,
                    text=text,
                    blocks=blocks,
                    tables=page_tables,
                    images=page_images,
                ))
                tables.extend(page_tables)
                images.extend(page_images)

            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creationDate": doc.metadata.get("creationDate", ""),
            }

            outline = self._extract_outline(doc.get_toc())

            self._document = PDFDocument(
                file_path=file_path,
                page_count=len(doc),
                metadata=metadata,
                pages=pages,
                outline=outline,
                tables=tables,
                images=images,
            )

            return self._document
        except Exception:
            return None

    def _parse_with_pdfplumber(self, file_path: str) -> PDFDocument | None:
        try:
            import pdfplumber

            with pdfplumber.open(file_path) as pdf:
                pages: list[PDFPage] = []
                tables: list[Table] = []
                images: list[Image] = []

                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    width = page.width
                    height = page.height

                    blocks = self._extract_blocks_pdfplumber(page)
                    page_tables = self._extract_tables_pdfplumber(page, page_num)

                    pages.append(PDFPage(
                        page_num=page_num,
                        width=width,
                        height=height,
                        text=text,
                        blocks=blocks,
                        tables=page_tables,
                        images=[],
                    ))
                    tables.extend(page_tables)

                metadata = self._extract_metadata_pdfplumber(pdf)

                self._document = PDFDocument(
                    file_path=file_path,
                    page_count=len(pdf.pages),
                    metadata=metadata,
                    pages=pages,
                    outline=[],
                    tables=tables,
                    images=images,
                )

                logger.info(f"Successfully parsed PDF with pdfplumber: {len(pages)} pages")
                return self._document
        except Exception as e:
            logger.error(f"Error parsing PDF with pdfplumber: {e}")
            return None

    def _parse_with_pypdf2(self, file_path: str) -> PDFDocument | None:
        try:
            import PyPDF2

            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                pages: list[PDFPage] = []

                for page_num, page in enumerate(reader.pages, start=1):
                    text = page.extract_text() or ""

                    width = float(page.mediabox[2]) if page.mediabox else 612.0
                    height = float(page.mediabox[3]) if page.mediabox else 792.0

                    pages.append(PDFPage(
                        page_num=page_num,
                        width=width,
                        height=height,
                        text=text,
                        blocks=[],
                        tables=[],
                        images=[],
                    ))

                metadata = self._extract_metadata_pypdf2(reader)

                self._document = PDFDocument(
                    file_path=file_path,
                    page_count=len(reader.pages),
                    metadata=metadata,
                    pages=pages,
                    outline=[],
                    tables=[],
                    images=[],
                )

                logger.info(f"Successfully parsed PDF with PyPDF2: {len(pages)} pages")
                return self._document
        except Exception as e:
            logger.error(f"Error parsing PDF with PyPDF2: {e}")
            return None

    def _extract_blocks_pdfplumber(self, page) -> list[TextBlock]:
        blocks: list[TextBlock] = []
        try:
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
                        text = "".join([c["text"] for c in current_block])
                        x0 = min([c["x0"] for c in current_block])
                        y0 = min([c["top"] for c in current_block])
                        x1 = max([c["x1"] for c in current_block])
                        y1 = max([c["bottom"] for c in current_block])

                        blocks.append(TextBlock(
                            x=x0,
                            y=y0,
                            width=x1 - x0,
                            height=y1 - y0,
                            text=text,
                            font_name=current_block[0].get("fontname", ""),
                            font_size=current_block[0].get("size", 0.0),
                        ))

                    current_block = [char]
                    current_y = char["top"]

            if current_block:
                text = "".join([c["text"] for c in current_block])
                x0 = min([c["x0"] for c in current_block])
                y0 = min([c["top"] for c in current_block])
                x1 = max([c["x1"] for c in current_block])
                y1 = max([c["bottom"] for c in current_block])

                blocks.append(TextBlock(
                    x=x0,
                    y=y0,
                    width=x1 - x0,
                    height=y1 - y0,
                    text=text,
                    font_name=current_block[0].get("fontname", ""),
                    font_size=current_block[0].get("size", 0.0),
                ))
        except Exception as e:
            logger.warning(f"Error extracting blocks with pdfplumber: {e}")

        return blocks

    def _extract_tables_pdfplumber(self, page, page_num: int) -> list[Table]:
        tables: list[Table] = []
        try:
            extracted_tables = page.extract_tables()
            for table_data in extracted_tables:
                if table_data:
                    bbox = page.bbox or (0, 0, page.width, page.height)
                    rows = len(table_data)
                    cols = len(table_data[0]) if table_data else 0

                    tables.append(Table(
                        page_num=page_num,
                        x=int(bbox[0]),
                        y=int(bbox[1]),
                        rows=rows,
                        cols=cols,
                        data=table_data,
                        bbox=bbox,
                    ))
        except Exception as e:
            logger.warning(f"Error extracting tables with pdfplumber: {e}")

        return tables

    def _extract_metadata_pdfplumber(self, pdf) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        try:
            if pdf.metadata:
                metadata = {
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                    "subject": pdf.metadata.get("Subject", ""),
                    "creator": pdf.metadata.get("Creator", ""),
                    "producer": pdf.metadata.get("Producer", ""),
                    "creationDate": pdf.metadata.get("CreationDate", ""),
                    "modDate": pdf.metadata.get("ModDate", ""),
                }
        except Exception as e:
            logger.warning(f"Error extracting metadata with pdfplumber: {e}")

        return metadata

    def _extract_metadata_pypdf2(self, reader) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        try:
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                    "producer": reader.metadata.get("/Producer", ""),
                    "creationDate": reader.metadata.get("/CreationDate", ""),
                    "modDate": reader.metadata.get("/ModDate", ""),
                }
        except Exception as e:
            logger.warning(f"Error extracting metadata with PyPDF2: {e}")

        return metadata

    def _extract_blocks(self, page) -> list[TextBlock]:
        blocks: list[TextBlock] = []
        try:
            for block in page.get_text("blocks"):
                bbox = block["bbox"]
                blocks.append(TextBlock(
                    x=bbox[0],
                    y=bbox[1],
                    width=bbox[2] - bbox[0],
                    height=bbox[3] - bbox[1],
                    text=block["text"],
                    font_name=block.get("fontname", ""),
                    font_size=block.get("size", 0),
                ))
        except Exception:
            pass
        return blocks

    def _extract_tables(self, page) -> list[Table]:
        tables: list[Table] = []
        try:
            for table in page.find_tables():
                bbox = table.bbox
                tables.append(Table(
                    page_num=table.page_number + 1,
                    x=int(bbox[0]),
                    y=int(bbox[1]),
                    rows=table.row_count,
                    cols=table.col_count,
                    data=table.extract(),
                    bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
                ))
        except Exception:
            pass
        return tables

    def _extract_images(self, page, page_num: int) -> list[Image]:
        images: list[Image] = []
        try:
            for img in page.get_images():
                bbox = img["bbox"]
                images.append(Image(
                    page_num=page_num + 1,
                    x=int(bbox[0]),
                    y=int(bbox[1]),
                    width=int(bbox[2] - bbox[0]),
                    height=int(bbox[3] - bbox[1]),
                    format=img.get("ext", "unknown"),
                    data=img["image"],
                ))
        except Exception:
            pass
        return images

    def _extract_outline(self, toc) -> list[OutlineItem]:
        outline: list[OutlineItem] = []
        try:
            for item in toc:
                children = self._extract_outline(item.get("children", []))
                outline.append(OutlineItem(
                    title=item.get("title", ""),
                    level=item.get("level", 0),
                    page_num=item.get("page", 0),
                    children=children,
                ))
        except Exception:
            pass
        return outline

    def get_page_count(self) -> int:
        return self._document.page_count if self._document else 0

    def get_page(self, page_num: int) -> PDFPage | None:
        if not self._document:
            return None
        if 0 < page_num <= len(self._document.pages):
            return self._document.pages[page_num - 1]
        return None

    def get_metadata(self) -> dict[str, Any]:
        return self._document.metadata if self._document else {}

    def get_outline(self) -> list[OutlineItem]:
        return self._document.outline if self._document else []


pdf_parser = PDFParser()
