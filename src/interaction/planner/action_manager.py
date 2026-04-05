"""
PyAgent 聊天Agent核心 - 动作管理器

参考MaiBot的ActionManager设计，管理可用动作的注册和创建。
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .types import ActionActivationType, ActionInfo


@dataclass
class ActionHandler:
    """动作处理器"""
    name: str
    handler: Callable
    description: str = ""
    parameters: dict[str, str] = field(default_factory=dict)
    requirements: list[str] = field(default_factory=list)


class ActionManager:
    """动作管理器"""

    def __init__(self):
        self._actions: dict[str, ActionInfo] = {}
        self._handlers: dict[str, ActionHandler] = {}
        self._using_actions: dict[str, ActionInfo] = {}

    def register_action(
        self,
        name: str,
        description: str = "",
        parameters: dict[str, str] | None = None,
        requirements: list[str] | None = None,
        parallel_action: bool = True,
        activation_type: ActionActivationType = ActionActivationType.ALWAYS,
        activation_keywords: list[str] | None = None,
        random_activation_probability: float = 0.5,
        handler: Callable | None = None
    ) -> None:
        """注册动作"""
        action_info = ActionInfo(
            name=name,
            description=description,
            parameters=parameters or {},
            requirements=requirements or [],
            parallel_action=parallel_action,
            activation_type=activation_type,
            activation_keywords=activation_keywords or [],
            random_activation_probability=random_activation_probability
        )

        self._actions[name] = action_info
        self._using_actions[name] = action_info

        if handler:
            self._handlers[name] = ActionHandler(
                name=name,
                handler=handler,
                description=description,
                parameters=parameters or {},
                requirements=requirements or []
            )

    def unregister_action(self, name: str) -> None:
        """注销动作"""
        if name in self._actions:
            del self._actions[name]
        if name in self._using_actions:
            del self._using_actions[name]
        if name in self._handlers:
            del self._handlers[name]

    def enable_action(self, name: str) -> None:
        """启用动作"""
        if name in self._actions:
            self._using_actions[name] = self._actions[name]

    def disable_action(self, name: str) -> None:
        """禁用动作"""
        if name in self._using_actions:
            del self._using_actions[name]

    def get_action(self, name: str) -> ActionInfo | None:
        """获取动作信息"""
        return self._actions.get(name)

    def get_using_actions(self) -> dict[str, ActionInfo]:
        """获取可用动作"""
        return self._using_actions.copy()

    def get_all_actions(self) -> dict[str, ActionInfo]:
        """获取所有动作"""
        return self._actions.copy()

    def get_handler(self, name: str) -> ActionHandler | None:
        """获取动作处理器"""
        return self._handlers.get(name)

    def create_action(
        self,
        action_name: str,
        action_data: dict[str, Any] | None = None,
        **kwargs
    ) -> ActionHandler | None:
        """创建动作处理器实例"""
        handler = self._handlers.get(action_name)
        if handler:
            return handler
        return None

    def has_action(self, name: str) -> bool:
        """检查动作是否存在"""
        return name in self._actions

    def is_action_enabled(self, name: str) -> bool:
        """检查动作是否启用"""
        return name in self._using_actions


def create_default_action_manager() -> ActionManager:
    """创建默认动作管理器"""
    manager = ActionManager()

    manager.register_action(
        name="reply",
        description="回复消息",
        parameters={
            "target_message_id": "目标消息ID",
            "think_level": "思考深度(0或1)",
            "unknown_words": "未知词语列表",
            "quote": "是否引用回复"
        },
        requirements=[
            "可以回复呼叫了你的名字但未回应的消息",
            "可以顺着聊天内容自然回复",
            "不要回复自己发送的消息"
        ],
        parallel_action=False
    )

    manager.register_action(
        name="no_reply",
        description="保持沉默，不回复",
        parameters={},
        requirements=[
            "保持沉默直到有新消息",
            "控制聊天频率"
        ],
        parallel_action=False
    )

    manager.register_action(
        name="search",
        description="搜索信息",
        parameters={
            "query": "搜索查询内容",
            "target_message_id": "目标消息ID"
        },
        requirements=[
            "当需要搜索外部信息时使用"
        ],
        parallel_action=True
    )

    manager.register_action(
        name="execute",
        description="执行任务",
        parameters={
            "task": "要执行的任务",
            "async_mode": "是否异步执行",
            "target_message_id": "目标消息ID"
        },
        requirements=[
            "当需要执行具体操作任务时使用"
        ],
        parallel_action=True
    )

    manager.register_action(
        name="read",
        description="阅读文件或网页",
        parameters={
            "path": "文件路径或URL",
            "target_message_id": "目标消息ID"
        },
        requirements=[
            "当需要阅读文件或网页内容时使用"
        ],
        parallel_action=True
    )

    manager.register_action(
        name="memory",
        description="操作记忆",
        parameters={
            "operation": "操作类型：store/retrieve/forget",
            "content": "记忆内容",
            "target_message_id": "目标消息ID"
        },
        requirements=[
            "当需要存储或检索记忆时使用"
        ],
        parallel_action=True
    )

    return manager
