"""
PyAgent 安全策略系统 - 策略引擎

参考OpenAkita的Policy设计，实现六层安全防护体系。
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ZoneType(Enum):
    """四区路径类型"""
    WORKSPACE = "workspace"
    CONTROLLED = "controlled"
    PROTECTED = "protected"
    FORBIDDEN = "forbidden"


class RiskLevel(Enum):
    """风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    """动作类型"""
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"
    SANDBOX = "sandbox"


@dataclass
class PolicyRule:
    """策略规则"""
    name: str
    description: str = ""
    pattern: str = ""
    action: ActionType = ActionType.ALLOW
    risk_level: RiskLevel = RiskLevel.SAFE
    message: str = ""
    enabled: bool = True


@dataclass
class PolicyResult:
    """策略检查结果"""
    allowed: bool
    action: ActionType
    risk_level: RiskLevel
    message: str = ""
    rule_name: str = ""
    requires_confirmation: bool = False


class PolicyEngine:
    """
    策略引擎

    实现六层安全防护：
    L1: 四区路径保护
    L2: 确认门
    L3: 命令模式拦截
    L4: 文件快照
    L5: 自保护
    L6: 沙箱
    """

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path
        self._rules: dict[str, list[PolicyRule]] = {}
        self._zones: dict[ZoneType, list[str]] = {
            ZoneType.WORKSPACE: [],
            ZoneType.CONTROLLED: [],
            ZoneType.PROTECTED: [],
            ZoneType.FORBIDDEN: []
        }
        self._command_patterns: dict[str, list[str]] = {}
        self._confirmation_callbacks: list[Callable] = []
        self._sandbox_enabled = False
        self._readonly_mode = False

        if config_path:
            self.load_config(config_path)
        else:
            self._load_default_rules()

    def load_config(self, config_path: str) -> None:
        """加载配置文件"""
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if zones := config.get("zones", {}):
                for zone_name, paths in zones.items():
                    zone_type = ZoneType(zone_name.lower())
                    self._zones[zone_type] = [Path(p) for p in paths]

            if rules := config.get("rules", {}):
                for category, rule_list in rules.items():
                    self._rules[category] = []
                    for rule_data in rule_list:
                        rule = PolicyRule(
                            name=rule_data.get("name", ""),
                            description=rule_data.get("description", ""),
                            pattern=rule_data.get("pattern", ""),
                            action=ActionType(rule_data.get("action", "allow")),
                            risk_level=RiskLevel(rule_data.get("risk_level", "safe")),
                            message=rule_data.get("message", ""),
                            enabled=rule_data.get("enabled", True)
                        )
                        self._rules[category].append(rule)

            if patterns := config.get("command_patterns", {}):
                self._command_patterns = patterns

            if sandbox := config.get("sandbox", {}):
                self._sandbox_enabled = sandbox.get("enabled", False)

        except Exception as e:
            print(f"加载策略配置失败: {e}")
            self._load_default_rules()

    def _load_default_rules(self) -> None:
        """加载默认规则"""
        self._rules = {
            "file_operations": [
                PolicyRule(
                    name="forbidden_paths",
                    description="禁止访问敏感路径",
                    pattern=r"(/etc/passwd|/etc/shadow|\.ssh/|\.env)",
                    action=ActionType.DENY,
                    risk_level=RiskLevel.CRITICAL,
                    message="禁止访问系统敏感文件"
                ),
                PolicyRule(
                    name="system_paths",
                    description="系统路径需要确认",
                    pattern=r"(/usr/|/bin/|/sbin/|/boot/|/proc/|/sys/)",
                    action=ActionType.CONFIRM,
                    risk_level=RiskLevel.HIGH,
                    message="访问系统路径需要确认"
                )
            ],
            "shell_commands": [
                PolicyRule(
                    name="dangerous_commands",
                    description="危险命令拦截",
                    pattern=r"(rm\s+-rf\s+/|mkfs|dd\s+if=|:(){ :|:& };:)",
                    action=ActionType.DENY,
                    risk_level=RiskLevel.CRITICAL,
                    message="禁止执行危险命令"
                ),
                PolicyRule(
                    name="privilege_commands",
                    description="特权命令需要确认",
                    pattern=r"(sudo|su|chmod|chown)",
                    action=ActionType.CONFIRM,
                    risk_level=RiskLevel.HIGH,
                    message="执行特权命令需要确认"
                ),
                PolicyRule(
                    name="network_commands",
                    description="网络命令需要确认",
                    pattern=r"(curl|wget|nc|netcat|ssh|scp|rsync)",
                    action=ActionType.CONFIRM,
                    risk_level=RiskLevel.MEDIUM,
                    message="执行网络命令需要确认"
                )
            ],
            "network_operations": [
                PolicyRule(
                    name="internal_network",
                    description="内网访问需要确认",
                    pattern=r"(localhost|127\.0\.0\.1|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)",
                    action=ActionType.CONFIRM,
                    risk_level=RiskLevel.MEDIUM,
                    message="访问内网地址需要确认"
                )
            ]
        }

        self._command_patterns = {
            "blocked": [
                "rm -rf /",
                "mkfs",
                "dd if=",
                ":(){ :|:& };:",
                "chmod -R 777 /"
            ],
            "restricted": [
                "sudo",
                "su -",
                "passwd",
                "useradd",
                "userdel"
            ]
        }

    def check_path(self, path: str) -> PolicyResult:
        """检查路径访问权限"""
        path_obj = Path(path).resolve()

        zone = self._get_path_zone(path_obj)

        if zone == ZoneType.FORBIDDEN:
            return PolicyResult(
                allowed=False,
                action=ActionType.DENY,
                risk_level=RiskLevel.CRITICAL,
                message="禁止访问此路径",
                rule_name="zone_forbidden"
            )

        if zone == ZoneType.PROTECTED:
            return PolicyResult(
                allowed=True,
                action=ActionType.CONFIRM,
                risk_level=RiskLevel.HIGH,
                message="访问受保护路径需要确认",
                rule_name="zone_protected",
                requires_confirmation=True
            )

        if zone == ZoneType.CONTROLLED:
            return PolicyResult(
                allowed=True,
                action=ActionType.CONFIRM,
                risk_level=RiskLevel.MEDIUM,
                message="访问受控路径需要确认",
                rule_name="zone_controlled",
                requires_confirmation=True
            )

        for rule in self._rules.get("file_operations", []):
            if not rule.enabled:
                continue
            if re.search(rule.pattern, str(path_obj)):
                return PolicyResult(
                    allowed=rule.action != ActionType.DENY,
                    action=rule.action,
                    risk_level=rule.risk_level,
                    message=rule.message,
                    rule_name=rule.name,
                    requires_confirmation=rule.action == ActionType.CONFIRM
                )

        return PolicyResult(
            allowed=True,
            action=ActionType.ALLOW,
            risk_level=RiskLevel.SAFE,
            message="路径访问允许"
        )

    def check_command(self, command: str) -> PolicyResult:
        """检查命令执行权限"""
        if self._readonly_mode:
            return PolicyResult(
                allowed=False,
                action=ActionType.DENY,
                risk_level=RiskLevel.CRITICAL,
                message="系统处于只读模式",
                rule_name="readonly_mode"
            )

        for blocked in self._command_patterns.get("blocked", []):
            if blocked in command:
                return PolicyResult(
                    allowed=False,
                    action=ActionType.DENY,
                    risk_level=RiskLevel.CRITICAL,
                    message=f"命令被阻止: 包含危险操作 '{blocked}'",
                    rule_name="blocked_command"
                )

        for rule in self._rules.get("shell_commands", []):
            if not rule.enabled:
                continue
            if re.search(rule.pattern, command):
                return PolicyResult(
                    allowed=rule.action != ActionType.DENY,
                    action=rule.action,
                    risk_level=rule.risk_level,
                    message=rule.message,
                    rule_name=rule.name,
                    requires_confirmation=rule.action == ActionType.CONFIRM
                )

        return PolicyResult(
            allowed=True,
            action=ActionType.ALLOW,
            risk_level=RiskLevel.SAFE,
            message="命令执行允许"
        )

    def check_url(self, url: str) -> PolicyResult:
        """检查URL访问权限"""
        for rule in self._rules.get("network_operations", []):
            if not rule.enabled:
                continue
            if re.search(rule.pattern, url):
                return PolicyResult(
                    allowed=rule.action != ActionType.DENY,
                    action=rule.action,
                    risk_level=rule.risk_level,
                    message=rule.message,
                    rule_name=rule.name,
                    requires_confirmation=rule.action == ActionType.CONFIRM
                )

        return PolicyResult(
            allowed=True,
            action=ActionType.ALLOW,
            risk_level=RiskLevel.SAFE,
            message="URL访问允许"
        )

    def _get_path_zone(self, path: Path) -> ZoneType:
        """获取路径所属区域"""
        for zone_type, zone_paths in self._zones.items():
            for zone_path in zone_paths:
                try:
                    path.relative_to(zone_path)
                    return zone_type
                except ValueError:
                    continue

        return ZoneType.WORKSPACE

    def add_rule(self, category: str, rule: PolicyRule) -> None:
        """添加规则"""
        if category not in self._rules:
            self._rules[category] = []
        self._rules[category].append(rule)

    def remove_rule(self, category: str, rule_name: str) -> bool:
        """移除规则"""
        if category not in self._rules:
            return False

        for i, rule in enumerate(self._rules[category]):
            if rule.name == rule_name:
                self._rules[category].pop(i)
                return True
        return False

    def enable_readonly_mode(self) -> None:
        """启用只读模式（死亡开关）"""
        self._readonly_mode = True

    def disable_readonly_mode(self) -> None:
        """禁用只读模式"""
        self._readonly_mode = False

    def is_readonly(self) -> bool:
        """检查是否只读模式"""
        return self._readonly_mode

    def enable_sandbox(self) -> None:
        """启用沙箱模式"""
        self._sandbox_enabled = True

    def disable_sandbox(self) -> None:
        """禁用沙箱模式"""
        self._sandbox_enabled = False

    def is_sandbox_enabled(self) -> bool:
        """检查沙箱是否启用"""
        return self._sandbox_enabled

    def register_confirmation_callback(self, callback: Callable) -> None:
        """注册确认回调"""
        self._confirmation_callbacks.append(callback)

    async def request_confirmation(
        self,
        action: str,
        details: dict[str, Any]
    ) -> bool:
        """请求用户确认"""
        for callback in self._confirmation_callbacks:
            try:
                result = await callback(action, details)
                if result is False:
                    return False
            except Exception:
                continue

        return True


policy_engine = PolicyEngine()
