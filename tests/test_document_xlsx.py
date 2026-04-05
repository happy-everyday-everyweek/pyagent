"""
XLSX 模块单元测试

测试 Excel 工作簿的创建、编辑、工作表和图表功能。
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestXlsxCreator:
    """测试 XLSX 创建器。"""

    def test_create_blank_workbook(self):
        """测试创建空白工作簿。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator
        
        creator = XlsxCreator()
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name
        
        try:
            result = creator.save(output_path)
            assert result is True
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_add_sheet(self):
        """测试添加工作表。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator
        
        creator = XlsxCreator()
        sheet_id = creator.add_sheet("测试工作表")
        
        assert sheet_id > 1
        assert "测试工作表" in creator.sheets

    def test_set_cell_string(self):
        """测试设置字符串单元格。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator
        
        creator = XlsxCreator()
        result = creator.set_cell("Sheet1", "A1", "测试内容")
        
        assert result is True

    def test_set_cell_number(self):
        """测试设置数字单元格。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator
        
        creator = XlsxCreator()
        result = creator.set_cell("Sheet1", "B1", 123.45)
        
        assert result is True

    def test_set_cell_formula(self):
        """测试设置公式单元格。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator
        
        creator = XlsxCreator()
        creator.set_cell("Sheet1", "A1", 10)
        creator.set_cell("Sheet1", "A2", 20)
        result = creator.set_cell("Sheet1", "A3", 0, formula="=A1+A2")
        
        assert result is True


class TestXlsxEditor:
    """测试 XLSX 编辑器。"""

    def test_create_and_edit_workbook(self):
        """测试创建并编辑工作簿。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator, XlsxEditor
        
        creator = XlsxCreator()
        creator.set_cell("Sheet1", "A1", "测试值")
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.save(output_path)
            
            editor = XlsxEditor(output_path)
            value = editor.get_cell("Sheet1", "A1")
            
            assert value == "测试值"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_list_sheets(self):
        """测试列出工作表。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator, XlsxEditor
        
        creator = XlsxCreator()
        creator.add_sheet("工作表2")
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.save(output_path)
            
            editor = XlsxEditor(output_path)
            sheets = editor.list_sheets()
            
            assert "Sheet1" in sheets
            assert "工作表2" in sheets
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)


class TestSheetManager:
    """测试工作表管理器。"""

    def test_list_sheets(self):
        """测试列出工作表。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator, SheetManager
        
        creator = XlsxCreator()
        creator.add_sheet("数据")
        creator.add_sheet("分析")
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.save(output_path)
            
            manager = SheetManager(output_path)
            sheets = manager.list_sheets()
            
            assert len(sheets) >= 3
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_rename_sheet(self):
        """测试重命名工作表。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator, SheetManager
        
        creator = XlsxCreator()
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.save(output_path)
            
            manager = SheetManager(output_path)
            result = manager.rename_sheet("Sheet1", "重命名后")
            
            assert result is True
            assert "重命名后" in manager.sheets
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)


class TestChartManager:
    """测试图表管理器。"""

    def test_chart_manager_import(self):
        """测试图表管理器导入。"""
        pytest.importorskip("defusedxml")
        
        from src.document import ChartManager
        assert ChartManager is not None

    def test_list_charts(self):
        """测试列出图表。"""
        pytest.importorskip("defusedxml")
        
        from src.document import XlsxCreator, ChartManager
        
        creator = XlsxCreator()
        creator.set_cell("Sheet1", "A1", "月份")
        creator.set_cell("Sheet1", "B1", "销售额")
        creator.set_cell("Sheet1", "A2", "1月")
        creator.set_cell("Sheet1", "B2", 1000)
        
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name
        
        try:
            creator.save(output_path)
            
            manager = ChartManager(output_path)
            charts = manager.list_charts()
            
            assert isinstance(charts, list)
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)
