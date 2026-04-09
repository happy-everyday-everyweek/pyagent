"""
PyAgent IM通道验证 - 中间件

验证中间件，拦截未验证用户的消息。
"""

import logging
import re

from ..base import IMMessage
from .manager import IMVerificationManager, verification_manager

logger = logging.getLogger(__name__)


class VerificationMiddleware:
    """验证中间件"""

    CODE_PATTERN = re.compile(r"^\d{6}$")

    def __init__(self, manager: IMVerificationManager | None = None):
        self.manager = manager or verification_manager
        self._enabled = True
        self._admin_users: set[str] = set()

    def set_admin_users(self, admin_ids: list[str]) -> None:
        """设置管理员用户ID列表"""
        self._admin_users = set(admin_ids)

    def enable(self) -> None:
        """启用验证"""
        self._enabled = True
        logger.info("Verification middleware enabled")

    def disable(self) -> None:
        """禁用验证"""
        self._enabled = False
        logger.info("Verification middleware disabled")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

    async def process(self, message: IMMessage) -> tuple[bool, str | None]:
        """
        处理消息，检查验证状态
        
        Args:
            message: IM消息
            
        Returns:
            tuple[bool, Optional[str]]: (是否允许通过, 回复消息)
        """
        if not self._enabled:
            return True, None

        if message.chat_type.value != "private":
            return True, None

        user_id = message.sender.user_id
        platform = message.platform

        if user_id in self._admin_users:
            return True, None

        if self.manager.is_verified(user_id):
            return True, None

        content = message.content.strip()

        if self.CODE_PATTERN.match(content):
            success, reply = self.manager.verify(user_id, content, message.sender.nickname)
            return False, reply

        session = self.manager.get_pending_session(user_id)
        if session:
            return False, f"请回复 6 位验证码完成验证。验证码有效期 {self.manager.expire_minutes} 分钟。"

        guide_message = self.manager.get_verification_guide_message(user_id, platform)
        return False, guide_message

    def should_intercept(self, message: IMMessage) -> bool:
        """
        检查是否应该拦截消息
        
        Args:
            message: IM消息
            
        Returns:
            bool: 是否应该拦截
        """
        if not self._enabled:
            return False

        if message.chat_type.value != "private":
            return False

        user_id = message.sender.user_id

        if user_id in self._admin_users:
            return False

        return not self.manager.is_verified(user_id)


verification_middleware = VerificationMiddleware()
