"""Browser skills system for reusable automation patterns."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class SkillParameter:
    name: str
    description: str
    param_type: str = "string"
    required: bool = True
    default: Any = None
    options: list[str] = field(default_factory=list)


@dataclass
class SkillStep:
    action: str
    selector: str | None = None
    value: str | None = None
    description: str = ""
    wait_after: float = 0.5
    condition: str | None = None


@dataclass
class Skill:
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    parameters: list[SkillParameter] = field(default_factory=list)
    steps: list[SkillStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "parameters": [
                {
                    "name": p.name,
                    "description": p.description,
                    "type": p.param_type,
                    "required": p.required,
                    "default": p.default,
                    "options": p.options,
                }
                for p in self.parameters
            ],
            "steps": [
                {
                    "action": s.action,
                    "selector": s.selector,
                    "value": s.value,
                    "description": s.description,
                    "wait_after": s.wait_after,
                    "condition": s.condition,
                }
                for s in self.steps
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Skill":
        params = [
            SkillParameter(
                name=p["name"],
                description=p.get("description", ""),
                param_type=p.get("type", "string"),
                required=p.get("required", True),
                default=p.get("default"),
                options=p.get("options", []),
            )
            for p in data.get("parameters", [])
        ]

        steps = [
            SkillStep(
                action=s["action"],
                selector=s.get("selector"),
                value=s.get("value"),
                description=s.get("description", ""),
                wait_after=s.get("wait_after", 0.5),
                condition=s.get("condition"),
            )
            for s in data.get("steps", [])
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            parameters=params,
            steps=steps,
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )


class SkillManager:
    """Manages browser automation skills."""

    def __init__(self, skills_dir: str = "skills"):
        self._skills_dir = Path(skills_dir)
        self._skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills: dict[str, Skill] = {}
        self._custom_handlers: dict[str, Callable] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        for skill_file in self._skills_dir.glob("**/*.json"):
            try:
                with open(skill_file, encoding="utf-8") as f:
                    data = json.load(f)
                skill = Skill.from_dict(data)
                self._skills[skill.id] = skill
            except Exception as e:
                logger.warning("Failed to load skill %s: %s", skill_file, e)

    def register_skill(self, skill: Skill) -> None:
        self._skills[skill.id] = skill
        self._save_skill(skill)
        logger.info("Registered skill: %s", skill.name)

    def create_skill(
        self,
        name: str,
        description: str,
        steps: list[dict[str, Any]],
        parameters: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        author: str = "",
    ) -> Skill:
        import uuid

        skill = Skill(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            author=author,
            tags=tags or [],
            parameters=[SkillParameter(**p) for p in (parameters or [])],
            steps=[SkillStep(**s) for s in steps],
        )
        self.register_skill(skill)
        return skill

    def delete_skill(self, skill_id: str) -> bool:
        if skill_id not in self._skills:
            return False

        skill = self._skills[skill_id]
        skill_file = self._skills_dir / f"{skill_id}.json"
        if skill_file.exists():
            skill_file.unlink()

        del self._skills[skill_id]
        return True

    def get_skill(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def list_skills(self, tags: list[str] | None = None) -> list[Skill]:
        skills = list(self._skills.values())
        if tags:
            skills = [s for s in skills if any(tag in s.tags for tag in tags)]
        return skills

    def search_skills(self, query: str) -> list[Skill]:
        query_lower = query.lower()
        results = []

        for skill in self._skills.values():
            if query_lower in skill.name.lower() or query_lower in skill.description.lower():
                results.append(skill)
            elif any(query_lower in tag.lower() for tag in skill.tags):
                results.append(skill)

        return results

    def register_custom_handler(self, action: str, handler: Callable) -> None:
        self._custom_handlers[action] = handler

    async def execute_skill(
        self,
        skill_id: str,
        browser_controller: Any,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import asyncio

        skill = self._skills.get(skill_id)
        if not skill:
            return {"success": False, "error": f"Skill not found: {skill_id}"}

        params = params or {}
        validation = self._validate_params(skill, params)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}

        results = []
        for i, step in enumerate(skill.steps):
            try:
                result = await self._execute_step(step, browser_controller, params)
                results.append({"step": i, "success": True, "result": result})

                if step.wait_after > 0:
                    await asyncio.sleep(step.wait_after)

            except Exception as e:
                results.append({"step": i, "success": False, "error": str(e)})
                return {"success": False, "results": results, "failed_step": i}

        return {"success": True, "results": results}

    def _validate_params(self, skill: Skill, params: dict[str, Any]) -> dict[str, Any]:
        for param in skill.parameters:
            if param.required and param.name not in params:
                if param.default is not None:
                    params[param.name] = param.default
                else:
                    return {"valid": False, "error": f"Missing required parameter: {param.name}"}

        return {"valid": True}

    async def _execute_step(
        self,
        step: SkillStep,
        browser: Any,
        params: dict[str, Any],
    ) -> Any:
        selector = self._substitute_params(step.selector, params) if step.selector else None
        value = self._substitute_params(step.value, params) if step.value else None

        if step.action == "navigate":
            return await browser.navigate(value)
        elif step.action == "click":
            return await browser.click(selector)
        elif step.action == "input":
            return await browser.input_text(selector, value)
        elif step.action == "select":
            return await browser.select_option(selector, value)
        elif step.action == "wait":
            import asyncio

            await asyncio.sleep(float(value or 1))
            return {"waited": value}
        elif step.action == "screenshot":
            return await browser.screenshot()
        elif step.action in self._custom_handlers:
            return await self._custom_handlers[step.action](browser, selector, value, params)
        else:
            raise ValueError(f"Unknown action: {step.action}")

    def _substitute_params(self, template: str | None, params: dict[str, Any]) -> str | None:
        if not template:
            return None

        result = template
        for key, value in params.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def _save_skill(self, skill: Skill) -> None:
        skill_file = self._skills_dir / f"{skill.id}.json"
        with open(skill_file, "w", encoding="utf-8") as f:
            json.dump(skill.to_dict(), f, ensure_ascii=False, indent=2)


_manager: SkillManager | None = None


def get_skill_manager() -> SkillManager:
    global _manager
    if _manager is None:
        _manager = SkillManager()
    return _manager
