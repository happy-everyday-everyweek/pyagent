"""
PyAgent 执行模块子Agent系统 - 搜索子Agent

专门负责搜索任务的子Agent。
"""

from typing import Any

from .base_sub_agent import BaseSubAgent, SubAgentResult


class SearchSubAgent(BaseSubAgent):
    """搜索子Agent"""

    name = "search_agent"
    description = "专门负责搜索信息的子Agent"

    def __init__(
        self,
        llm_client: Any | None = None,
        search_tool: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        super().__init__(llm_client, None, config)
        self.search_tool = search_tool

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None
    ) -> SubAgentResult:
        """执行搜索任务"""
        steps = []

        search_query = await self._extract_search_query(task)
        steps.append({"step": "extract_query", "query": search_query})

        if self.search_tool:
            try:
                result = await self.search_tool.execute(query=search_query)
                steps.append({"step": "search", "success": result.success})

                if result.success:
                    summary = await self._summarize_results(search_query, result.results)
                    steps.append({"step": "summarize", "success": True})

                    return SubAgentResult(
                        success=True,
                        result=summary,
                        data=result.results,
                        steps=steps
                    )
                else:
                    return SubAgentResult(
                        success=False,
                        error=result.error,
                        steps=steps
                    )
            except Exception as e:
                return SubAgentResult(
                    success=False,
                    error=str(e),
                    steps=steps
                )

        return SubAgentResult(
            success=True,
            result=f"模拟搜索结果: {search_query}",
            steps=steps
        )

    async def _extract_search_query(self, task: str) -> str:
        """从任务中提取搜索查询"""
        if self.llm_client:
            try:
                from src.llm import Message
                prompt = f"请从以下任务中提取搜索关键词，只输出关键词：\n{task}"
                messages = [Message(role="user", content=prompt)]
                response = await self.llm_client.generate(messages=messages)
                return response.content.strip()
            except Exception:
                pass

        return task

    async def _summarize_results(
        self,
        query: str,
        results: list[Any]
    ) -> str:
        """总结搜索结果"""
        if not results:
            return f"未找到关于 '{query}' 的结果"

        summary_parts = [f"关于 '{query}' 的搜索结果：\n"]

        for i, result in enumerate(results[:5], 1):
            if hasattr(result, 'title'):
                summary_parts.append(f"{i}. {result.title}")
                if hasattr(result, 'snippet'):
                    summary_parts.append(f"   {result.snippet[:100]}...")
            else:
                summary_parts.append(f"{i}. {str(result)[:100]}")

        return "\n".join(summary_parts)
