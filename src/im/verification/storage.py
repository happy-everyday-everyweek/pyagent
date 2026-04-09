"""
PyAgent IM通道验证 - 存储模块

持久化存储验证状态。
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class VerificationStorage:
    """验证状态存储"""

    def __init__(self, db_path: str = "data/im_verification.json"):
        self.db_path = db_path
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

    def load_verified_users(self) -> dict[str, dict[str, Any]]:
        """
        从数据库加载已验证用户
        
        Returns:
            dict: 用户ID到验证信息的映射
        """
        try:
            if not os.path.exists(self.db_path):
                return {}

            with open(self.db_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("verified_users", {})
        except Exception as e:
            logger.error(f"Failed to load verified users: {e}")
            return {}

    def save_verified_users(self, verified_users: dict[str, Any]) -> bool:
        """
        保存已验证用户到数据库
        
        Args:
            verified_users: 用户ID到验证信息的映射
            
        Returns:
            bool: 是否保存成功
        """
        try:
            self._ensure_data_dir()

            data = {
                "version": 1,
                "updated_at": datetime.now().isoformat(),
                "verified_users": verified_users
            }

            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(verified_users)} verified users")
            return True
        except Exception as e:
            logger.error(f"Failed to save verified users: {e}")
            return False

    def add_verified_user(
        self,
        user_id: str,
        platform: str,
        nickname: str | None = None
    ) -> bool:
        """
        添加已验证用户
        
        Args:
            user_id: 用户ID
            platform: 平台名称
            nickname: 用户昵称
            
        Returns:
            bool: 是否添加成功
        """
        verified_users = self.load_verified_users()
        verified_users[user_id] = {
            "platform": platform,
            "verified_at": datetime.now().isoformat(),
            "nickname": nickname
        }
        return self.save_verified_users(verified_users)

    def remove_verified_user(self, user_id: str) -> bool:
        """
        移除已验证用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否移除成功
        """
        verified_users = self.load_verified_users()
        if user_id in verified_users:
            del verified_users[user_id]
            return self.save_verified_users(verified_users)
        return False

    def is_verified(self, user_id: str) -> bool:
        """
        检查用户是否已验证
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否已验证
        """
        verified_users = self.load_verified_users()
        return user_id in verified_users

    def get_verified_user(self, user_id: str) -> dict[str, Any] | None:
        """
        获取已验证用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict | None: 用户验证信息
        """
        verified_users = self.load_verified_users()
        return verified_users.get(user_id)

    def get_all_verified_users(self) -> dict[str, dict[str, Any]]:
        """
        获取所有已验证用户
        
        Returns:
            dict: 所有已验证用户
        """
        return self.load_verified_users()

    def get_verified_users_by_platform(self, platform: str) -> dict[str, dict[str, Any]]:
        """
        获取指定平台的已验证用户
        
        Args:
            platform: 平台名称
            
        Returns:
            dict: 该平台的已验证用户
        """
        verified_users = self.load_verified_users()
        return {
            user_id: info
            for user_id, info in verified_users.items()
            if info.get("platform") == platform
        }
