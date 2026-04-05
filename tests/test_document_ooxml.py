"""
OOXML 工具模块单元测试

测试 Office 文档的打包、解包和验证功能。
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestPackDocument:
    """测试打包工具。"""

    def test_pack_document_import(self):
        """测试打包工具导入。"""
        pytest.importorskip("defusedxml")
        
        from src.document import pack_document
        assert pack_document is not None

    def test_pack_docx(self):
        """测试打包 DOCX 文档。"""
        pytest.importorskip("defusedxml")
        
        from src.document import pack_document, unpack_document
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            unpacked_dir = temp_dir / "unpacked"
            unpacked_dir.mkdir()
            
            content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
</Types>'''
            (unpacked_dir / "[Content_Types].xml").write_text(content_types, encoding="utf-8")
            
            rels_dir = unpacked_dir / "_rels"
            rels_dir.mkdir()
            
            rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>'''
            (rels_dir / ".rels").write_text(rels, encoding="utf-8")
            
            output_path = temp_dir / "test.docx"
            result = pack_document(unpacked_dir, output_path)
            
            assert result is True
            assert output_path.exists()


class TestUnpackDocument:
    """测试解包工具。"""

    def test_unpack_document_import(self):
        """测试解包工具导入。"""
        pytest.importorskip("defusedxml")
        
        from src.document import unpack_document
        assert unpack_document is not None

    def test_unpack_docx(self):
        """测试解包 DOCX 文档。"""
        pytest.importorskip("defusedxml")
        
        from src.document import DocxCreator, unpack_document
        
        creator = DocxCreator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            docx_path = temp_dir / "test.docx"
            creator.create_blank(docx_path)
            
            unpacked_dir = temp_dir / "unpacked"
            result = unpack_document(docx_path, unpacked_dir)
            
            assert result is not None
            assert "output_path" in result
            assert "xml_files" in result
            assert unpacked_dir.exists()


class TestValidateDocument:
    """测试验证工具。"""

    def test_validate_document_import(self):
        """测试验证工具导入。"""
        pytest.importorskip("defusedxml")
        
        from src.document import validate_document
        assert validate_document is not None

    def test_validate_docx(self):
        """测试验证 DOCX 文档。"""
        pytest.importorskip("defusedxml")
        
        from src.document import DocxCreator, validate_document
        
        creator = DocxCreator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            docx_path = temp_dir / "test.docx"
            creator.create_blank(docx_path)
            
            valid, errors = validate_document(docx_path)
            
            assert valid is True
            assert len(errors) == 0


class TestOOXMLIntegration:
    """OOXML 集成测试。"""

    def test_unpack_pack_cycle(self):
        """测试解包-打包循环。"""
        pytest.importorskip("defusedxml")
        
        from src.document import DocxCreator, unpack_document, pack_document
        
        creator = DocxCreator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            original_path = temp_dir / "original.docx"
            creator.create_blank(original_path)
            
            unpacked_dir = temp_dir / "unpacked"
            unpack_document(original_path, unpacked_dir)
            
            repacked_path = temp_dir / "repacked.docx"
            pack_document(unpacked_dir, repacked_path)
            
            assert repacked_path.exists()
            assert repacked_path.stat().st_size > 0

    def test_get_document_type(self):
        """测试获取文档类型。"""
        pytest.importorskip("defusedxml")
        
        from src.document.ooxml.unpack import get_document_type, unpack_document
        from src.document import DocxCreator
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            docx_creator = DocxCreator()
            docx_path = temp_dir / "test.docx"
            docx_creator.create_blank(docx_path)
            
            unpacked_dir = temp_dir / "docx_unpacked"
            unpack_document(docx_path, unpacked_dir)
            
            doc_type = get_document_type(unpacked_dir)
            assert doc_type == "docx"
