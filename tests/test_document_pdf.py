"""
PDF 模块单元测试

测试 PDF 文档的提取、合并、拆分和表单功能。
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestPDFExtractor:
    """测试 PDF 提取器。"""

    def test_extractor_import(self):
        """测试提取器导入。"""
        pdfplumber = pytest.importorskip("pdfplumber")
        
        from src.document import PDFExtractor
        assert PDFExtractor is not None

    def test_text_extractor_import(self):
        """测试文本提取器导入。"""
        pytest.importorskip("pdfplumber")
        
        from src.document import TextExtractor
        assert TextExtractor is not None

    def test_table_extractor_import(self):
        """测试表格提取器导入。"""
        pytest.importorskip("pdfplumber")
        
        from src.document import TableExtractor
        assert TableExtractor is not None


class TestPDFMerger:
    """测试 PDF 合并器。"""

    def test_merger_import(self):
        """测试合并器导入。"""
        pytest.importorskip("pypdf")
        
        from src.document import PDFMerger
        assert PDFMerger is not None

    def test_splitter_import(self):
        """测试拆分器导入。"""
        pytest.importorskip("pypdf")
        
        from src.document import PDFSplitter
        assert PDFSplitter is not None


class TestPDFFormFiller:
    """测试 PDF 表单填写器。"""

    def test_form_filler_import(self):
        """测试表单填写器导入。"""
        pytest.importorskip("pypdf")
        
        from src.document import PDFFormFiller, FormFieldInfo
        assert PDFFormFiller is not None
        assert FormFieldInfo is not None


class TestPDFOCRProcessor:
    """测试 PDF OCR 处理器。"""

    def test_ocr_processor_import(self):
        """测试 OCR 处理器导入。"""
        pytest.importorskip("PIL")
        
        from src.document import PDFOCRProcessor
        assert PDFOCRProcessor is not None


class TestPDFIntegration:
    """PDF 集成测试。"""

    def test_create_and_extract_pdf(self):
        """测试创建并提取 PDF。"""
        pytest.importorskip("reportlab")
        pytest.importorskip("pdfplumber")
        
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from src.document import PDFExtractor
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        
        try:
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.drawString(100, 750, "Hello, PDF Test!")
            c.save()
            
            extractor = PDFExtractor()
            result = extractor.extract(pdf_path)
            
            assert result.text is not None
            assert "Hello, PDF Test!" in result.text
        finally:
            if Path(pdf_path).exists():
                os.unlink(pdf_path)
