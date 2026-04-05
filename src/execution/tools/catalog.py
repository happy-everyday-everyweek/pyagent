"""
PyAgent 执行模块工具系统 - 工具目录

生成和管理工具目录，供LLM参考。
"""

from typing import Any

from .base import BaseTool
from .registry import ToolRegistry


class ToolCatalog:
    """工具目录"""

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()

    def generate_catalog_text(self) -> str:
        """生成工具目录文本"""
        tools = self.registry.get_all_tools()
        if not tools:
            return "当前没有可用工具"

        catalog_parts = ["# 可用工具目录\n"]

        categories = {}
        for tool in tools.values():
            cat = tool.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)

        for category, category_tools in categories.items():
            catalog_parts.append(f"\n## {category.upper()}\n")

            for tool in category_tools:
                catalog_parts.append(f"\n### {tool.name}\n")
                catalog_parts.append(f"描述: {tool.description}\n")
                catalog_parts.append(f"风险等级: {tool.risk_level.value}\n")

                params = tool.get_parameters()
                if params:
                    catalog_parts.append("参数:\n")
                    for param in params:
                        required = "必需" if param.required else "可选"
                        catalog_parts.append(f"  - {param.name} ({param.type}, {required}): {param.description}\n")

        return "".join(catalog_parts)

    def generate_catalog_json(self) -> list[dict[str, Any]]:
        """生成工具目录JSON"""
        tools = self.registry.get_all_tools()
        return [tool.get_info() for tool in tools.values()]

    def generate_tool_schema(self) -> dict[str, Any]:
        """生成工具Schema（OpenAI格式）"""
        tools = self.registry.get_all_tools()

        return {
            "type": "array",
            "items": [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.get_parameter_schema()
                    }
                }
                for tool in tools.values()
            ]
        }

    def search_tools(self, query: str) -> list[BaseTool]:
        """搜索工具"""
        tools = self.registry.get_all_tools()
        query_lower = query.lower()

        results = []
        for tool in tools.values():
            if (query_lower in tool.name.lower() or
                query_lower in tool.description.lower()):
                results.append(tool)

        return results

    def get_tool_usage_examples(self, tool_name: str) -> list[str]:
        """获取工具使用示例"""
        examples = {
            "shell": [
                '{"command": "ls -la"}',
                '{"command": "echo hello"}'
            ],
            "file_read": [
                '{"path": "/path/to/file.txt"}',
                '{"path": "/path/to/file.txt", "encoding": "utf-8"}'
            ],
            "file_write": [
                '{"path": "/path/to/file.txt", "content": "Hello World"}'
            ],
            "web_search": [
                '{"query": "Python教程"}',
                '{"query": "最新新闻", "max_results": 5}'
            ]
        }

        return examples.get(tool_name, [])
