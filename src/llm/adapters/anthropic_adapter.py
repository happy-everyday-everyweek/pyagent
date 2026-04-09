"""
PyAgent LLM适配器 - Anthropic适配器
"""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .base import (
    BaseAdapter,
    LLMError,
    LLMRequest,
    LLMResponse,
    RateLimitError,
    StopReason,
    StreamChunk,
    ToolCall,
    Usage,
)


class AnthropicAdapter(BaseAdapter):
    """Anthropic Claude API适配器"""

    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "claude-3-sonnet-20240229",
        timeout: int = 180,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        super().__init__(api_key, base_url, model, timeout, max_retries, retry_delay)
        self._api_base = base_url or "https://api.anthropic.com"
        self._headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成响应"""
        url = f"{self._api_base}/v1/messages"

        payload = self._build_payload(request)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(url, headers=self._headers, json=payload)

                    if response.status_code == 429:
                        raise RateLimitError("Rate limit exceeded")

                    response.raise_for_status()
                    data = response.json()
                    return self._parse_response(data)

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        raise RateLimitError("Rate limit exceeded") from e
                    if attempt < self.max_retries - 1:
                        continue
                    raise LLMError(f"HTTP error: {e}") from e
                except httpx.RequestError as e:
                    if attempt < self.max_retries - 1:
                        continue
                    raise LLMError(f"Request error: {e}") from e

        raise LLMError("Max retries exceeded")

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """流式生成响应"""
        url = f"{self._api_base}/v1/messages"

        payload = self._build_payload(request)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, headers=self._headers, json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        chunk = self._parse_stream_chunk(data)
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

    def _build_payload(self, request: LLMRequest) -> dict[str, Any]:
        """构建请求载荷"""
        messages = []
        for msg in request.messages:
            if isinstance(msg.content, str):
                messages.append({"role": msg.role, "content": msg.content})
            else:
                content = []
                for block in msg.content:
                    content.append(block.to_dict())
                messages.append({"role": msg.role, "content": content})

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "messages": messages,
        }

        if request.system:
            payload["system"] = request.system

        if request.tools:
            payload["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in request.tools
            ]

        if request.temperature is not None:
            payload["temperature"] = request.temperature

        return payload

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        """解析响应"""
        content = ""
        tool_calls = []

        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    arguments=block.get("input", {}),
                ))

        stop_reason_str = data.get("stop_reason", "end_turn")
        try:
            stop_reason = StopReason(stop_reason_str)
        except ValueError:
            stop_reason = StopReason.END_TURN

        usage_data = data.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        )

        return LLMResponse(
            id=data.get("id", ""),
            content=content,
            stop_reason=stop_reason,
            usage=usage,
            model=data.get("model", self.model),
            tool_calls=tool_calls,
            raw_response=data,
        )

    def _parse_stream_chunk(self, data: dict[str, Any]) -> StreamChunk | None:
        """解析流式响应块"""
        event_type = data.get("type", "")

        if event_type == "content_block_delta":
            delta = data.get("delta", {})
            if delta.get("type") == "text_delta":
                return StreamChunk(content=delta.get("text", ""))

        elif event_type == "content_block_start":
            block = data.get("content_block", {})
            if block.get("type") == "tool_use":
                return StreamChunk(
                    tool_calls=[ToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        arguments={},
                    )]
                )

        elif event_type == "message_stop":
            return StreamChunk(is_final=True)

        elif event_type == "message_delta":
            usage_data = data.get("usage", {})
            if usage_data:
                return StreamChunk(
                    is_final=True,
                    usage=Usage(
                        output_tokens=usage_data.get("output_tokens", 0),
                    )
                )

        return None
