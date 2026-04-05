"""
PyAgent 技能系统测试
"""

import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from skills.registry import SkillInfo, SkillRegistry, skill_registry


@dataclass
class MockMetadata:
    """模拟技能元数据"""
    name: str = "Test Skill"
    description: str = "Test skill description"
    version: str = "1.0.0"
    author: str = "Test Author"
    system: bool = False
    handler: str = ""
    tool_name: str = ""


@dataclass
class MockParsedSkill:
    """模拟解析后的技能"""
    skill_dir: Path = field(default_factory=lambda: Path("test_skill"))
    metadata: MockMetadata = field(default_factory=MockMetadata)
    handler: Any = None
    tools: list = field(default_factory=list)


class TestSkillInfo:
    """测试技能信息"""

    def test_skill_info_creation(self):
        info = SkillInfo(
            skill_id="test_skill",
            name="Test Skill",
            description="Test description",
            enabled=True,
            system=False
        )
        assert info.skill_id == "test_skill"
        assert info.name == "Test Skill"
        assert info.description == "Test description"
        assert info.enabled is True

    def test_skill_info_defaults(self):
        info = SkillInfo(skill_id="simple", name="Simple", description="Simple skill")
        assert info.enabled is True
        assert info.system is False
        assert info.handler == ""
        assert info.tool_name == ""


class TestSkillRegistry:
    """测试技能注册中心"""

    def setup_method(self):
        self.registry = SkillRegistry()
        self.registry.clear()

    def test_registry_creation(self):
        assert self.registry._skills == {}
        assert self.registry._disabled == set()

    def test_register_skill(self):
        skill = MockParsedSkill(
            skill_dir=Path("test_skill"),
            metadata=MockMetadata(name="Test Skill")
        )
        self.registry.register(skill, "test_skill")

        assert self.registry.count() == 1
        assert self.registry.get_skill("test_skill") == skill

    def test_unregister_skill(self):
        skill = MockParsedSkill()
        self.registry.register(skill, "test_skill")

        self.registry.unregister("test_skill")
        assert self.registry.count() == 0

    def test_get_nonexistent_skill(self):
        skill = self.registry.get_skill("nonexistent")
        assert skill is None

    def test_get_skill_info(self):
        skill = MockParsedSkill(
            metadata=MockMetadata(
                name="Test Skill",
                description="Test description",
                system=True
            )
        )
        self.registry.register(skill, "test_skill")

        info = self.registry.get_skill_info("test_skill")
        assert info is not None
        assert info.name == "Test Skill"
        assert info.system is True

    def test_get_skill_info_nonexistent(self):
        info = self.registry.get_skill_info("nonexistent")
        assert info is None

    def test_list_skills(self):
        skill1 = MockParsedSkill()
        skill2 = MockParsedSkill()

        self.registry.register(skill1, "skill1")
        self.registry.register(skill2, "skill2")

        skills = self.registry.list_skills()
        assert len(skills) == 2
        assert "skill1" in skills
        assert "skill2" in skills

    def test_list_enabled_skills(self):
        skill1 = MockParsedSkill()
        skill2 = MockParsedSkill()

        self.registry.register(skill1, "skill1")
        self.registry.register(skill2, "skill2")
        self.registry.set_disabled("skill2", True)

        enabled = self.registry.list_enabled_skills()
        assert len(enabled) == 1
        assert "skill1" in enabled

    def test_list_system_skills(self):
        skill1 = MockParsedSkill(metadata=MockMetadata(system=True))
        skill2 = MockParsedSkill(metadata=MockMetadata(system=False))

        self.registry.register(skill1, "skill1")
        self.registry.register(skill2, "skill2")

        system = self.registry.list_system_skills()
        assert len(system) == 1
        assert "skill1" in system

    def test_list_external_skills(self):
        skill1 = MockParsedSkill(metadata=MockMetadata(system=True))
        skill2 = MockParsedSkill(metadata=MockMetadata(system=False))

        self.registry.register(skill1, "skill1")
        self.registry.register(skill2, "skill2")

        external = self.registry.list_external_skills()
        assert len(external) == 1
        assert "skill2" in external

    def test_set_disabled(self):
        skill = MockParsedSkill()
        self.registry.register(skill, "test_skill")

        self.registry.set_disabled("test_skill", True)
        assert self.registry.is_enabled("test_skill") is False

        self.registry.set_disabled("test_skill", False)
        assert self.registry.is_enabled("test_skill") is True

    def test_is_enabled_nonexistent(self):
        result = self.registry.is_enabled("nonexistent")
        assert result is True

    def test_get_all_skills(self):
        skill = MockParsedSkill()
        self.registry.register(skill, "test_skill")

        all_skills = self.registry.get_all_skills()
        assert len(all_skills) == 1
        assert "test_skill" in all_skills

    def test_count(self):
        skill = MockParsedSkill()
        self.registry.register(skill, "test_skill")

        assert self.registry.count() == 1

    def test_clear(self):
        skill = MockParsedSkill()
        self.registry.register(skill, "test_skill")
        self.registry.set_disabled("test_skill", True)

        self.registry.clear()
        assert self.registry.count() == 0
        assert len(self.registry._disabled) == 0


class TestSkillRegistryGlobal:
    """测试全局技能注册中心实例"""

    def test_global_instance(self):
        assert skill_registry is not None
        assert isinstance(skill_registry, SkillRegistry)
