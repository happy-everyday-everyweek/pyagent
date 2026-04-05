"""
PyAgent IM平台适配器 - 意图分析中间件

在消息路由前进行意图分析，实现智能路由分发。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from .base import IMMessage

logger = logging.getLogger(__name__)

Intent = None
IntentRecognizer = None
IntentRouter = None
RouteResult = None

try:
    from ..interaction.intent import Intent, IntentRecognizer, IntentRouter, RouteResult
except ImportError:
    pass


@dataclass
class ProcessedMessage:
    """处理后的消息"""
    original: IMMessage
    intent: Any = None
    route_result: Optional[Any] = None
    should_forward_to_chat: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


class IntentMiddleware:
    """意图分析中间件"""
    
    def __init__(
        self,
        recognizer: Optional[Any] = None,
        router: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None
    ):
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        self._log_intents = self.config.get("log_intents", True)
        self._available = IntentRecognizer is not None and IntentRouter is not None
        
        if self._available:
            self.recognizer = recognizer or IntentRecognizer()
            self.router = router or IntentRouter()
        else:
            self.recognizer = None
            self.router = None
            self._enabled = False
            logger.warning("Intent analysis module not available, middleware disabled")
    
    async def process(self, message: IMMessage) -> ProcessedMessage:
        """
        处理消息，进行意图分析
        
        Args:
            message: 原始消息
            
        Returns:
            ProcessedMessage: 处理后的消息
        """
        if not self._enabled or not self._available:
            return ProcessedMessage(
                original=message,
                intent=None,
                should_forward_to_chat=True
            )
        
        try:
            context = self._build_context(message)
            intent = await self.recognizer.recognize(message.content, context)
            
            if self._log_intents and intent:
                logger.info(
                    f"Intent recognized: {intent.type.name} "
                    f"(confidence: {intent.confidence:.2f}) "
                    f"for message: {message.content[:50]}..."
                )
            
            route_result = self.router.route(intent) if self.router else None
            should_forward = not intent.needs_redirect() if intent else True
            
            return ProcessedMessage(
                original=message,
                intent=intent,
                route_result=route_result,
                should_forward_to_chat=should_forward,
                extra={
                    "redirect_url": route_result.redirect_url if route_result else None,
                    "handler_name": route_result.handler_name if route_result else None
                }
            )
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return ProcessedMessage(
                original=message,
                intent=None,
                should_forward_to_chat=True
            )
    
    def _build_context(self, message: IMMessage) -> dict[str, Any]:
        """
        构建意图分析上下文
        
        Args:
            message: 消息对象
            
        Returns:
            dict: 上下文信息
        """
        return {
            "platform": message.platform,
            "chat_type": message.chat_type.value,
            "sender_id": message.sender.user_id,
            "sender_name": message.sender.name or message.sender.nickname,
            "is_at_bot": message.is_at_bot,
            "timestamp": message.timestamp
        }
    
    def enable(self) -> None:
        """启用意图分析"""
        self._enabled = True
        logger.info("Intent middleware enabled")
    
    def disable(self) -> None:
        """禁用意图分析"""
        self._enabled = False
        logger.info("Intent middleware disabled")
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled


intent_middleware = IntentMiddleware()
