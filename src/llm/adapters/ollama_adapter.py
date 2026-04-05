"""Ollama LLM adapter for local models."""

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


class OllamaAdapter(BaseAdapter):
    """Adapter for Ollama local LLM server.

    Supports any model available in Ollama:
    - llama3, llama3.1, llama3.2
    - mistral, mixtral
    - qwen2, qwen2.5
    - deepseek-coder
    - And many more...
    """

    name = "ollama"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        api_key: str = "",
        base_url: str | None = None,
        model: str = "llama3.1",
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        super().__init__(
            api_key=api_key or "ollama",
            base_url=base_url or self.DEFAULT_BASE_URL,
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

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
                            "image_url": block.image.to_data_url(),
                        })
                messages.append({"role": msg.role, "content": content})

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "options": {
                "num_predict": request.max_tokens,
                "temperature": request.temperature,
            },
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
            body["options"].update(request.extra_params)

        return body

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        message = data.get("message", {})

        content = message.get("content", "") or ""

        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            tool_calls.append(ToolCall(
                id=tc.get("id", f"call_{len(tool_calls)}"),
                name=func.get("name", ""),
                arguments=func.get("arguments", {}),
            ))

        eval_count = data.get("eval_count", 0)
        prompt_eval_count = data.get("prompt_eval_count", 0)
        usage = Usage(
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            total_tokens=prompt_eval_count + eval_count,
        )

        done_reason = data.get("done_reason", "stop")
        stop_reason = StopReason.END_TURN
        if done_reason == "length":
            stop_reason = StopReason.MAX_TOKENS

        return LLMResponse(
            id=f"ollama-{data.get('created_at', '')}",
            content=content,
            stop_reason=stop_reason,
            usage=usage,
            model=data.get("model", self.model),
            tool_calls=tool_calls,
            raw_response=data,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        body = self._build_request_body(request)
        body["stream"] = False

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(url, json=body)
                    response.raise_for_status()
                    return self._parse_response(response.json())
                except httpx.HTTPStatusError as e:
                    raise LLMError(f"HTTP error: {e}") from e
                except httpx.RequestError as e:
                    if attempt < self.max_retries - 1:
                        await self._get_retry_delay(attempt)
                        continue
                    raise LLMError(f"Network error: {e}") from e

        raise LLMError("Max retries exceeded")

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        url = f"{self.base_url}/api/chat"
        body = self._build_request_body(request)
        body["stream"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=body) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        import json
                        chunk = json.loads(line)
                        message = chunk.get("message", {})

                        content = message.get("content", "") or ""

                        tool_calls = []
                        for tc in message.get("tool_calls", []):
                            func = tc.get("function", {})
                            tool_calls.append(ToolCall(
                                id=tc.get("id", ""),
                                name=func.get("name", ""),
                                arguments=func.get("arguments", {}),
                            ))

                        is_final = chunk.get("done", False)

                        usage = None
                        if is_final:
                            eval_count = chunk.get("eval_count", 0)
                            prompt_eval_count = chunk.get("prompt_eval_count", 0)
                            usage = Usage(
                                input_tokens=prompt_eval_count,
                                output_tokens=eval_count,
                                total_tokens=prompt_eval_count + eval_count,
                            )

                        yield StreamChunk(
                            content=content,
                            tool_calls=tool_calls,
                            is_final=is_final,
                            usage=usage,
                            stop_reason=StopReason.END_TURN if is_final else None,
                        )
                    except Exception as e:
                        logger.warning("Failed to parse stream chunk: %s", e)

    async def list_models(self) -> list[str]:
        """List available models in Ollama.

        Returns:
            List of model names.
        """
        url = f"{self.base_url}/api/tags"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry.

        Args:
            model_name: Name of the model to pull.

        Returns:
            True if successful.
        """
        url = f"{self.base_url}/api/pull"
        body = {"name": model_name}

        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            return True
