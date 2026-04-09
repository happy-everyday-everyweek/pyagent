"""
PyAgent 垂类智能体模块

提供垂类智能体支持，包括金融智能体、编码智能体等。
"""

from .base import AgentCapability, BaseVerticalAgent
from .coding import CodingAgent, ProjectContext, SystemPromptBuilder
from .financial import FinancialAgent
from .registry import AgentRegistry

__all__ = [
    "AgentCapability",
    "AgentRegistry",
    "BaseVerticalAgent",
    "CodingAgent",
    "FinancialAgent",
    "ProjectContext",
    "SystemPromptBuilder",
]
