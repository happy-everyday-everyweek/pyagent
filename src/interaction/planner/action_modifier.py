"""
PyAgent 聊天Agent核心 - 动作修改器

参考MaiBot的ActionModifier设计，根据上下文动态修改可用动作。
"""

import random
from typing import Any

from .action_manager import ActionManager
from .types import ActionActivationType, ActionInfo


class ActionModifier:
    """动作修改器"""

    def __init__(self, action_manager: ActionManager, chat_id: str):
        self.action_manager = action_manager
        self.chat_id = chat_id
        self._modification_history: list[dict[str, Any]] = []

    async def modify_actions(self) -> dict[str, ActionInfo]:
        """修改可用动作"""
        available_actions = self.action_manager.get_using_actions()
        modified_actions = {}

        for action_name, action_info in available_actions.items():
            if self._should_activate_action(action_info):
                modified_actions[action_name] = action_info

        self._modification_history.append({
            "original_count": len(available_actions),
            "modified_count": len(modified_actions),
            "actions": list(modified_actions.keys())
        })

        if len(self._modification_history) > 50:
            self._modification_history = self._modification_history[-25:]

        return modified_actions

    def _should_activate_action(self, action_info: ActionInfo) -> bool:
        """判断动作是否应该激活"""
        if action_info.activation_type == ActionActivationType.NEVER:
            return False

        if action_info.activation_type == ActionActivationType.ALWAYS:
            return True

        if action_info.activation_type == ActionActivationType.RANDOM:
            return random.random() < action_info.random_activation_probability

        if action_info.activation_type == ActionActivationType.KEYWORD:
            return self._check_keywords(action_info.activation_keywords)

        return True

    def _check_keywords(self, keywords: list[str]) -> bool:
        """检查关键词"""
        return False

    def get_modification_history(self) -> list[dict[str, Any]]:
        """获取修改历史"""
        return self._modification_history.copy()

    def clear_history(self) -> None:
        """清空历史"""
        self._modification_history.clear()
