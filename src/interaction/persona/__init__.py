"""
PyAgent 交互模块 - 个性系统
"""

from .goal_analyzer import ConversationGoal, GoalAnalyzer, goal_analyzer
from .person import MemoryPoint, Person, PersonManager, person_manager
from .persona_system import (
    ActionType,
    ConversationGoal as PersonaGoal,
    EmotionState,
    EmotionType,
    PersonalityState,
    PersonaSystem,
    persona_system,
)

__all__ = [
    "ActionType",
    "ConversationGoal",
    "EmotionState",
    "EmotionType",
    "GoalAnalyzer",
    "MemoryPoint",
    "Person",
    "PersonManager",
    "PersonalityState",
    "PersonaSystem",
    "goal_analyzer",
    "person_manager",
    "persona_system",
]
