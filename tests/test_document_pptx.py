"""
PPTX 模块单元测试

测试 PowerPoint 演示文稿的创建、编辑和幻灯片管理功能。
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestPptxCreator:
    """测试 PPTX 创建器。"""

    def test_create_blank_presentation(self):
        """测试创建空白演示文稿。"""
        pytest.importorskip("defusedxml")
        
        from src.document import PptxCreator
        
        creator = PptxCreator()
        
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            output_path = f.name
        
        try:
            result = creator.save(output_path)
            assert result is True
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_add_title_slide(self):
        """测试添加标题幻灯片。"""
        pytest.importorskip("defusedxml")
        
        from src.document import PptxCreator
        
        creator = PptxCreator()
        slide_idx = creator.add_title_slide("测试标题", "测试副标题")
        
        assert slide_idx >= 1
        assert creator.slides_count >= 1

    def test_add_content_slide(self):
        """测试添加内容幻灯片。"""
        pytest.importorskip("defusedxml")
        
        from src.document import PptxCreator
        
        creator = PptxCreator()
        slide_idx = creator.add_content_slide(
            "内容标题",
            ["要点1", "要点2", "要点3"]
        )
        
        assert slide_idx >= 1
        assert creator.slides_count >= 1

    def test_multiple_slides(self):
        """测试添加多个幻灯片。"""
        pytest.importorskip("defusedxml")
        
        from src.document import PptxCreator
        
        creator = PptxCreator()
        creator.add_title_slide("标题", "副标题")
        creator.add_content_slide("内容1", ["要点1"])
        creator.add_content_slide("内容2", ["要点2"])
        
        assert creator.slides_count >= 3


class TestPptxEditor:
    """测试 PPTX 编辑器。"""

    def test_edit_presentation(self):
        """测试编辑演示文稿。"""
        pytest.importorskip("defusedxml")
        
        from src.document import PptxCreator, PptxEditor
        
        creator = PptxCreator()
        creator.add_title_slide("原始标题")
        
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.save(output_path)
            
            editor = PptxEditor(output_path)
            assert editor.slides_count >= 1
            
            elements = editor.find_text_elements(1)
            assert isinstance(elements, list)
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)


class TestSlideManager:
    """测试幻灯片管理器。"""

    def test_list_slides(self):
        """测试列出幻灯片。"""
        pytest.importorskip("defusedxml")
        
        from src.document import PptxCreator, SlideManager
        
        creator = PptxCreator()
        creator.add_title_slide("标题1")
        creator.add_content_slide("标题2", ["要点"])
        
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.save(output_path)
            
            manager = SlideManager(output_path)
            slides = manager.list_slides()
            
            assert len(slides) >= 2
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)


class TestThumbnailGenerator:
    """测试缩略图生成器。"""

    def test_thumbnail_generator_import(self):
        """测试缩略图生成器导入。"""
        pytest.importorskip("defusedxml")
        
        from src.document import ThumbnailGenerator
        assert ThumbnailGenerator is not None
