"""
PyAgent 人类任务管理系统 - 分类管理

提供任务分类的管理功能。
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Category:
    """
    任务分类
    
    属性：
    - id: 分类ID
    - name: 分类名称
    - color: 分类颜色（十六进制）
    - icon: 分类图标（SVG路径）
    - description: 分类描述
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    color: str = "#3498db"
    icon: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(self, **kwargs: Any) -> None:
        """更新分类属性"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Category":
        """从字典创建分类"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            color=data.get("color", "#3498db"),
            icon=data.get("icon", ""),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )


class CategoryManager:
    """
    分类管理器
    
    管理任务分类的创建、更新、删除和查询。
    """

    DEFAULT_CATEGORIES = [
        {
            "name": "工作",
            "color": "#3498db",
            "icon": "M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z",
            "description": "工作相关任务"
        },
        {
            "name": "个人",
            "color": "#2ecc71",
            "icon": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
            "description": "个人生活任务"
        },
        {
            "name": "学习",
            "color": "#9b59b6",
            "icon": "M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z",
            "description": "学习和提升任务"
        },
        {
            "name": "健康",
            "color": "#e74c3c",
            "icon": "M19 3H5c-1.1 0-1.99.9-1.99 2L3 19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 11h-4v4h-4v-4H6v-4h4V6h4v4h4v4z",
            "description": "健康和运动任务"
        },
        {
            "name": "其他",
            "color": "#95a5a6",
            "icon": "M6 10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z",
            "description": "其他类型任务"
        }
    ]

    def __init__(self, data_dir: str = "data/human_tasks"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.categories: dict[str, Category] = {}
        self._load_data()

        if not self.categories:
            self._init_default_categories()

    def _get_storage_file(self) -> Path:
        """获取存储文件路径"""
        return self.data_dir / "categories.json"

    def _load_data(self) -> None:
        """加载数据"""
        file_path = self._get_storage_file()
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("categories", []):
                        category = Category.from_dict(item)
                        self.categories[category.id] = category
            except Exception:
                pass

    def _save_data(self) -> None:
        """保存数据"""
        file_path = self._get_storage_file()
        try:
            data = {
                "categories": [c.to_dict() for c in self.categories.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _init_default_categories(self) -> None:
        """初始化默认分类"""
        for cat_data in self.DEFAULT_CATEGORIES:
            category = Category(
                id=str(uuid.uuid4()),
                name=cat_data["name"],
                color=cat_data["color"],
                icon=cat_data["icon"],
                description=cat_data["description"]
            )
            self.categories[category.id] = category

        self._save_data()

    def create_category(
        self,
        name: str,
        color: str = "#3498db",
        icon: str = "",
        description: str = ""
    ) -> Category:
        """
        创建新分类
        
        Args:
            name: 分类名称
            color: 分类颜色（十六进制）
            icon: 分类图标（SVG路径）
            description: 分类描述
            
        Returns:
            创建的分类对象
        """
        category = Category(
            name=name,
            color=color,
            icon=icon,
            description=description
        )

        self.categories[category.id] = category
        self._save_data()

        return category

    def update_category(
        self,
        category_id: str,
        name: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        description: str | None = None
    ) -> Category | None:
        """
        更新分类
        
        Args:
            category_id: 分类ID
            name: 新名称
            color: 新颜色
            icon: 新图标
            description: 新描述
            
        Returns:
            更新后的分类对象，如果分类不存在则返回None
        """
        category = self.categories.get(category_id)
        if not category:
            return None

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if color is not None:
            update_data["color"] = color
        if icon is not None:
            update_data["icon"] = icon
        if description is not None:
            update_data["description"] = description

        category.update(**update_data)
        self._save_data()

        return category

    def delete_category(self, category_id: str) -> bool:
        """
        删除分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            是否删除成功
        """
        if category_id in self.categories:
            del self.categories[category_id]
            self._save_data()
            return True
        return False

    def get_category(self, category_id: str) -> Category | None:
        """
        获取分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            分类对象，如果不存在则返回None
        """
        return self.categories.get(category_id)

    def get_category_by_name(self, name: str) -> Category | None:
        """
        通过名称获取分类
        
        Args:
            name: 分类名称
            
        Returns:
            分类对象，如果不存在则返回None
        """
        for category in self.categories.values():
            if category.name == name:
                return category
        return None

    def list_categories(self) -> list[Category]:
        """
        列出所有分类
        
        Returns:
            分类列表
        """
        return list(self.categories.values())

    def get_statistics(self) -> dict[str, Any]:
        """
        获取分类统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_categories": len(self.categories),
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "color": cat.color,
                }
                for cat in self.categories.values()
            ]
        }


category_manager = CategoryManager()
