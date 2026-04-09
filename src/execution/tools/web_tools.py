"""
PyAgent 执行模块工具系统 - 网络请求工具
"""

from typing import Any

import httpx

from .base import BaseTool, RiskLevel, ToolCategory, ToolParameter, ToolResult


class WebRequestTool(BaseTool):
    """HTTP请求工具"""

    name = "web_request"
    description = "发送HTTP请求"
    category = ToolCategory.WEB
    risk_level = RiskLevel.LOW

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="请求URL",
                required=True
            ),
            ToolParameter(
                name="method",
                type="string",
                description="HTTP方法",
                required=False,
                default="GET",
                enum=["GET", "POST", "PUT", "DELETE", "PATCH"]
            ),
            ToolParameter(
                name="headers",
                type="object",
                description="请求头",
                required=False
            ),
            ToolParameter(
                name="body",
                type="object",
                description="请求体（JSON）",
                required=False
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="超时时间（秒）",
                required=False,
                default=30
            )
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """发送HTTP请求"""
        valid, errors = self.validate_parameters(**kwargs)
        if not valid:
            return ToolResult(success=False, error="; ".join(errors))

        url = kwargs.get("url", "")
        method = kwargs.get("method", "GET")
        headers = kwargs.get("headers", {})
        body = kwargs.get("body")
        timeout = kwargs.get("timeout", 30)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body or None
                )

                try:
                    content = response.text
                except Exception:
                    content = f"<二进制数据，大小: {len(response.content)} 字节>"

                return ToolResult(
                    success=response.is_success,
                    output=content,
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "url": str(response.url)
                    }
                )

        except httpx.TimeoutException:
            return ToolResult(success=False, error=f"请求超时（{timeout}秒）")
        except Exception as e:
            return ToolResult(success=False, error=f"请求失败: {e!s}")


class WebFetchTool(BaseTool):
    """网页抓取工具"""

    name = "web_fetch"
    description = "抓取网页内容"
    category = ToolCategory.WEB
    risk_level = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="网页URL",
                required=True
            ),
            ToolParameter(
                name="selector",
                type="string",
                description="CSS选择器（可选）",
                required=False
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="最大内容长度",
                required=False,
                default=10000
            )
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """抓取网页"""
        valid, errors = self.validate_parameters(**kwargs)
        if not valid:
            return ToolResult(success=False, error="; ".join(errors))

        url = kwargs.get("url", "")
        max_length = kwargs.get("max_length", 10000)

        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                content = response.text

                if len(content) > max_length:
                    content = content[:max_length] + "...[内容已截断]"

                return ToolResult(
                    success=True,
                    output=content,
                    metadata={
                        "url": url,
                        "size": len(response.text)
                    }
                )

        except Exception as e:
            return ToolResult(success=False, error=f"抓取失败: {e!s}")
