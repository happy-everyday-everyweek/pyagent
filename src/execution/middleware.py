"""
PyAgent 执行模块 - 增强型中间件系统

参考deer-flow设计，优化智能体编排架构。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MiddlewarePhase(Enum):
    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"
    ON_ERROR = "on_error"
    ON_RETRY = "on_retry"


@dataclass
class MiddlewareContext:
    task_id: str
    phase: MiddlewarePhase
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[Exception] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    def add_error(self, error: Exception) -> None:
        self.errors.append(error)

    def set_data(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class BaseMiddleware(ABC):
    """中间件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def priority(self) -> int:
        return 100

    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        phase = context.phase

        if phase == MiddlewarePhase.BEFORE_EXECUTE:
            return await self.before_execute(context)
        elif phase == MiddlewarePhase.AFTER_EXECUTE:
            return await self.after_execute(context)
        elif phase == MiddlewarePhase.ON_ERROR:
            return await self.on_error(context)
        elif phase == MiddlewarePhase.ON_RETRY:
            return await self.on_retry(context)

        return context

    async def before_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        return context

    async def after_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        return context

    async def on_error(self, context: MiddlewareContext) -> MiddlewareContext:
        return context

    async def on_retry(self, context: MiddlewareContext) -> MiddlewareContext:
        return context


class LoggingMiddleware(BaseMiddleware):
    """日志中间件"""

    @property
    def name(self) -> str:
        return "logging"

    @property
    def priority(self) -> int:
        return 10

    async def before_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        logger.info(f"[{context.task_id}] Starting execution")
        return context

    async def after_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        duration = (context.end_time or datetime.now()) - context.start_time
        logger.info(f"[{context.task_id}] Execution completed in {duration.total_seconds():.2f}s")
        return context

    async def on_error(self, context: MiddlewareContext) -> MiddlewareContext:
        for error in context.errors:
            logger.error(f"[{context.task_id}] Error: {error}")
        return context


class TimingMiddleware(BaseMiddleware):
    """计时中间件"""

    @property
    def name(self) -> str:
        return "timing"

    @property
    def priority(self) -> int:
        return 5

    async def before_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        context.metadata["timing_start"] = datetime.now()
        return context

    async def after_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        start = context.metadata.get("timing_start", context.start_time)
        duration = (datetime.now() - start).total_seconds()
        context.metadata["duration_seconds"] = duration
        return context


class RetryMiddleware(BaseMiddleware):
    """重试中间件"""

    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay

    @property
    def name(self) -> str:
        return "retry"

    @property
    def priority(self) -> int:
        return 20

    async def on_error(self, context: MiddlewareContext) -> MiddlewareContext:
        retry_count = context.metadata.get("retry_count", 0)

        if retry_count < self.max_retries:
            context.metadata["retry_count"] = retry_count + 1
            context.metadata["should_retry"] = True
            logger.warning(f"[{context.task_id}] Retrying ({retry_count + 1}/{self.max_retries})")
            await asyncio.sleep(self.delay * (retry_count + 1))
        else:
            context.metadata["should_retry"] = False
            logger.error(f"[{context.task_id}] Max retries exceeded")

        return context


class CacheMiddleware(BaseMiddleware):
    """缓存中间件"""

    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self._cache: dict[str, tuple[Any, datetime]] = {}

    @property
    def name(self) -> str:
        return "cache"

    @property
    def priority(self) -> int:
        return 15

    async def before_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        cache_key = self._get_cache_key(context)
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.ttl:
                context.metadata["cache_hit"] = True
                context.data["result"] = cached_data
                logger.debug(f"[{context.task_id}] Cache hit")
        return context

    async def after_execute(self, context: MiddlewareContext) -> MiddlewareContext:
        if not context.metadata.get("cache_hit"):
            cache_key = self._get_cache_key(context)
            result = context.data.get("result")
            if result:
                self._cache[cache_key] = (result, datetime.now())
        return context

    def _get_cache_key(self, context: MiddlewareContext) -> str:
        import hashlib
        import json
        key_data = json.dumps(context.data, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()


class MiddlewarePipeline:
    """中间件管道"""

    def __init__(self):
        self._middlewares: list[BaseMiddleware] = []

    def add(self, middleware: BaseMiddleware) -> "MiddlewarePipeline":
        self._middlewares.append(middleware)
        self._middlewares.sort(key=lambda m: m.priority)
        return self

    def remove(self, name: str) -> bool:
        for i, mw in enumerate(self._middlewares):
            if mw.name == name:
                del self._middlewares[i]
                return True
        return False

    async def execute(
        self,
        task_id: str,
        phase: MiddlewarePhase,
        executor: Callable,
        *args,
        **kwargs
    ) -> MiddlewareContext:
        context = MiddlewareContext(task_id=task_id, phase=phase)

        for middleware in self._middlewares:
            try:
                context = await middleware.process(context)
            except Exception as e:
                logger.error(f"Middleware {middleware.name} failed: {e}")
                context.add_error(e)

        if phase == MiddlewarePhase.BEFORE_EXECUTE:
            try:
                result = await executor(*args, **kwargs)
                context.data["result"] = result
            except Exception as e:
                context.add_error(e)

        context.end_time = datetime.now()

        for middleware in self._middlewares:
            try:
                context = await middleware.process(context)
            except Exception as e:
                logger.error(f"Middleware {middleware.name} failed in post-processing: {e}")

        return context


class EnhancedCollaborationManager:
    """增强型协作管理器

    集成中间件系统的协作管理器。
    """

    def __init__(self):
        self.pipeline = MiddlewarePipeline()
        self.pipeline.add(LoggingMiddleware())
        self.pipeline.add(TimingMiddleware())
        self.pipeline.add(RetryMiddleware())

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        self.pipeline.add(middleware)

    async def execute_with_middleware(
        self,
        task_id: str,
        executor: Callable,
        *args,
        **kwargs
    ) -> Any:
        context = await self.pipeline.execute(
            task_id=task_id,
            phase=MiddlewarePhase.BEFORE_EXECUTE,
            executor=executor,
            *args,
            **kwargs
        )

        if context.errors:
            error_context = MiddlewareContext(
                task_id=task_id,
                phase=MiddlewarePhase.ON_ERROR
            )
            error_context.errors = context.errors
            error_context.data = context.data

            for middleware in self.pipeline._middlewares:
                await middleware.on_error(error_context)

        return context.data.get("result")


enhanced_collaboration = EnhancedCollaborationManager()
