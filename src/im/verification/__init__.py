"""
PyAgent IM通道验证模块

实现用户验证机制，确保只有经过验证的用户才能使用私聊功能。
"""

from .manager import IMVerificationManager, VerifiedUser, verification_manager
from .storage import VerificationStorage

__all__ = [
    "IMVerificationManager",
    "VerificationStorage",
    "VerifiedUser",
    "verification_manager",
]
