"""
DOCX 模块单元测试

测试 Word 文档的创建、编辑、批注和修订功能。
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestDocxCreator:
    """测试 DOCX 创建器。"""

    def test_create_blank_document(self):
        """测试创建空白文档。"""
        pytest.importorskip("defusedxml")
        
        from src.document import DocxCreator
        
        creator = DocxCreator()
        
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            output_path = f.name
        
        try:
            result = creator.create_blank(output_path)
            assert result is True
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_create_with_content(self):
        """测试创建带内容的文档。"""
        pytest.importorskip("defusedxml")
        
        from src.document import DocxCreator
        
        creator = DocxCreator()
        
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            output_path = f.name
        
        try:
            result = creator.create_with_content(
                output_path,
                title="测试标题",
                paragraphs=["段落1", "段落2"]
            )
            assert result is True
            assert Path(output_path).exists()
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)


class TestDocxEditor:
    """测试 DOCX 编辑器。"""

    def test_create_and_edit_document(self):
        """测试创建并编辑文档。"""
        pytest.importorskip("defusedxml")
        
        from src.document import DocxCreator, Document, unpack_document
        
        creator = DocxCreator()
        
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.create_blank(output_path)
            
            unpacked_dir = tempfile.mkdtemp(prefix="docx_unpacked_")
            try:
                unpack_document(output_path, unpacked_dir)
                
                doc = Document(unpacked_dir)
                assert doc is not None
                assert doc.unpacked_path.exists()
            finally:
                if Path(unpacked_dir).exists():
                    import shutil
                    shutil.rmtree(unpacked_dir)
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)


class TestCommentManager:
    """测试批注管理器。"""

    def test_comment_manager_import(self):
        """测试批注管理器导入。"""
        pytest.importorskip("defusedxml")
        
        from src.document import CommentManager
        assert CommentManager is not None


class TestRevisionManager:
    """测试修订管理器。"""

    def test_revision_manager_import(self):
        """测试修订管理器导入。"""
        pytest.importorskip("defusedxml")
        
        from src.document import RevisionManager
        assert RevisionManager is not None
