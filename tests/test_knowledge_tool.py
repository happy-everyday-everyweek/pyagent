"""
PyAgent 百科工具测试
"""

import pytest
import asyncio
from pathlib import Path

from src.execution.tools.knowledge import KnowledgeTool, ZimParser
from src.execution.tools.base import ToolCategory, RiskLevel


class TestKnowledgeTool:
    """百科工具测试"""

    def test_tool_properties(self):
        """测试工具属性"""
        tool = KnowledgeTool()
        
        assert tool.name == "knowledge_search"
        assert tool.category == ToolCategory.KNOWLEDGE
        assert tool.risk_level == RiskLevel.SAFE
        assert "百科" in tool.description or "知识" in tool.description

    def test_list_libraries(self):
        """测试列出知识库"""
        tool = KnowledgeTool()
        result = asyncio.run(tool.execute(action="list"))
        
        assert result.success is True
        assert "libraries" in result.data

    def test_list_categories(self):
        """测试列出分类"""
        tool = KnowledgeTool()
        result = asyncio.run(tool.execute(action="categories"))
        
        assert result.success is True
        assert "categories" in result.data

    def test_list_wikipedia_options(self):
        """测试列出Wikipedia选项"""
        tool = KnowledgeTool()
        result = asyncio.run(tool.execute(action="wikipedia_options"))
        
        assert result.success is True
        assert "options" in result.data

    def test_search_without_query(self):
        """测试无关键词搜索"""
        tool = KnowledgeTool()
        result = asyncio.run(tool.execute(action="search"))
        
        assert result.success is False
        assert "关键词" in result.error

    def test_get_article_without_query(self):
        """测试无关键词获取文章"""
        tool = KnowledgeTool()
        result = asyncio.run(tool.execute(action="get"))
        
        assert result.success is False


class TestZimParser:
    """ZIM解析器测试"""

    def test_parser_init(self):
        """测试解析器初始化"""
        parser = ZimParser("/nonexistent/path.zim")
        assert parser.zim_path == Path("/nonexistent/path.zim")

    def test_open_nonexistent_file(self):
        """测试打开不存在的文件"""
        parser = ZimParser("/nonexistent/path.zim")
        result = parser.open()
        
        assert result is False

    def test_get_info_without_open(self):
        """测试未打开时获取信息"""
        parser = ZimParser("/nonexistent/path.zim")
        info = parser.get_info()
        
        assert info == {}


class TestKnowledgeToolParameters:
    """百科工具参数测试"""

    def test_parameter_schema(self):
        """测试参数Schema"""
        tool = KnowledgeTool()
        schema = tool.get_parameter_schema()
        
        assert "properties" in schema
        assert "action" in schema["properties"]
        assert "query" in schema["properties"]
        assert "required" in schema
        assert "action" in schema["required"]

    def test_get_info(self):
        """测试获取工具信息"""
        tool = KnowledgeTool()
        info = tool.get_info()
        
        assert info["name"] == "knowledge_search"
        assert info["category"] == "knowledge"
        assert info["risk_level"] == "safe"
