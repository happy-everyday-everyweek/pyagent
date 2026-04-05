"""
PyAgent 聊天Agent工具集 - 搜索工具

通过模块间通信调用搜索模块。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str = ""
    source: str = ""


@dataclass
class SearchToolResult:
    """搜索工具结果"""
    success: bool
    results: list[SearchResult] = field(default_factory=list)
    error: str = ""
    query: str = ""


class SearchTool:
    """搜索工具"""

    def __init__(self, search_module: Any | None = None):
        self.search_module = search_module
        self.name = "search"
        self.description = "搜索信息"

    async def execute(
        self,
        query: str,
        max_results: int = 5,
        **kwargs
    ) -> SearchToolResult:
        """执行搜索"""
        if not query:
            return SearchToolResult(
                success=False,
                error="搜索查询不能为空"
            )

        if self.search_module:
            try:
                results = await self.search_module.search(query, max_results)
                return SearchToolResult(
                    success=True,
                    results=results,
                    query=query
                )
            except Exception as e:
                return SearchToolResult(
                    success=False,
                    error=str(e),
                    query=query
                )

        return SearchToolResult(
            success=True,
            results=[
                SearchResult(
                    title="模拟搜索结果",
                    url="https://example.com",
                    snippet=f"这是关于 '{query}' 的模拟搜索结果",
                    source="mock"
                )
            ],
            query=query
        )

    def get_description(self) -> str:
        """获取工具描述"""
        return self.description

    def get_parameters(self) -> dict[str, Any]:
        """获取参数定义"""
        return {
            "query": {
                "type": "string",
                "description": "搜索查询内容"
            },
            "max_results": {
                "type": "integer",
                "description": "最大返回结果数",
                "default": 5
            }
        }
