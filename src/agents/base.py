"""
PyAgent 垂类智能体模块 - 基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRequest:
    request_id: str
    action: str
    parameters: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    request_id: str
    success: bool
    data: Any = None
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class BaseVerticalAgent(ABC):
    """垂类智能体基类"""

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: list[AgentCapability],
        llm_client: Any | None = None
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.llm_client = llm_client
        self._status = AgentStatus.IDLE
        self._initialized = False
        self._request_handlers: dict[str, Callable] = {}

    @property
    def status(self) -> AgentStatus:
        return self._status

    def get_capabilities(self) -> list[AgentCapability]:
        return self.capabilities

    def has_capability(self, capability_name: str) -> bool:
        return any(c.name == capability_name for c in self.capabilities)

    def initialize(self) -> bool:
        if self._initialized:
            return True

        try:
            self._setup_handlers()
            self._initialized = True
            self._status = AgentStatus.IDLE
            return True
        except Exception:
            self._status = AgentStatus.ERROR
            return False

    def shutdown(self) -> None:
        self._initialized = False
        self._status = AgentStatus.OFFLINE
        self._request_handlers.clear()

    @abstractmethod
    def _setup_handlers(self) -> None:
        pass

    def register_handler(self, action: str, handler: Callable) -> None:
        self._request_handlers[action] = handler

    def validate_request(self, request: AgentRequest) -> bool:
        if not self._initialized:
            return False

        if request.action not in self._request_handlers:
            return False

        return True

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        if not self.validate_request(request):
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                error="Invalid request"
            )

        self._status = AgentStatus.BUSY

        try:
            handler = self._request_handlers.get(request.action)
            if handler:
                result = await handler(request.parameters)
                self._status = AgentStatus.IDLE
                return AgentResponse(
                    request_id=request.request_id,
                    success=True,
                    data=result
                )
            else:
                self._status = AgentStatus.IDLE
                return AgentResponse(
                    request_id=request.request_id,
                    success=False,
                    error=f"No handler for action: {request.action}"
                )
        except Exception as e:
            self._status = AgentStatus.ERROR
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self._status.value,
            "capabilities": [
                {"name": c.name, "description": c.description}
                for c in self.capabilities
            ],
            "initialized": self._initialized,
        }
