"""Middleware system for PyAgent execution pipeline.

This module provides a middleware chain architecture for processing
agent execution lifecycle events. Middlewares can intercept and modify
state at various stages of execution.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.execution.context import ExecutionContext


class MiddlewarePhase(Enum):
    """Execution phases where middleware can be applied."""

    BEFORE_AGENT = "before_agent"
    AFTER_AGENT = "after_agent"
    BEFORE_MODEL = "before_model"
    AFTER_MODEL = "after_model"
    BEFORE_TOOL = "before_tool"
    AFTER_TOOL = "after_tool"


@dataclass
class MiddlewareResult:
    """Result returned by middleware execution."""

    state_update: dict[str, Any] = field(default_factory=dict)
    should_continue: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseMiddleware(ABC):
    """Abstract base class for all middlewares.

    Middlewares intercept agent execution at various phases and can
    modify state, short-circuit execution, or perform side effects.
    """

    name: str = "base_middleware"
    priority: int = 100
    enabled: bool = True
    phases: list[MiddlewarePhase] = field(default_factory=list)

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def process(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        """Process the middleware logic.

        Args:
            phase: Current execution phase.
            state: Current agent state.
            context: Execution context with metadata.

        Returns:
            MiddlewareResult with state updates and control flags.
        """

    def should_run(self, phase: MiddlewarePhase, state: dict[str, Any]) -> bool:
        """Check if this middleware should run for the given phase.

        Args:
            phase: Current execution phase.
            state: Current agent state.

        Returns:
            True if middleware should execute.
        """
        return self.enabled and phase in self.phases

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(priority={self.priority}, enabled={self.enabled})"


class MiddlewareChain:
    """Chain of middlewares executed in priority order.

    Middlewares are sorted by priority (lower = earlier execution).
    Each middleware can modify state and control flow.
    """

    def __init__(self):
        self._middlewares: list[BaseMiddleware] = []

    def add(self, middleware: BaseMiddleware) -> "MiddlewareChain":
        """Add a middleware to the chain.

        Args:
            middleware: Middleware instance to add.

        Returns:
            Self for chaining.
        """
        self._middlewares.append(middleware)
        self._middlewares.sort(key=lambda m: m.priority)
        return self

    def remove(self, name: str) -> bool:
        """Remove a middleware by name.

        Args:
            name: Name of middleware to remove.

        Returns:
            True if middleware was found and removed.
        """
        for i, m in enumerate(self._middlewares):
            if m.name == name:
                self._middlewares.pop(i)
                return True
        return False

    def get(self, name: str) -> BaseMiddleware | None:
        """Get a middleware by name.

        Args:
            name: Name of middleware to find.

        Returns:
            Middleware instance or None if not found.
        """
        for m in self._middlewares:
            if m.name == name:
                return m
        return None

    def execute(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Execute all applicable middlewares for a phase.

        Args:
            phase: Current execution phase.
            state: Current agent state.
            context: Execution context.

        Returns:
            Updated state after all middlewares have processed.
        """
        result_state = state.copy()

        for middleware in self._middlewares:
            if not middleware.should_run(phase, result_state):
                continue

            try:
                result = middleware.process(phase, result_state, context)

                if result.state_update:
                    result_state.update(result.state_update)

                if not result.should_continue:
                    break

            except Exception as e:
                result_state["_middleware_errors"] = result_state.get("_middleware_errors", [])
                result_state["_middleware_errors"].append(
                    {"middleware": middleware.name, "error": str(e)}
                )

        return result_state

    async def aexecute(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Async version of execute.

        Args:
            phase: Current execution phase.
            state: Current agent state.
            context: Execution context.

        Returns:
            Updated state after all middlewares have processed.
        """
        result_state = state.copy()

        for middleware in self._middlewares:
            if not middleware.should_run(phase, result_state):
                continue

            try:
                if hasattr(middleware, "aprocess"):
                    result = await middleware.aprocess(phase, result_state, context)
                else:
                    result = middleware.process(phase, result_state, context)

                if result.state_update:
                    result_state.update(result.state_update)

                if not result.should_continue:
                    break

            except Exception as e:
                result_state["_middleware_errors"] = result_state.get("_middleware_errors", [])
                result_state["_middleware_errors"].append(
                    {"middleware": middleware.name, "error": str(e)}
                )

        return result_state

    def __len__(self) -> int:
        return len(self._middlewares)

    def __iter__(self):
        return iter(self._middlewares)


def create_default_middleware_chain() -> MiddlewareChain:
    """Create the default middleware chain with standard middlewares.

    Returns:
        Configured MiddlewareChain instance.
    """
    from src.execution.middlewares.clarification import ClarificationMiddleware
    from src.execution.middlewares.memory import MemoryMiddleware
    from src.execution.middlewares.summarization import SummarizationMiddleware
    from src.execution.middlewares.thread_data import ThreadDataMiddleware
    from src.execution.middlewares.title import TitleMiddleware
    from src.execution.middlewares.todo_list import TodoListMiddleware
    from src.execution.middlewares.uploads import UploadsMiddleware
    from src.execution.middlewares.view_image import ViewImageMiddleware

    chain = MiddlewareChain()
    chain.add(ThreadDataMiddleware()).priority = 10
    chain.add(UploadsMiddleware()).priority = 20
    chain.add(SummarizationMiddleware()).priority = 30
    chain.add(TodoListMiddleware()).priority = 40
    chain.add(TitleMiddleware()).priority = 50
    chain.add(MemoryMiddleware()).priority = 60
    chain.add(ViewImageMiddleware()).priority = 70
    chain.add(ClarificationMiddleware()).priority = 80

    return chain
