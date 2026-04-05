"""
PyAgent 聊天Agent核心 - 动作类型定义

定义动作规划器的类型系统。
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ActionType(Enum):
    """动作类型枚举"""
    REPLY = auto()
    NO_REPLY = auto()
    SEARCH = auto()
    EXECUTE = auto()
    READ = auto()
    MEMORY = auto()
    CUSTOM = auto()


class ActionActivationType(Enum):
    """动作激活类型"""
    ALWAYS = auto()
    NEVER = auto()
    RANDOM = auto()
    KEYWORD = auto()


@dataclass
class ActionInfo:
    """动作信息"""
    name: str
    description: str = ""
    parameters: dict[str, str] = field(default_factory=dict)
    requirements: list[str] = field(default_factory=list)
    parallel_action: bool = True
    activation_type: ActionActivationType = ActionActivationType.ALWAYS
    activation_keywords: list[str] = field(default_factory=list)
    random_activation_probability: float = 0.5


@dataclass
class ActionPlannerInfo:
    """动作规划信息"""
    action_type: str
    reasoning: str = ""
    action_data: dict[str, Any] = field(default_factory=dict)
    action_message: Any | None = None
    available_actions: dict[str, ActionInfo] = field(default_factory=dict)
    action_reasoning: str | None = None


@dataclass
class PlannerPromptInfo:
    """规划器提示词信息"""
    time_block: str = ""
    name_block: str = ""
    chat_content_block: str = ""
    action_options_text: str = ""
    actions_before_now_block: str = ""
    plan_style: str = ""
    moderation_prompt: str = ""
