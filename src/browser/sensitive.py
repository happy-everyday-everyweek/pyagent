"""
PyAgent 浏览器自动化模块 - 敏感数据处理器

提供敏感数据处理、占位符替换和日志脱敏功能。
参考 browser-use 项目的敏感数据处理设计实现。
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SensitiveDataType(str, Enum):
    """敏感数据类型"""
    PASSWORD = "password"
    API_KEY = "api_key"
    CREDIT_CARD = "credit_card"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    TOKEN = "token"
    SECRET = "secret"
    CUSTOM = "custom"


@dataclass
class SensitiveField:
    """敏感字段定义"""
    name: str
    data_type: SensitiveDataType
    placeholder: str = "[REDACTED]"
    pattern: str | None = None


class SensitiveDataConfig(BaseModel):
    """敏感数据配置"""

    enabled: bool = True
    placeholder: str = "[REDACTED]"
    log_redaction: bool = True
    fields: list[dict[str, Any]] = Field(default_factory=list)

    def get_default_fields(self) -> list[SensitiveField]:
        """获取默认敏感字段"""
        return [
            SensitiveField("password", SensitiveDataType.PASSWORD, "[PASSWORD]"),
            SensitiveField("passwd", SensitiveDataType.PASSWORD, "[PASSWORD]"),
            SensitiveField("pwd", SensitiveDataType.PASSWORD, "[PASSWORD]"),
            SensitiveField("api_key", SensitiveDataType.API_KEY, "[API_KEY]"),
            SensitiveField("apikey", SensitiveDataType.API_KEY, "[API_KEY]"),
            SensitiveField("token", SensitiveDataType.TOKEN, "[TOKEN]"),
            SensitiveField("access_token", SensitiveDataType.TOKEN, "[TOKEN]"),
            SensitiveField("secret", SensitiveDataType.SECRET, "[SECRET]"),
            SensitiveField("secret_key", SensitiveDataType.SECRET, "[SECRET]"),
            SensitiveField("credit_card", SensitiveDataType.CREDIT_CARD, "[CARD]"),
            SensitiveField("card_number", SensitiveDataType.CREDIT_CARD, "[CARD]"),
            SensitiveField("ssn", SensitiveDataType.SSN, "[SSN]"),
        ]


class SensitiveDataHandler:
    """敏感数据处理器"""

    def __init__(
        self,
        config: SensitiveDataConfig | None = None,
        secure_storage: Any | None = None,
    ):
        """
        初始化敏感数据处理器
        
        Args:
            config: 敏感数据配置
            secure_storage: 安全存储实例
        """
        self.config = config or SensitiveDataConfig()
        self._secure_storage = secure_storage
        self._sensitive_values: dict[str, str] = {}
        self._field_patterns: dict[str, re.Pattern] = {}

        self._init_patterns()

    def _init_patterns(self) -> None:
        """初始化正则表达式模式"""
        patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            "api_key": r"\b[a-zA-Z0-9]{32,}\b",
        }

        for name, pattern in patterns.items():
            try:
                self._field_patterns[name] = re.compile(pattern)
            except re.error:
                logger.warning(f"Invalid pattern for {name}")

    def register_sensitive_field(
        self,
        field_name: str,
        data_type: SensitiveDataType,
        placeholder: str | None = None,
    ) -> None:
        """
        注册敏感字段
        
        Args:
            field_name: 字段名称
            data_type: 数据类型
            placeholder: 占位符
        """
        field = SensitiveField(
            name=field_name.lower(),
            data_type=data_type,
            placeholder=placeholder or self.config.placeholder,
        )

        self.config.fields.append({
            "name": field.name,
            "data_type": field.data_type.value,
            "placeholder": field.placeholder,
        })

        logger.debug(f"Registered sensitive field: {field_name}")

    def store_sensitive_value(
        self,
        key: str,
        value: str,
    ) -> None:
        """
        存储敏感值
        
        Args:
            key: 键名
            value: 敏感值
        """
        self._sensitive_values[key] = value

        if self._secure_storage:
            try:
                self._secure_storage.set(key, value)
            except Exception as e:
                logger.error(f"Failed to store sensitive value: {e}")

    def get_sensitive_value(
        self,
        key: str,
    ) -> str | None:
        """
        获取敏感值
        
        Args:
            key: 键名
            
        Returns:
            敏感值或 None
        """
        if key in self._sensitive_values:
            return self._sensitive_values[key]

        if self._secure_storage:
            try:
                return self._secure_storage.get(key)
            except Exception as e:
                logger.error(f"Failed to get sensitive value: {e}")

        return None

    def redact_value(
        self,
        key: str,
        value: Any,
    ) -> Any:
        """
        脱敏值
        
        Args:
            key: 字段名
            value: 值
            
        Returns:
            脱敏后的值
        """
        if not self.config.enabled:
            return value

        if not isinstance(value, str):
            return value

        key_lower = key.lower()

        for field_config in self.config.fields:
            if field_config["name"] == key_lower:
                return field_config["placeholder"]

        for field_config in self.config.get_default_fields():
            if field_config.name == key_lower:
                return field_config.placeholder

        return value

    def redact_dict(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        脱敏字典
        
        Args:
            data: 原始字典
            
        Returns:
            脱敏后的字典
        """
        if not self.config.enabled:
            return data

        result = {}

        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self.redact_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.redact_dict(item) if isinstance(item, dict) else
                    self.redact_value(key, item)
                    for item in value
                ]
            else:
                result[key] = self.redact_value(key, value)

        return result

    def redact_string(
        self,
        text: str,
    ) -> str:
        """
        脱敏字符串中的敏感信息
        
        Args:
            text: 原始文本
            
        Returns:
            脱敏后的文本
        """
        if not self.config.enabled or not self.config.log_redaction:
            return text

        result = text

        for pattern_name, pattern in self._field_patterns.items():
            placeholder = f"[{pattern_name.upper()}]"
            result = pattern.sub(placeholder, result)

        for key, value in self._sensitive_values.items():
            if value and len(value) > 3:
                result = result.replace(value, f"[{key.upper()}]")

        return result

    def create_safe_log_message(
        self,
        message: str,
        **kwargs,
    ) -> str:
        """
        创建安全的日志消息
        
        Args:
            message: 原始消息
            **kwargs: 附加数据
            
        Returns:
            安全的日志消息
        """
        safe_message = self.redact_string(message)

        if kwargs:
            safe_kwargs = self.redact_dict(kwargs)
            return f"{safe_message} | {safe_kwargs}"

        return safe_message

    def inject_sensitive_value(
        self,
        action_params: dict[str, Any],
        sensitive_keys: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        注入敏感值到动作参数
        
        Args:
            action_params: 动作参数
            sensitive_keys: 敏感键映射 {参数名: 存储键}
            
        Returns:
            注入后的参数
        """
        if not sensitive_keys:
            return action_params

        result = action_params.copy()

        for param_name, storage_key in sensitive_keys.items():
            if param_name in result:
                placeholder = result[param_name]
                if isinstance(placeholder, str) and placeholder.startswith("[") and placeholder.endswith("]"):
                    actual_value = self.get_sensitive_value(storage_key)
                    if actual_value:
                        result[param_name] = actual_value

        return result

    def clear_sensitive_values(self) -> None:
        """清除所有敏感值"""
        self._sensitive_values.clear()
        logger.info("Sensitive values cleared")

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "enabled": self.config.enabled,
            "log_redaction": self.config.log_redaction,
            "registered_fields": len(self.config.fields),
            "stored_values": len(self._sensitive_values),
        }


class SensitiveLogFilter(logging.Filter):
    """敏感日志过滤器"""

    def __init__(self, handler: SensitiveDataHandler):
        super().__init__()
        self.handler = handler

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self.handler.redact_string(record.msg)

        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = self.handler.redact_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self.handler.redact_dict(arg) if isinstance(arg, dict) else arg
                    for arg in record.args
                )

        return True
