"""
PyAgent 用户信息系统

参考MaiBot的Person设计，管理用户信息。
"""

from .person import MemoryPoint, Person
from .person_manager import PersonManager, person_manager

__all__ = [
    "MemoryPoint",
    "Person",
    "PersonManager",
    "person_manager",
]
