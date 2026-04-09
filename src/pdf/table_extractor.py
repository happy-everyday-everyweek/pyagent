"""PDF table extraction and OCR enhancement."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    row: int
    col: int
    text: str
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = 1.0


@dataclass
class Table:
    page: int
    cells: list[TableCell]
    rows: int
    cols: int
    bbox: tuple[float, float, float, float] | None = None
    header_row: int | None = None

    def to_list(self) -> list[list[str]]:
        result = [[""] * self.cols for _ in range(self.rows)]
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                result[cell.row][cell.col] = cell.text
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "rows": self.rows,
            "cols": self.cols,
            "cells": [{"row": c.row, "col": c.col, "text": c.text, "confidence": c.confidence} for c in self.cells],
            "header_row": self.header_row,
        }


@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: tuple[float, float, float, float] | None = None
    language: str | None = None


class TableExtractor:
    """Extract tables from PDF documents."""

    def __init__(self):
        self._min_row_height = 10
        self._min_col_width = 20

    def extract_from_page(self, page_content: Any, page_num: int = 1) -> list[Table]:
        tables = []

        try:
            if hasattr(page_content, "extract_tables"):
                raw_tables = page_content.extract_tables()
                for i, raw_table in enumerate(raw_tables):
                    table = self._convert_raw_table(raw_table, page_num)
                    if table:
                        tables.append(table)
            else:
                tables = self._detect_tables_heuristic(page_content, page_num)

        except Exception as e:
            logger.warning("Failed to extract tables from page %d: %s", page_num, e)

        logger.info("Extracted %d tables from page %d", len(tables), page_num)
        return tables

    def _convert_raw_table(self, raw_table: list[list[str]], page_num: int) -> Table | None:
        if not raw_table or not raw_table[0]:
            return None

        rows = len(raw_table)
        cols = max(len(row) for row in raw_table)

        cells = []
        for row_idx, row in enumerate(raw_table):
            for col_idx, text in enumerate(row):
                if text:
                    cells.append(TableCell(row=row_idx, col=col_idx, text=str(text).strip()))

        return Table(page=page_num, cells=cells, rows=rows, cols=cols)

    def _detect_tables_heuristic(self, page_content: Any, page_num: int) -> list[Table]:
        tables = []

        text = ""
        if hasattr(page_content, "extract_text"):
            text = page_content.extract_text() or ""

        lines = text.split("\n")
        potential_table_lines = []

        for line in lines:
            cols = re.split(r"\t+|\s{3,}", line.strip())
            if len(cols) >= 2:
                potential_table_lines.append(cols)

        if len(potential_table_lines) >= 2:
            max_cols = max(len(row) for row in potential_table_lines)

            cells = []
            for row_idx, row in enumerate(potential_table_lines):
                for col_idx, text in enumerate(row):
                    if col_idx < max_cols:
                        cells.append(TableCell(row=row_idx, col=col_idx, text=text.strip()))

            tables.append(
                Table(
                    page=page_num,
                    cells=cells,
                    rows=len(potential_table_lines),
                    cols=max_cols,
                )
            )

        return tables

    def extract_all(self, pdf_path: str) -> list[Table]:
        all_tables = []

        try:
            import fitz

            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc, 1):
                tables = self.extract_from_page(page, page_num)
                all_tables.extend(tables)
            doc.close()

        except ImportError:
            logger.warning("PyMuPDF not available, using basic extraction")
            try:
                import pdfplumber

                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        tables = self.extract_from_page(page, page_num)
                        all_tables.extend(tables)

            except ImportError:
                logger.error("Neither PyMuPDF nor pdfplumber available")

        return all_tables


class OCREnhancer:
    """OCR enhancement for PDF image content."""

    def __init__(self, engine: str = "auto"):
        self._engine = engine
        self._ocr_engine: Any = None

    def _init_engine(self) -> None:
        if self._ocr_engine:
            return

        if self._engine == "tesseract":
            try:
                import pytesseract

                self._ocr_engine = pytesseract
            except ImportError:
                logger.warning("pytesseract not available")

        elif self._engine == "easyocr":
            try:
                import easyocr

                self._ocr_engine = easyocr.Reader(["ch_sim", "en"])
            except ImportError:
                logger.warning("easyocr not available")

        elif self._engine == "auto":
            try:
                import pytesseract

                self._ocr_engine = pytesseract
                self._engine = "tesseract"
            except ImportError:
                try:
                    import easyocr

                    self._ocr_engine = easyocr.Reader(["ch_sim", "en"])
                    self._engine = "easyocr"
                except ImportError:
                    logger.warning("No OCR engine available")

    def ocr_image(self, image_path: str | Path) -> OCRResult:
        self._init_engine()

        if not self._ocr_engine:
            return OCRResult(text="", confidence=0.0)

        try:
            if self._engine == "tesseract":
                result = self._ocr_engine.image_to_string(str(image_path), lang="chi_sim+eng")
                return OCRResult(text=result.strip(), confidence=0.8)

            if self._engine == "easyocr":
                results = self._ocr_engine.readtext(str(image_path))
                text = " ".join(r[1] for r in results)
                avg_conf = sum(r[2] for r in results) / len(results) if results else 0.0
                return OCRResult(text=text.strip(), confidence=avg_conf)

        except Exception as e:
            logger.warning("OCR failed: %s", e)
            return OCRResult(text="", confidence=0.0)

        return OCRResult(text="", confidence=0.0)

    def ocr_pdf_page(self, page: Any) -> list[OCRResult]:
        results = []

        try:
            if hasattr(page, "get_images"):
                images = page.get_images(full=True)
                for img_index, img in enumerate(images):
                    xref = img[0]
                    base_image = page.parent.extract_image(xref)
                    image_bytes = base_image["image"]

                    import tempfile

                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                        f.write(image_bytes)
                        f.flush()

                        ocr_result = self.ocr_image(f.name)
                        if ocr_result.text:
                            results.append(ocr_result)

        except Exception as e:
            logger.warning("PDF page OCR failed: %s", e)

        return results

    def enhance_pdf_text(self, pdf_path: str) -> dict[str, Any]:
        all_text = []
        all_ocr_results = []

        try:
            import fitz

            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                all_text.append({"page": page_num, "text": text})

                ocr_results = self.ocr_pdf_page(page)
                for ocr in ocr_results:
                    all_ocr_results.append({"page": page_num, "text": ocr.text, "confidence": ocr.confidence})

            doc.close()

        except Exception as e:
            logger.error("PDF enhancement failed: %s", e)

        return {
            "extracted_text": all_text,
            "ocr_text": all_ocr_results,
            "total_pages": len(all_text),
        }


def extract_tables(pdf_path: str) -> list[Table]:
    extractor = TableExtractor()
    return extractor.extract_all(pdf_path)


def ocr_pdf(pdf_path: str) -> dict[str, Any]:
    enhancer = OCREnhancer()
    return enhancer.enhance_pdf_text(pdf_path)
