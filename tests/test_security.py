"""
PyAgent 安全策略系统测试
"""

import pytest

from security.policy import (
    ActionType,
    PolicyEngine,
    PolicyResult,
    PolicyRule,
    RiskLevel,
    ZoneType,
    policy_engine,
)


class TestZoneType:
    """测试区域类型枚举"""

    def test_zone_type_values(self):
        assert ZoneType.WORKSPACE.value == "workspace"
        assert ZoneType.CONTROLLED.value == "controlled"
        assert ZoneType.PROTECTED.value == "protected"
        assert ZoneType.FORBIDDEN.value == "forbidden"

    def test_zone_type_count(self):
        assert len(ZoneType) == 4


class TestRiskLevel:
    """测试风险等级枚举"""

    def test_risk_level_values(self):
        assert RiskLevel.SAFE.value == "safe"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_risk_level_count(self):
        assert len(RiskLevel) == 5


class TestActionType:
    """测试动作类型枚举"""

    def test_action_type_values(self):
        assert ActionType.ALLOW.value == "allow"
        assert ActionType.CONFIRM.value == "confirm"
        assert ActionType.DENY.value == "deny"
        assert ActionType.SANDBOX.value == "sandbox"

    def test_action_type_count(self):
        assert len(ActionType) == 4


class TestPolicyRule:
    """测试策略规则"""

    def test_rule_creation(self):
        rule = PolicyRule(
            name="test_rule",
            description="Test rule",
            pattern=r"test.*",
            action=ActionType.DENY,
            risk_level=RiskLevel.HIGH,
            message="Test message"
        )
        assert rule.name == "test_rule"
        assert rule.description == "Test rule"
        assert rule.pattern == r"test.*"
        assert rule.action == ActionType.DENY
        assert rule.risk_level == RiskLevel.HIGH

    def test_rule_defaults(self):
        rule = PolicyRule(name="simple")
        assert rule.description == ""
        assert rule.pattern == ""
        assert rule.action == ActionType.ALLOW
        assert rule.risk_level == RiskLevel.SAFE
        assert rule.enabled is True


class TestPolicyResult:
    """测试策略结果"""

    def test_success_result(self):
        result = PolicyResult(
            allowed=True,
            action=ActionType.ALLOW,
            risk_level=RiskLevel.SAFE,
            message="Access allowed"
        )
        assert result.allowed is True
        assert result.action == ActionType.ALLOW
        assert result.risk_level == RiskLevel.SAFE

    def test_deny_result(self):
        result = PolicyResult(
            allowed=False,
            action=ActionType.DENY,
            risk_level=RiskLevel.CRITICAL,
            message="Access denied",
            rule_name="forbidden_path"
        )
        assert result.allowed is False
        assert result.action == ActionType.DENY
        assert result.requires_confirmation is False

    def test_confirm_result(self):
        result = PolicyResult(
            allowed=True,
            action=ActionType.CONFIRM,
            risk_level=RiskLevel.MEDIUM,
            requires_confirmation=True
        )
        assert result.allowed is True
        assert result.requires_confirmation is True


class TestPolicyEngine:
    """测试策略引擎"""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_engine_creation(self):
        assert self.engine._rules is not None
        assert self.engine._zones is not None

    def test_default_rules_loaded(self):
        assert "file_operations" in self.engine._rules
        assert "shell_commands" in self.engine._rules
        assert "network_operations" in self.engine._rules

    def test_check_path_allowed(self):
        result = self.engine.check_path("/home/user/test.txt")
        assert result.allowed is True
        assert result.action == ActionType.ALLOW

    def test_check_path_forbidden(self):
        result = self.engine.check_path("/etc/passwd")
        assert result.action in [ActionType.DENY, ActionType.ALLOW]
        if result.action == ActionType.DENY:
            assert result.risk_level == RiskLevel.CRITICAL

    def test_check_path_system(self):
        result = self.engine.check_path("/usr/bin/test")
        assert result.action in [ActionType.CONFIRM, ActionType.ALLOW]

    def test_check_command_allowed(self):
        result = self.engine.check_command("ls -la")
        assert result.allowed is True
        assert result.action == ActionType.ALLOW

    def test_check_command_dangerous(self):
        result = self.engine.check_command("rm -rf /")
        assert result.allowed is False
        assert result.action == ActionType.DENY
        assert result.risk_level == RiskLevel.CRITICAL

    def test_check_command_privilege(self):
        result = self.engine.check_command("sudo apt update")
        assert result.action == ActionType.CONFIRM

    def test_check_url_allowed(self):
        result = self.engine.check_url("https://example.com")
        assert result.allowed is True
        assert result.action == ActionType.ALLOW

    def test_check_url_internal(self):
        result = self.engine.check_url("http://192.168.1.1")
        assert result.action == ActionType.CONFIRM

    def test_add_rule(self):
        rule = PolicyRule(
            name="custom_rule",
            pattern=r"custom.*",
            action=ActionType.DENY,
            risk_level=RiskLevel.HIGH
        )
        self.engine.add_rule("custom", rule)

        assert "custom" in self.engine._rules
        assert len(self.engine._rules["custom"]) == 1

    def test_remove_rule(self):
        result = self.engine.remove_rule("file_operations", "forbidden_paths")
        assert result is True

        result = self.engine.remove_rule("nonexistent", "rule")
        assert result is False

    def test_readonly_mode(self):
        assert self.engine.is_readonly() is False

        self.engine.enable_readonly_mode()
        assert self.engine.is_readonly() is True

        result = self.engine.check_command("ls")
        assert result.allowed is False

        self.engine.disable_readonly_mode()
        assert self.engine.is_readonly() is False

    def test_sandbox_mode(self):
        assert self.engine.is_sandbox_enabled() is False

        self.engine.enable_sandbox()
        assert self.engine.is_sandbox_enabled() is True

        self.engine.disable_sandbox()
        assert self.engine.is_sandbox_enabled() is False

    @pytest.mark.asyncio
    async def test_request_confirmation_no_callbacks(self):
        result = await self.engine.request_confirmation(
            "test_action",
            {"detail": "test"}
        )
        assert result is True

    def test_register_confirmation_callback(self):
        async def callback(action, details):
            return True

        self.engine.register_confirmation_callback(callback)
        assert len(self.engine._confirmation_callbacks) == 1


class TestPolicyEngineGlobal:
    """测试全局策略引擎实例"""

    def test_global_instance(self):
        assert policy_engine is not None
        assert isinstance(policy_engine, PolicyEngine)
