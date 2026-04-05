"""
PyAgent 聊天Agent核心 - 回复生成器管理器

参考MaiBot的ReplyerManager设计，管理回复生成器实例。
"""

from typing import Any

from .base_generator import BaseReplyer
from .group_generator import GroupReplyer
from .private_generator import PrivateReplyer


class ReplyerManager:
    """回复生成器管理器"""

    def __init__(self):
        self._repliers: dict[str, BaseReplyer] = {}

    def get_replyer(
        self,
        chat_id: str,
        chat_stream: Any | None = None,
        llm_client: Any | None = None,
        is_group_chat: bool = True,
        request_type: str = "replyer"
    ) -> BaseReplyer | None:
        """获取或创建回复生成器实例"""
        if not chat_id:
            return None

        if chat_id in self._repliers:
            return self._repliers[chat_id]

        if is_group_chat:
            replyer = GroupReplyer(
                chat_id=chat_id,
                llm_client=llm_client
            )
        else:
            replyer = PrivateReplyer(
                chat_id=chat_id,
                llm_client=llm_client
            )

        self._repliers[chat_id] = replyer
        return replyer

    def remove_replyer(self, chat_id: str) -> None:
        """移除回复生成器"""
        if chat_id in self._repliers:
            del self._repliers[chat_id]

    def clear_all(self) -> None:
        """清空所有回复生成器"""
        self._repliers.clear()

    def has_replyer(self, chat_id: str) -> bool:
        """检查回复生成器是否存在"""
        return chat_id in self._repliers


replyer_manager = ReplyerManager()
