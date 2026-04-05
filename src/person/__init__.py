"""
PyAgent 用户信息系统

参考MaiBot的Person设计，管理用户信息。
"""

from .person import Person, MemoryPoint
from .person_manager import PersonManager, person_manager

__all__ = [
    "Person",
    "MemoryPoint",
    "PersonManager",
    "person_manager",
]
