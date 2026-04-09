"""
PyAgent IM通道验证 - 管理器

管理用户验证流程。
"""

import logging
import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta

from .storage import VerificationStorage

logger = logging.getLogger(__name__)


@dataclass
class VerifiedUser:
    """已验证用户"""
    user_id: str
    platform: str
    verified_at: datetime
    nickname: str | None = None


@dataclass
class VerificationSession:
    """验证会话"""
    user_id: str
    platform: str
    code: str
    created_at: datetime
    expires_at: datetime
    attempts: int = 0


class IMVerificationManager:
    """IM通道验证管理器"""

    DEFAULT_CODE_LENGTH = 6
    DEFAULT_EXPIRE_MINUTES = 10
    DEFAULT_MAX_ATTEMPTS = 3

    def __init__(
        self,
        code_length: int = DEFAULT_CODE_LENGTH,
        expire_minutes: int = DEFAULT_EXPIRE_MINUTES,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        db_path: str = "data/im_verification.json"
    ):
        self.code_length = code_length
        self.expire_minutes = expire_minutes
        self.max_attempts = max_attempts
        self.storage = VerificationStorage(db_path)
        self._sessions: dict[str, VerificationSession] = {}
        self._verified_users: dict[str, VerifiedUser] = {}
        self._load_verified_users()

    def _load_verified_users(self) -> None:
        """从存储加载已验证用户"""
        users_data = self.storage.load_verified_users()
        for user_id, user_info in users_data.items():
            try:
                self._verified_users[user_id] = VerifiedUser(
                    user_id=user_id,
                    platform=user_info["platform"],
                    verified_at=datetime.fromisoformat(user_info["verified_at"]),
                    nickname=user_info.get("nickname")
                )
            except Exception as e:
                logger.error(f"Failed to load verified user {user_id}: {e}")

        logger.info(f"Loaded {len(self._verified_users)} verified users")

    def _save_verified_users(self) -> None:
        """保存已验证用户到存储"""
        users_data = {}
        for user_id, user in self._verified_users.items():
            users_data[user_id] = {
                "platform": user.platform,
                "verified_at": user.verified_at.isoformat(),
                "nickname": user.nickname
            }
        self.storage.save_verified_users(users_data)

    def generate_code(self, user_id: str, platform: str) -> str:
        """
        生成验证码
        
        Args:
            user_id: 用户ID
            platform: 平台名称
            
        Returns:
            str: 验证码
        """
        code = "".join(random.choices(string.digits, k=self.code_length))
        now = datetime.now()

        self._sessions[user_id] = VerificationSession(
            user_id=user_id,
            platform=platform,
            code=code,
            created_at=now,
            expires_at=now + timedelta(minutes=self.expire_minutes)
        )

        logger.info(f"Generated verification code for user {user_id} on {platform}")
        return code

    def verify(self, user_id: str, code: str, nickname: str | None = None) -> tuple[bool, str]:
        """
        验证验证码
        
        Args:
            user_id: 用户ID
            code: 验证码
            nickname: 用户昵称
            
        Returns:
            tuple[bool, str]: (是否验证成功, 消息)
        """
        session = self._sessions.get(user_id)

        if not session:
            return False, "请先发送消息获取验证码"

        if datetime.now() > session.expires_at:
            del self._sessions[user_id]
            return False, "验证码已过期，请重新获取"

        session.attempts += 1

        if session.attempts > self.max_attempts:
            del self._sessions[user_id]
            return False, "验证尝试次数过多，请重新获取验证码"

        if session.code != code:
            remaining = self.max_attempts - session.attempts
            return False, f"验证码错误，还剩 {remaining} 次尝试机会"

        self._verified_users[user_id] = VerifiedUser(
            user_id=user_id,
            platform=session.platform,
            verified_at=datetime.now(),
            nickname=nickname
        )
        self._save_verified_users()
        del self._sessions[user_id]

        logger.info(f"User {user_id} verified successfully on {session.platform}")
        return True, "验证成功！现在可以正常使用了"

    def is_verified(self, user_id: str) -> bool:
        """
        检查用户是否已验证
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否已验证
        """
        return user_id in self._verified_users

    def get_verified_user(self, user_id: str) -> VerifiedUser | None:
        """
        获取已验证用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            VerifiedUser | None: 用户验证信息
        """
        return self._verified_users.get(user_id)

    def revoke_verification(self, user_id: str) -> tuple[bool, str]:
        """
        撤销用户验证状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            tuple[bool, str]: (是否撤销成功, 消息)
        """
        if user_id not in self._verified_users:
            return False, "用户未验证"

        del self._verified_users[user_id]
        self._save_verified_users()

        if user_id in self._sessions:
            del self._sessions[user_id]

        logger.info(f"Revoked verification for user {user_id}")
        return True, "已撤销用户验证状态"

    def get_pending_session(self, user_id: str) -> VerificationSession | None:
        """
        获取待验证会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            VerificationSession | None: 验证会话
        """
        session = self._sessions.get(user_id)
        if session and datetime.now() <= session.expires_at:
            return session
        return None

    def is_code_expired(self, user_id: str) -> bool:
        """
        检查验证码是否过期
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否过期
        """
        session = self._sessions.get(user_id)
        if not session:
            return True
        return datetime.now() > session.expires_at

    def get_verification_guide_message(self, user_id: str, platform: str) -> str:
        """
        获取验证引导消息
        
        Args:
            user_id: 用户ID
            platform: 平台名称
            
        Returns:
            str: 引导消息
        """
        code = self.generate_code(user_id, platform)
        return (
            f"欢迎使用 PyAgent！\n\n"
            f"为了确保账户安全，请完成身份验证。\n\n"
            f"验证码：{code}\n\n"
            f"请在 {self.expire_minutes} 分钟内回复此验证码完成验证。\n"
            f"验证成功后，以后无需再次验证。"
        )

    def get_all_verified_users(self) -> dict[str, VerifiedUser]:
        """
        获取所有已验证用户
        
        Returns:
            dict: 所有已验证用户
        """
        return self._verified_users.copy()

    def get_verified_users_by_platform(self, platform: str) -> dict[str, VerifiedUser]:
        """
        获取指定平台的已验证用户
        
        Args:
            platform: 平台名称
            
        Returns:
            dict: 该平台的已验证用户
        """
        return {
            user_id: user
            for user_id, user in self._verified_users.items()
            if user.platform == platform
        }

    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的验证会话
        
        Returns:
            int: 清理的会话数量
        """
        now = datetime.now()
        expired_users = [
            user_id
            for user_id, session in self._sessions.items()
            if session.expires_at < now
        ]

        for user_id in expired_users:
            del self._sessions[user_id]

        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired sessions")

        return len(expired_users)


verification_manager = IMVerificationManager()
