"""ZhipuAI (智谱) LLM adapter."""

import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from src.llm.adapters.base import (
    BaseAdapter,
    LLMError,
    LLMRequest,
    LLMResponse,
    Message,
    StopReason,
    StreamChunk,
    ToolCall,
    Usage,
)

logger = logging.getLogger(__name__)


class ZhipuAdapter(BaseAdapter):
    """Adapter for ZhipuAI (智谱) API.

    Supports models:
    - glm-4
    - glm-4-flash
    - glm-4-plus
    - glm-4-air
    - glm-4v (vision)
    """

    name = "zhipu"
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "glm-4-flash",
        timeout: int = 180,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_request_body(self, request: LLMRequest) -> dict[str, Any]:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})

        for msg in request.messages:
            if isinstance(msg.content, str):
                messages.append({"role": msg.role, "content": msg.content})
            else:
                content = []
                for block in msg.content:
                    if hasattr(block, "text"):
                        content.append({"type": "text", "text": block.text})
                    elif hasattr(block, "image"):
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": block.image.to_data_url()},
                        })
                messages.append({"role": msg.role, "content": content})

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if request.tools:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema,
                    },
                }
                for t in request.tools
            ]

        if request.extra_params:
            body.update(request.extra_params)

        return body

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        content = message.get("content", "") or ""

        tool_calls = []
        for tc in message.get("tool_calls", []):
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=tc.get("function", {}).get("name", ""),
                arguments=tc.get("function", {}).get("arguments", {}),
            ))

        usage_data = data.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        finish_reason = choice.get("finish_reason", "stop")
        stop_reason = StopReason.END_TURN
        if finish_reason == "length":
            stop_reason = StopReason.MAX_TOKENS
        elif finish_reason == "tool_calls":
            stop_reason = StopReason.TOOL_USE

        return LLMResponse(
            id=data.get("id", ""),
            content=content,
            stop_reason=stop_reason,
            usage=usage,
            model=data.get("model", self.model),
            tool_calls=tool_calls,
            raw_response=data,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        body = self._build_request_body(request)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(url, json=body, headers=headers)
                    response.raise_for_status()
                    return self._parse_response(response.json())
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        raise LLMError("Authentication failed") from e
                    if e.response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            await self._get_retry_delay(attempt)
                            continue
                        raise LLMError("Rate limit exceeded") from e
                    raise LLMError(f"HTTP error: {e}") from e
                except httpx.RequestError as e:
                    if attempt < self.max_retries - 1:
                        await self._get_retry_delay(attempt)
                        continue
                    raise LLMError(f"Network error: {e}") from e

        raise LLMError("Max retries exceeded")

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        body = self._build_request_body(request)
        body["stream"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=body, headers=headers) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data = line[6:]
                    if data == "[DONE]":
                        yield StreamChunk(is_final=True)
                        break

                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})

                        content = delta.get("content", "") or ""

                        tool_calls = []
                        for tc in delta.get("tool_calls", []):
                            tool_calls.append(ToolCall(
                                id=tc.get("id", ""),
                                name=tc.get("function", {}).get("name", ""),
                                arguments=tc.get("function", {}).get("arguments", {}),
                            ))

                        finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
                        is_final = finish_reason is not None

                        yield StreamChunk(
                            content=content,
                            tool_calls=tool_calls,
                            is_final=is_final,
                            stop_reason=StopReason.END_TURN if is_final else None,
                        )
                    except Exception as e:
                        logger.warning("Failed to parse stream chunk: %s", e)
