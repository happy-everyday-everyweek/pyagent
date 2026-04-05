"""
PyAgent 垂类智能体模块

提供垂类智能体支持，包括金融智能体等。
"""

from .base import BaseVerticalAgent, AgentCapability
from .financial import FinancialAgent
from .registry import AgentRegistry

__all__ = [
    "BaseVerticalAgent",
    "AgentCapability",
    "FinancialAgent",
    "AgentRegistry",
]
