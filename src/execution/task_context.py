"""
PyAgent 执行模块 - 任务上下文

提供任务执行上下文的管理功能。
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TaskContext:
    """
    任务上下文
    
    管理任务执行过程中的上下文数据，包括：
    - 任务ID关联
    - 数据存储
    - 元数据管理
    """
    task_id: str
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_context: Optional["TaskContext"] = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取上下文数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            数据值，如果不存在则返回默认值
        """
        if key in self.data:
            return self.data[key]
        if self.parent_context:
            return self.parent_context.get(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        """
        设置上下文数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self.data[key] = value

    def update(self, data: dict[str, Any]) -> None:
        """
        批量更新上下文数据
        
        Args:
            data: 要更新的数据字典
        """
        self.data.update(data)

    def delete(self, key: str) -> bool:
        """
        删除上下文数据
        
        Args:
            key: 数据键
            
        Returns:
            是否成功删除
        """
        if key in self.data:
            del self.data[key]
            return True
        return False

    def has(self, key: str) -> bool:
        """
        检查是否存在指定键
        
        Args:
            key: 数据键
            
        Returns:
            是否存在
        """
        if key in self.data:
            return True
        if self.parent_context:
            return self.parent_context.has(key)
        return False

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        获取元数据
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value

    def clear(self) -> None:
        """清空上下文数据"""
        self.data.clear()
        self.metadata.clear()

    def keys(self) -> list[str]:
        """获取所有数据键"""
        keys = list(self.data.keys())
        if self.parent_context:
            keys.extend(self.parent_context.keys())
        return list(set(keys))

    def values(self) -> list[Any]:
        """获取所有数据值"""
        return [self.get(k) for k in self.keys()]

    def items(self) -> list[tuple[str, Any]]:
        """获取所有键值对"""
        return [(k, self.get(k)) for k in self.keys()]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "task_id": self.task_id,
            "data": self.data.copy(),
            "metadata": self.metadata.copy()
        }
        if self.parent_context:
            result["parent_task_id"] = self.parent_context.task_id
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any], parent: Optional["TaskContext"] = None) -> "TaskContext":
        """从字典创建上下文"""
        return cls(
            task_id=data.get("task_id", ""),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            parent_context=parent
        )

    def create_child(self, task_id: str) -> "TaskContext":
        """
        创建子上下文
        
        Args:
            task_id: 子任务ID
            
        Returns:
            子上下文实例
        """
        return TaskContext(
            task_id=task_id,
            data={},
            metadata={},
            parent_context=self
        )

    def __contains__(self, key: str) -> bool:
        """支持 'in' 操作符"""
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        if key in self.data:
            return self.data[key]
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典式设置"""
        self.data[key] = value
