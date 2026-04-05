import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .base import (
    AuthenticationError,
    BaseAdapter,
    ContentBlockType,
    ImageBlock,
    LLMError,
    LLMRequest,
    LLMResponse,
    NetworkError,
    RateLimitError,
    StopReason,
    StreamChunk,
    Tool,
    ToolCall,
    Usage,
)

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseAdapter):
    name = "openai"

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    PROVIDER_BASE_URLS = {
        "openai": DEFAULT_BASE_URL,
        "deepseek": DEEPSEEK_BASE_URL,
        "zhipu": ZHIPU_BASE_URL,
    }

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "gpt-4o",
        timeout: int = 180,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        provider: str = "openai",
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.PROVIDER_BASE_URLS.get(provider, self.DEFAULT_BASE_URL),
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self.provider = provider
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _build_messages(self, request: LLMRequest) -> list[dict]:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})

        for msg in request.messages:
            if isinstance(msg.content, str):
                messages.append({"role": msg.role, "content": msg.content})
            else:
                content_parts = self._convert_content_blocks(msg.content)
                messages.append({"role": msg.role, "content": content_parts})

        return messages

    def _convert_content_blocks(self, blocks: list[ContentBlockType]) -> list[dict]:
        parts = []
        for block in blocks:
            if isinstance(block, ImageBlock):
                parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": block.image.to_data_url(),
                    },
                })
            elif hasattr(block, "text"):
                parts.append({"type": "text", "text": getattr(block, "text", "")})
        return parts

    def _build_tools(self, tools: list[Tool] | None) -> list[dict] | None:
        if not tools:
            return None

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]

    def _parse_response(self, response_data: dict) -> LLMResponse:
        choices = response_data.get("choices", [])
        if not choices:
            raise LLMError("No choices in response")

        choice = choices[0]
        message = choice.get("message", {})
        content = message.get("content", "") or ""
        finish_reason = choice.get("finish_reason", "stop")

        stop_reason_map = {
            "stop": StopReason.END_TURN,
            "length": StopReason.MAX_TOKENS,
            "tool_calls": StopReason.TOOL_USE,
            "content_filter": StopReason.STOP_SEQUENCE,
        }
        stop_reason = stop_reason_map.get(finish_reason, StopReason.END_TURN)

        tool_calls = []
        raw_tool_calls = message.get("tool_calls", [])
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            args_str = func.get("arguments", "{}")
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id", str(uuid.uuid4())),
                name=func.get("name", ""),
                arguments=args,
            ))

        usage_data = response_data.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return LLMResponse(
            id=response_data.get("id", str(uuid.uuid4())),
            content=content,
            stop_reason=stop_reason,
            usage=usage,
            model=response_data.get("model", self.model),
            tool_calls=tool_calls,
            raw_response=response_data,
        )

    def _handle_error(self, status_code: int, error_data: dict) -> None:
        error_msg = error_data.get("error", {}).get("message", str(error_data))

        if status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_msg}")
        elif status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {error_msg}")
        elif status_code >= 500:
            raise NetworkError(f"Server error: {error_msg}")
        else:
            raise LLMError(f"API error ({status_code}): {error_msg}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        client = await self._get_client()
        messages = self._build_messages(request)
        tools = self._build_tools(request.tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        if request.extra_params:
            payload.update(request.extra_params)

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                )

                if response.status_code != 200:
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {"error": {"message": response.text}}
                    self._handle_error(response.status_code, error_data)

                response_data = response.json()
                return self._parse_response(response_data)

            except (AuthenticationError, RateLimitError):
                raise
            except httpx.TimeoutException as e:
                last_error = NetworkError(f"Request timeout: {e}")
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries}")
            except httpx.NetworkError as e:
                last_error = NetworkError(f"Network error: {e}")
                logger.warning(f"Network error on attempt {attempt + 1}/{self.max_retries}")
            except LLMError:
                raise
            except Exception as e:
                last_error = LLMError(f"Unexpected error: {e}")
                logger.error(f"Unexpected error on attempt {attempt + 1}/{self.max_retries}: {e}")

            if attempt < self.max_retries - 1:
                delay = self._get_retry_delay(attempt)
                await asyncio.sleep(delay)

        raise last_error or LLMError("All retries failed")

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        client = await self._get_client()
        messages = self._build_messages(request)
        tools = self._build_tools(request.tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        if request.extra_params:
            payload.update(request.extra_params)

        accumulated_content = ""
        tool_calls_buffer: dict[int, dict] = {}
        usage: Usage | None = None
        finish_reason: str | None = None

        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    try:
                        error_data = await response.aread()
                        error_json = json.loads(error_data)
                    except Exception:
                        error_json = {"error": {"message": response.text}}
                    self._handle_error(response.status_code, error_json)

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[6:]
                    if data == "[DONE]":
                        break

                    try:
                        chunk_data = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk_data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason")

                    content = delta.get("content", "")
                    if content:
                        accumulated_content += content
                        yield StreamChunk(content=content)

                    raw_tool_calls = delta.get("tool_calls", [])
                    for tc in raw_tool_calls:
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": tc.get("id", ""),
                                "name": "",
                                "arguments": "",
                            }
                        func = tc.get("function", {})
                        if func.get("name"):
                            tool_calls_buffer[idx]["name"] = func["name"]
                        if func.get("arguments"):
                            tool_calls_buffer[idx]["arguments"] += func["arguments"]

                    if "usage" in chunk_data:
                        usage_data = chunk_data["usage"]
                        usage = Usage(
                            input_tokens=usage_data.get("prompt_tokens", 0),
                            output_tokens=usage_data.get("completion_tokens", 0),
                            total_tokens=usage_data.get("total_tokens", 0),
                        )

        except (AuthenticationError, RateLimitError):
            raise
        except httpx.TimeoutException as e:
            raise NetworkError(f"Stream timeout: {e}") from e
        except httpx.NetworkError as e:
            raise NetworkError(f"Stream network error: {e}") from e

        tool_calls = []
        for idx in sorted(tool_calls_buffer.keys()):
            tc_data = tool_calls_buffer[idx]
            try:
                args = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(
                id=tc_data["id"] or str(uuid.uuid4()),
                name=tc_data["name"],
                arguments=args,
            ))

        stop_reason_map = {
            "stop": StopReason.END_TURN,
            "length": StopReason.MAX_TOKENS,
            "tool_calls": StopReason.TOOL_USE,
        }

        yield StreamChunk(
            content="",
            tool_calls=tool_calls,
            is_final=True,
            usage=usage,
            stop_reason=stop_reason_map.get(finish_reason, StopReason.END_TURN) if finish_reason else None,
        )
