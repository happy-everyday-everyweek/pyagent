"""
PyAgent IM平台适配器 - 消息路由器

路由消息到正确的处理器。
"""

import logging
from collections.abc import Callable
from typing import Any, Optional

from .base import BaseIMAdapter, IMMessage, IMReply
from .intent_middleware import IntentMiddleware, ProcessedMessage
from .verification.middleware import VerificationMiddleware, verification_middleware

logger = logging.getLogger(__name__)


class MessageRouter:
    """消息路由器"""

    def __init__(
        self,
        enable_intent_analysis: bool = True,
        enable_verification: bool = True
    ):
        self._adapters: dict[str, BaseIMAdapter] = {}
        self._handlers: list[Callable] = []
        self._platform_handlers: dict[str, list[Callable]] = {}
        self._intent_middleware: Optional[IntentMiddleware] = None
        self._verification_middleware: Optional[VerificationMiddleware] = None
        self._enable_intent_analysis = enable_intent_analysis
        self._enable_verification = enable_verification
        self._intent_handlers: dict[str, Callable] = {}
        
        if enable_intent_analysis:
            self._intent_middleware = IntentMiddleware()
        
        if enable_verification:
            self._verification_middleware = verification_middleware

    def register_adapter(self, adapter: BaseIMAdapter) -> None:
        """注册适配器"""
        platform = adapter.get_platform_name()
        self._adapters[platform] = adapter

        adapter.register_message_handler(self._route_message)

    def unregister_adapter(self, platform: str) -> None:
        """注销适配器"""
        if platform in self._adapters:
            adapter = self._adapters.pop(platform)
            adapter.unregister_message_handler(self._route_message)

    def register_handler(
        self,
        handler: Callable,
        platform: str | None = None
    ) -> None:
        """注册消息处理器"""
        if platform:
            if platform not in self._platform_handlers:
                self._platform_handlers[platform] = []
            self._platform_handlers[platform].append(handler)
        else:
            self._handlers.append(handler)

    def register_intent_handler(
        self,
        intent_type: str,
        handler: Callable
    ) -> None:
        """
        注册意图处理器
        
        Args:
            intent_type: 意图类型名称（如 "OPEN_FILE", "CREATE_EVENT" 等）
            handler: 处理函数，接收 ProcessedMessage 对象
        """
        self._intent_handlers[intent_type] = handler
        logger.info(f"Registered intent handler for: {intent_type}")

    def unregister_handler(
        self,
        handler: Callable,
        platform: str | None = None
    ) -> None:
        """注销消息处理器"""
        if platform:
            if platform in self._platform_handlers:
                if handler in self._platform_handlers[platform]:
                    self._platform_handlers[platform].remove(handler)
        else:
            if handler in self._handlers:
                self._handlers.remove(handler)

    async def _route_message(self, message: IMMessage) -> None:
        """路由消息"""
        if self._verification_middleware:
            allowed, reply = await self._verification_middleware.process(message)
            if not allowed:
                if reply:
                    await self.send_message(
                        message.platform,
                        message.chat_id,
                        reply
                    )
                return
        
        processed = await self._analyze_and_route(message)
        
        if processed.should_forward_to_chat:
            for handler in self._handlers:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Message handler error: {e}")

            platform_handlers = self._platform_handlers.get(message.platform, [])
            for handler in platform_handlers:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Platform handler error: {e}")

    async def _analyze_and_route(self, message: IMMessage) -> ProcessedMessage:
        """
        分析意图并路由
        
        Args:
            message: 原始消息
            
        Returns:
            ProcessedMessage: 处理后的消息
        """
        if not self._intent_middleware:
            from .intent_middleware import ProcessedMessage
            return ProcessedMessage(
                original=message,
                intent=None,
                should_forward_to_chat=True
            )
        
        processed = await self._intent_middleware.process(message)
        
        if processed.route_result and processed.route_result.redirect_url:
            intent_type_name = processed.intent.type.name
            handler = self._intent_handlers.get(intent_type_name)
            
            if handler:
                try:
                    await handler(processed)
                    logger.info(
                        f"Intent {intent_type_name} handled by custom handler, "
                        f"redirect: {processed.route_result.redirect_url}"
                    )
                except Exception as e:
                    logger.error(f"Intent handler error: {e}")
            else:
                logger.info(
                    f"Intent {intent_type_name} needs redirect to: "
                    f"{processed.route_result.redirect_url}"
                )
        
        return processed

    async def send_message(
        self,
        platform: str,
        chat_id: str,
        content: str,
        **kwargs
    ) -> bool:
        """发送消息"""
        from .base import IMReply

        adapter = self._adapters.get(platform)
        if not adapter:
            print(f"Adapter not found for platform: {platform}")
            return False

        reply = IMReply(content=content, **kwargs)
        return await adapter.send_message(chat_id, reply)

    def get_adapter(self, platform: str) -> BaseIMAdapter | None:
        """获取适配器"""
        return self._adapters.get(platform)

    def list_platforms(self) -> list[str]:
        """列出所有平台"""
        return list(self._adapters.keys())

    async def connect_all(self) -> dict[str, bool]:
        """连接所有适配器"""
        results = {}
        for platform, adapter in self._adapters.items():
            try:
                results[platform] = await adapter.connect()
            except Exception as e:
                print(f"Failed to connect {platform}: {e}")
                results[platform] = False
        return results

    async def disconnect_all(self) -> None:
        """断开所有适配器"""
        for adapter in self._adapters.values():
            try:
                await adapter.disconnect()
            except Exception as e:
                print(f"Failed to disconnect: {e}")


message_router = MessageRouter()
