"""
PyAgent Skills技能系统 - 技能加载器

从目录加载技能，支持SKILL.md解析。
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

from .parser import ParsedSkill, SkillParser
from .registry import SkillRegistry, skill_registry

logger = logging.getLogger(__name__)

CURRENT_PLATFORM = sys.platform


class SkillLoader:
    """技能加载器"""

    def __init__(
        self,
        registry: SkillRegistry | None = None,
        parser: SkillParser | None = None
    ):
        self.registry = registry or skill_registry
        self.parser = parser or SkillParser()
        self._loaded_skills: dict[str, ParsedSkill] = {}

        self._skill_directories = [
            "skills",
            "__user_workspace__"
        ]

    def discover_skill_directories(
        self,
        base_path: Path | None = None
    ) -> list[Path]:
        """发现技能目录"""
        base_path = base_path or Path.cwd()
        directories = []

        for skill_dir in self._skill_directories:
            if skill_dir == "__user_workspace__":
                path = Path.home() / ".pyagent" / "skills"
            else:
                path = base_path / skill_dir

            if path.exists() and path.is_dir():
                directories.append(path)

        return directories

    def load_all(self, base_path: Path | None = None) -> int:
        """加载所有技能"""
        directories = self.discover_skill_directories(base_path)
        loaded = 0

        for skill_dir in directories:
            loaded += self.load_from_directory(skill_dir)

        return loaded

    def load_from_directory(self, directory: Path) -> int:
        """从目录加载技能"""
        if not directory.exists():
            logger.warning(f"Skill directory not found: {directory}")
            return 0

        loaded = 0

        for item in directory.iterdir():
            if not item.is_dir():
                continue

            skill_md = item / "SKILL.md"
            if skill_md.exists():
                try:
                    skill = self.load_skill(item)
                    if skill:
                        loaded += 1
                except Exception as e:
                    logger.error(f"Failed to load skill from {item}: {e}")

        logger.info(f"Loaded {loaded} skills from {directory}")
        return loaded

    def load_skill(self, skill_dir: Path) -> ParsedSkill | None:
        """加载单个技能"""
        try:
            skill = self.parser.parse_directory(skill_dir)

            if not self._is_os_compatible(skill.metadata.supported_os):
                logger.debug(
                    f"Skipping skill {skill.metadata.name}: "
                    f"not compatible with {CURRENT_PLATFORM}"
                )
                return None

            errors = self.parser.validate(skill)
            if errors:
                for error in errors:
                    logger.warning(f"Skill validation warning: {error}")

            sid = skill_dir.name

            self.registry.register(skill, skill_id=sid)
            self._loaded_skills[sid] = skill

            logger.info(f"Loaded skill: {sid} (name={skill.metadata.name})")
            return skill

        except Exception as e:
            logger.error(f"Failed to load skill from {skill_dir}: {e}")
            return None

    def _is_os_compatible(self, supported_os: list[str]) -> bool:
        """检查操作系统兼容性"""
        if not supported_os:
            return True
        return CURRENT_PLATFORM in supported_os

    def get_skill(self, key: str) -> ParsedSkill | None:
        """获取技能"""
        skill = self._loaded_skills.get(key)
        if skill:
            return skill

        for s in self._loaded_skills.values():
            if s.metadata.name == key:
                return s

        return None

    def get_skill_body(self, key: str) -> str | None:
        """获取技能指令"""
        skill = self.get_skill(key)
        if skill:
            return skill.body
        return None

    def run_script(
        self,
        name: str,
        script_name: str,
        args: list[str] | None = None,
        cwd: Path | None = None
    ) -> tuple[bool, str]:
        """运行技能脚本"""
        skill = self.get_skill(name)
        if not skill:
            return False, f"Skill not found: {name}"

        script_path = self._resolve_script_path(skill, script_name)
        if not script_path:
            return False, f"Script not found: {script_name}"

        args = args or []

        if script_path.suffix == ".py":
            cmd = [sys.executable, str(script_path)] + args
        elif script_path.suffix in (".sh", ".bash"):
            bash_path = shutil.which("bash")
            if not bash_path:
                return False, "bash not found"
            cmd = [bash_path, str(script_path)] + args
        elif script_path.suffix == ".js":
            cmd = ["node", str(script_path)] + args
        else:
            cmd = [str(script_path)] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or skill.skill_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"

            return result.returncode == 0, output

        except subprocess.TimeoutExpired:
            return False, "Script execution timed out"
        except Exception as e:
            return False, f"Script execution failed: {e}"

    def _resolve_script_path(
        self,
        skill: ParsedSkill,
        script_name: str
    ) -> Path | None:
        """解析脚本路径"""
        if skill.scripts_dir:
            candidate = skill.scripts_dir / script_name
            if candidate.exists():
                return candidate

        candidate = skill.skill_dir / script_name
        if candidate.exists():
            return candidate

        return None

    def unload_skill(self, name: str) -> bool:
        """卸载技能"""
        if name in self._loaded_skills:
            del self._loaded_skills[name]
            self.registry.unregister(name)
            logger.info(f"Unloaded skill: {name}")
            return True
        return False

    def reload_skill(self, name: str) -> ParsedSkill | None:
        """重新加载技能"""
        skill = self._loaded_skills.get(name)
        if not skill:
            return None

        skill_dir = skill.skill_dir
        self.unload_skill(name)
        return self.load_skill(skill_dir)

    @property
    def loaded_count(self) -> int:
        """已加载技能数量"""
        return len(self._loaded_skills)

    @property
    def loaded_skills(self) -> list[ParsedSkill]:
        """所有已加载的技能"""
        return list(self._loaded_skills.values())


skill_loader = SkillLoader()
