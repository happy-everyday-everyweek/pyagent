"""
PyAgent 聊天Agent核心 - 拟人化系统

参考MaiBot的设计，实现深度拟人化：
- 情感表达系统
- 行为规划（懂得在合适的时间说话）
- 个性系统（性格特征、状态切换）
- 自然语言风格Prompt
"""

from .behavior_planner import (
    ActionType,
    ActionDecision,
    BehaviorPlanner,
    ConversationContext,
)
from .humanized_prompt import (
    ConversationGoal,
    EmotionType,
    HumanizedPromptBuilder,
    humanized_prompt_builder,
)

__all__ = [
    "ActionType",
    "ActionDecision",
    "BehaviorPlanner",
    "ConversationContext",
    "ConversationGoal",
    "EmotionType",
    "HumanizedPromptBuilder",
    "humanized_prompt_builder",
]
