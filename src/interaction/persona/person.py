"""
PyAgent 拟人化系统 - 用户记忆管理

管理用户相关的记忆点。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryPoint:
    """记忆点"""
    category: str
    content: str
    weight: float = 1.0
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    last_accessed: float = field(default_factory=lambda: datetime.now().timestamp())
    access_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "content": self.content,
            "weight": self.weight,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count
        }
    
    @classmethod
    def from_string(cls, point_str: str) -> Optional["MemoryPoint"]:
        """
        从字符串解析记忆点
        
        格式: category:content:weight
        
        Args:
            point_str: 字符串格式的记忆点
            
        Returns:
            MemoryPoint | None: 记忆点对象
        """
        parts = point_str.split(":", 2)
        if len(parts) >= 2:
            category = parts[0]
            content = parts[1]
            weight = float(parts[2]) if len(parts) > 2 else 1.0
            return cls(category=category, content=content, weight=weight)
        return None
    
    def to_string(self) -> str:
        """转换为字符串格式"""
        return f"{self.category}:{self.content}:{self.weight}"


class Person:
    """用户信息管理"""
    
    MEMORY_SIMILARITY_THRESHOLD = 0.8
    
    def __init__(
        self,
        user_id: str,
        name: str = "",
        nickname: str = "",
        platform: str = ""
    ):
        self.user_id = user_id
        self.name = name
        self.nickname = nickname
        self.platform = platform
        self.memory_points: list[MemoryPoint] = []
        self._created_at = datetime.now().timestamp()
        self._last_interaction = datetime.now().timestamp()
    
    def add_memory(
        self,
        category: str,
        content: str,
        weight: float = 1.0
    ) -> bool:
        """
        添加记忆点
        
        Args:
            category: 分类（如：喜好、工作、生活、关系等）
            content: 内容
            weight: 权重
            
        Returns:
            bool: 是否添加成功
        """
        if not content:
            return False
        
        if self._is_similar_memory(category, content):
            return False
        
        self.memory_points.append(MemoryPoint(
            category=category,
            content=content,
            weight=weight
        ))
        
        self._last_interaction = datetime.now().timestamp()
        logger.debug(f"Added memory for {self.user_id}: {category}:{content}")
        return True
    
    def add_memory_from_string(self, point_str: str) -> bool:
        """
        从字符串添加记忆点
        
        Args:
            point_str: 格式为 "category:content:weight" 的字符串
            
        Returns:
            bool: 是否添加成功
        """
        point = MemoryPoint.from_string(point_str)
        if point:
            return self.add_memory(point.category, point.content, point.weight)
        return False
    
    def _is_similar_memory(self, category: str, content: str) -> bool:
        """检查是否存在相似的记忆"""
        for point in self.memory_points:
            if point.category == category:
                similarity = SequenceMatcher(
                    None,
                    point.content.lower(),
                    content.lower()
                ).ratio()
                if similarity >= self.MEMORY_SIMILARITY_THRESHOLD:
                    return True
        return False
    
    def get_memories_by_category(self, category: str) -> list[MemoryPoint]:
        """
        按分类获取记忆
        
        Args:
            category: 分类名称
            
        Returns:
            list[MemoryPoint]: 该分类的记忆列表
        """
        return [
            point for point in self.memory_points
            if point.category == category
        ]
    
    def get_memories_by_keyword(self, keyword: str) -> list[MemoryPoint]:
        """
        按关键词搜索记忆
        
        Args:
            keyword: 关键词
            
        Returns:
            list[MemoryPoint]: 包含关键词的记忆列表
        """
        keyword_lower = keyword.lower()
        return [
            point for point in self.memory_points
            if keyword_lower in point.content.lower()
        ]
    
    def get_recent_memories(self, limit: int = 10) -> list[MemoryPoint]:
        """
        获取最近的记忆
        
        Args:
            limit: 最大数量
            
        Returns:
            list[MemoryPoint]: 最近的记忆列表
        """
        sorted_points = sorted(
            self.memory_points,
            key=lambda p: p.last_accessed,
            reverse=True
        )
        return sorted_points[:limit]
    
    def get_important_memories(self, limit: int = 10) -> list[MemoryPoint]:
        """
        获取重要的记忆（按权重和访问次数）
        
        Args:
            limit: 最大数量
            
        Returns:
            list[MemoryPoint]: 重要的记忆列表
        """
        sorted_points = sorted(
            self.memory_points,
            key=lambda p: p.weight * (1 + p.access_count * 0.1),
            reverse=True
        )
        return sorted_points[:limit]
    
    def access_memory(self, index: int) -> Optional[MemoryPoint]:
        """
        访问记忆（更新访问时间和次数）
        
        Args:
            index: 记忆索引
            
        Returns:
            MemoryPoint | None: 记忆点
        """
        if 0 <= index < len(self.memory_points):
            point = self.memory_points[index]
            point.last_accessed = datetime.now().timestamp()
            point.access_count += 1
            return point
        return None
    
    def forget_memory(self, index: int) -> bool:
        """
        遗忘记忆
        
        Args:
            index: 记忆索引
            
        Returns:
            bool: 是否遗忘成功
        """
        if 0 <= index < len(self.memory_points):
            del self.memory_points[index]
            return True
        return False
    
    def decay_memories(self, threshold: float = 0.1) -> int:
        """
        记忆衰减（降低权重）
        
        Args:
            threshold: 权重阈值，低于此值的记忆将被删除
            
        Returns:
            int: 删除的记忆数量
        """
        now = datetime.now().timestamp()
        day_seconds = 86400
        
        to_remove = []
        for i, point in enumerate(self.memory_points):
            days_since_access = (now - point.last_accessed) / day_seconds
            point.weight *= (0.99 ** days_since_access)
            
            if point.weight < threshold:
                to_remove.append(i)
        
        for i in reversed(to_remove):
            del self.memory_points[i]
        
        return len(to_remove)
    
    def get_memory_summary(self) -> str:
        """
        获取记忆摘要
        
        Returns:
            str: 记忆摘要文本
        """
        if not self.memory_points:
            return ""
        
        categories: dict[str, list[MemoryPoint]] = {}
        for point in self.memory_points:
            if point.category not in categories:
                categories[point.category] = []
            categories[point.category].append(point)
        
        lines = []
        for category, points in categories.items():
            contents = [p.content for p in points[:5]]
            lines.append(f"【{category}】{', '.join(contents)}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "nickname": self.nickname,
            "platform": self.platform,
            "memory_points": [p.to_dict() for p in self.memory_points],
            "created_at": self._created_at,
            "last_interaction": self._last_interaction
        }


class PersonManager:
    """用户管理器"""
    
    def __init__(self):
        self._persons: dict[str, Person] = {}
    
    def get_person(
        self,
        user_id: str,
        name: str = "",
        nickname: str = "",
        platform: str = ""
    ) -> Person:
        """
        获取或创建用户
        
        Args:
            user_id: 用户ID
            name: 用户名
            nickname: 昵称
            platform: 平台
            
        Returns:
            Person: 用户对象
        """
        if user_id not in self._persons:
            self._persons[user_id] = Person(
                user_id=user_id,
                name=name,
                nickname=nickname,
                platform=platform
            )
        return self._persons[user_id]
    
    def add_memory(
        self,
        user_id: str,
        category: str,
        content: str,
        weight: float = 1.0
    ) -> bool:
        """
        为用户添加记忆
        
        Args:
            user_id: 用户ID
            category: 分类
            content: 内容
            weight: 权重
            
        Returns:
            bool: 是否添加成功
        """
        person = self._persons.get(user_id)
        if person:
            return person.add_memory(category, content, weight)
        return False
    
    def get_memory_summary(self, user_id: str) -> str:
        """
        获取用户记忆摘要
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 记忆摘要
        """
        person = self._persons.get(user_id)
        if person:
            return person.get_memory_summary()
        return ""
    
    def get_all_persons(self) -> dict[str, Person]:
        """获取所有用户"""
        return self._persons.copy()


person_manager = PersonManager()
