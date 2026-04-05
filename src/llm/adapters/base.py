from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class StopReason(StrEnum):
    END_TURN = "end_turn"
    MAX_TOKENS = "max_tokens"
    TOOL_USE = "tool_use"
    STOP_SEQUENCE = "stop_sequence"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "Usage":
        return cls(
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )


@dataclass
class ImageContent:
    media_type: str
    data: str

    def to_data_url(self) -> str:
        return f"data:{self.media_type};base64,{self.data}"


@dataclass
class ContentBlock:
    type: str

    def to_dict(self) -> dict:
        raise NotImplementedError


@dataclass
class TextBlock(ContentBlock):
    text: str
    type: str = field(default="text", init=False)

    def to_dict(self) -> dict:
        return {"type": "text", "text": self.text}


@dataclass
class ImageBlock(ContentBlock):
    image: ImageContent
    type: str = field(default="image", init=False)

    def to_dict(self) -> dict:
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": self.image.media_type,
                "data": self.image.data,
            },
        }


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class ToolUseBlock(ContentBlock):
    id: str
    name: str
    input: dict
    type: str = field(default="tool_use", init=False)

    def to_dict(self) -> dict:
        return {
            "type": "tool_use",
            "id": self.id,
            "name": self.name,
            "input": self.input,
        }


@dataclass
class ToolResultBlock(ContentBlock):
    tool_use_id: str
    content: str
    is_error: bool = False
    type: str = field(default="tool_result", init=False)

    def to_dict(self) -> dict:
        result = {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "content": self.content,
        }
        if self.is_error:
            result["is_error"] = True
        return result


ContentBlockType = TextBlock | ImageBlock | ToolUseBlock | ToolResultBlock


@dataclass
class Message:
    role: str
    content: str | list[ContentBlockType]

    def to_dict(self) -> dict:
        if isinstance(self.content, str):
            return {"role": self.role, "content": self.content}
        return {
            "role": self.role,
            "content": [block.to_dict() for block in self.content],
        }


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class LLMRequest:
    messages: list[Message]
    system: str = ""
    tools: list[Tool] | None = None
    max_tokens: int = 4096
    temperature: float = 1.0
    extra_params: dict | None = None

    def to_dict(self) -> dict:
        result = {
            "messages": [msg.to_dict() for msg in self.messages],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if self.system:
            result["system"] = self.system
        if self.tools:
            result["tools"] = [tool.to_dict() for tool in self.tools]
        return result


@dataclass
class LLMResponse:
    id: str
    content: str
    stop_reason: StopReason
    usage: Usage
    model: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    reasoning_content: str | None = None
    raw_response: Any = None

    @property
    def text(self) -> str:
        return self.content or ""

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "stop_reason": self.stop_reason.value,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
            },
            "model": self.model,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
        }


@dataclass
class StreamChunk:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    is_final: bool = False
    usage: Usage | None = None
    stop_reason: StopReason | None = None


class LLMError(Exception):
    pass


class AuthenticationError(LLMError):
    pass


class RateLimitError(LLMError):
    pass


class NetworkError(LLMError):
    pass


class ModelNotFoundError(LLMError):
    pass


class BaseAdapter(ABC):
    name: str = "base"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "",
        timeout: int = 180,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError("generate() must be implemented by subclass")

    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        raise NotImplementedError("generate_stream() must be implemented by subclass")
        yield StreamChunk()

    async def health_check(self) -> bool:
        try:
            request = LLMRequest(
                messages=[Message(role="user", content="Hi")],
                max_tokens=10,
            )
            response = await self.generate(request)
            return bool(response.content)
        except Exception:
            return False

    def _get_retry_delay(self, attempt: int) -> float:
        return self.retry_delay * (2**attempt)
