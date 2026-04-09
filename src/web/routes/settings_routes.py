"""
PyAgent Web服务 - 设置管理API

提供设置读取、更新和同步功能。
"""

import json
import logging
import os
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingScope(str, Enum):
    """设置范围"""
    LOCAL = "local"
    SYNC = "sync"


class SettingCategory(str, Enum):
    """设置分类"""
    GENERAL = "general"
    AI_AGENT = "ai_agent"
    APPLICATIONS = "applications"
    DISTRIBUTED = "distributed"
    LABORATORY = "laboratory"


SETTING_DEFINITIONS = {
    "general": {
        "scope": SettingScope.LOCAL,
        "settings": {
            "language": {
                "type": "string",
                "default": "zh-CN",
                "options": ["zh-CN", "en-US", "ja-JP"],
                "label": "语言",
                "description": "界面显示语言"
            },
            "theme": {
                "type": "string",
                "default": "light",
                "options": ["light", "dark", "auto"],
                "label": "主题",
                "description": "界面主题模式"
            },
            "notifications": {
                "type": "boolean",
                "default": True,
                "label": "通知",
                "description": "是否启用系统通知"
            },
            "sound": {
                "type": "boolean",
                "default": True,
                "label": "声音",
                "description": "是否启用提示音"
            }
        }
    },
    "ai_agent": {
        "scope": SettingScope.SYNC,
        "settings": {
            "default_model": {
                "type": "string",
                "default": "gpt-4",
                "label": "默认模型",
                "description": "默认使用的AI模型"
            },
            "collaboration_mode": {
                "type": "boolean",
                "default": False,
                "label": "协作模式",
                "description": "是否启用多智能体协作"
            },
            "max_agents": {
                "type": "number",
                "default": 3,
                "min": 1,
                "max": 10,
                "label": "最大智能体数",
                "description": "协作时最大智能体数量"
            },
            "timeout": {
                "type": "number",
                "default": 300,
                "min": 30,
                "max": 3600,
                "label": "超时时间",
                "description": "任务执行超时时间（秒）"
            },
            "persona_enabled": {
                "type": "boolean",
                "default": True,
                "label": "拟人化",
                "description": "是否启用拟人化对话"
            },
            "state_probability": {
                "type": "number",
                "default": 0.15,
                "min": 0,
                "max": 1,
                "label": "状态切换概率",
                "description": "个性状态随机切换概率"
            }
        }
    },
    "applications": {
        "scope": SettingScope.SYNC,
        "settings": {
            "calendar_enabled": {
                "type": "boolean",
                "default": True,
                "label": "日历",
                "description": "是否启用日历功能"
            },
            "email_enabled": {
                "type": "boolean",
                "default": True,
                "label": "邮件",
                "description": "是否启用邮件功能"
            },
            "documents_enabled": {
                "type": "boolean",
                "default": True,
                "label": "文档",
                "description": "是否启用文档编辑"
            },
            "video_enabled": {
                "type": "boolean",
                "default": True,
                "label": "视频",
                "description": "是否启用视频编辑"
            }
        }
    },
    "distributed": {
        "scope": SettingScope.SYNC,
        "settings": {
            "domain_id": {
                "type": "string",
                "default": "",
                "label": "域ID",
                "description": "当前所属域"
            },
            "sync_enabled": {
                "type": "boolean",
                "default": True,
                "label": "同步",
                "description": "是否启用跨设备同步"
            },
            "sync_interval": {
                "type": "number",
                "default": 60,
                "min": 10,
                "max": 3600,
                "label": "同步间隔",
                "description": "自动同步间隔（秒）"
            },
            "conflict_strategy": {
                "type": "string",
                "default": "last_write_wins",
                "options": ["last_write_wins", "manual", "ask"],
                "label": "冲突策略",
                "description": "同步冲突解决策略"
            }
        }
    },
    "laboratory": {
        "scope": SettingScope.LOCAL,
        "settings": {
            "experimental_features": {
                "type": "object",
                "default": {},
                "label": "实验性功能",
                "description": "实验性功能开关"
            },
            "debug_mode": {
                "type": "boolean",
                "default": False,
                "label": "调试模式",
                "description": "是否启用调试模式"
            },
            "verbose_logging": {
                "type": "boolean",
                "default": False,
                "label": "详细日志",
                "description": "是否记录详细日志"
            }
        }
    }
}


class SettingsManager:
    """设置管理器"""

    def __init__(self, settings_dir: str = "data/settings"):
        self.settings_dir = settings_dir
        self._ensure_dir()
        self._settings: dict[str, Any] = {}
        self._load_settings()

    def _ensure_dir(self) -> None:
        """确保设置目录存在"""
        if not os.path.exists(self.settings_dir):
            os.makedirs(self.settings_dir, exist_ok=True)

    def _get_settings_file(self, scope: SettingScope) -> str:
        """获取设置文件路径"""
        return os.path.join(self.settings_dir, f"{scope.value}_settings.json")

    def _load_settings(self) -> None:
        """加载设置"""
        for scope in SettingScope:
            file_path = self._get_settings_file(scope)
            try:
                if os.path.exists(file_path):
                    with open(file_path, encoding="utf-8") as f:
                        self._settings[scope.value] = json.load(f)
                else:
                    self._settings[scope.value] = self._get_default_settings(scope)
            except Exception as e:
                logger.error(f"Failed to load {scope.value} settings: {e}")
                self._settings[scope.value] = self._get_default_settings(scope)

    def _get_default_settings(self, scope: SettingScope) -> dict[str, Any]:
        """获取默认设置"""
        defaults = {}
        for category, config in SETTING_DEFINITIONS.items():
            if config["scope"] == scope:
                defaults[category] = {
                    key: setting["default"]
                    for key, setting in config["settings"].items()
                }
        return defaults

    def _save_settings(self, scope: SettingScope) -> bool:
        """保存设置"""
        file_path = self._get_settings_file(scope)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._settings[scope.value], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save {scope.value} settings: {e}")
            return False

    def get_all_settings(self) -> dict[str, Any]:
        """获取所有设置"""
        return self._settings.copy()

    def get_category_settings(self, category: str) -> dict[str, Any]:
        """获取分类设置"""
        return self._settings.get(category, {})

    def get_setting(self, category: str, key: str) -> Any:
        """获取单个设置"""
        return self._settings.get(category, {}).get(key)

    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """设置单个设置"""
        if category not in self._settings:
            self._settings[category] = {}

        self._settings[category][key] = value

        config = SETTING_DEFINITIONS.get(category)
        if config:
            scope = config["scope"]
            return self._save_settings(scope)

        return False

    def update_category(self, category: str, settings: dict[str, Any]) -> bool:
        """更新分类设置"""
        if category not in SETTING_DEFINITIONS:
            return False

        self._settings[category] = settings
        config = SETTING_DEFINITIONS[category]
        return self._save_settings(config["scope"])

    def get_scope(self, category: str) -> SettingScope | None:
        """获取设置范围"""
        config = SETTING_DEFINITIONS.get(category)
        return config["scope"] if config else None

    def is_sync_setting(self, category: str) -> bool:
        """是否为同步设置"""
        scope = self.get_scope(category)
        return scope == SettingScope.SYNC


settings_manager = SettingsManager()


class SettingUpdateRequest(BaseModel):
    """设置更新请求"""
    category: str
    key: str
    value: Any


class CategoryUpdateRequest(BaseModel):
    """分类更新请求"""
    category: str
    settings: dict[str, Any]


@router.get("")
async def get_all_settings() -> dict[str, Any]:
    """获取所有设置"""
    return {
        "settings": settings_manager.get_all_settings(),
        "definitions": SETTING_DEFINITIONS
    }


@router.get("/{category}")
async def get_category_settings(category: str) -> dict[str, Any]:
    """获取分类设置"""
    if category not in SETTING_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Category {category} not found")

    return {
        "category": category,
        "settings": settings_manager.get_category_settings(category),
        "definition": SETTING_DEFINITIONS[category]
    }


@router.get("/{category}/{key}")
async def get_setting(category: str, key: str) -> dict[str, Any]:
    """获取单个设置"""
    if category not in SETTING_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Category {category} not found")

    if key not in SETTING_DEFINITIONS[category]["settings"]:
        raise HTTPException(status_code=404, detail=f"Setting {key} not found in {category}")

    value = settings_manager.get_setting(category, key)
    return {
        "category": category,
        "key": key,
        "value": value,
        "definition": SETTING_DEFINITIONS[category]["settings"][key]
    }


@router.put("")
async def update_setting(request: SettingUpdateRequest) -> dict[str, Any]:
    """更新单个设置"""
    if request.category not in SETTING_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Category {request.category} not found")

    if request.key not in SETTING_DEFINITIONS[request.category]["settings"]:
        raise HTTPException(status_code=404, detail=f"Setting {request.key} not found")

    success = settings_manager.set_setting(request.category, request.key, request.value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save setting")

    is_sync = settings_manager.is_sync_setting(request.category)

    return {
        "success": True,
        "category": request.category,
        "key": request.key,
        "value": request.value,
        "scope": "sync" if is_sync else "local",
        "message": "设置已保存" + ("，将同步到其他设备" if is_sync else "")
    }


@router.put("/category")
async def update_category(request: CategoryUpdateRequest) -> dict[str, Any]:
    """更新分类设置"""
    if request.category not in SETTING_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Category {request.category} not found")

    success = settings_manager.update_category(request.category, request.settings)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings")

    is_sync = settings_manager.is_sync_setting(request.category)

    return {
        "success": True,
        "category": request.category,
        "settings": request.settings,
        "scope": "sync" if is_sync else "local",
        "message": "设置已保存" + ("，将同步到其他设备" if is_sync else "")
    }


@router.post("/reset/{category}")
async def reset_category(category: str) -> dict[str, Any]:
    """重置分类设置为默认值"""
    if category not in SETTING_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Category {category} not found")

    defaults = {
        key: setting["default"]
        for key, setting in SETTING_DEFINITIONS[category]["settings"].items()
    }

    success = settings_manager.update_category(category, defaults)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset settings")

    return {
        "success": True,
        "category": category,
        "settings": defaults,
        "message": "设置已重置为默认值"
    }
