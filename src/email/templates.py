"""
PyAgent 邮件模块 - 邮件模板
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import re


@dataclass
class EmailTemplate:
    name: str
    subject: str
    body_text: str
    body_html: str = ""
    variables: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "variables": self.variables,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmailTemplate":
        return cls(
            name=data.get("name", ""),
            subject=data.get("subject", ""),
            body_text=data.get("body_text", ""),
            body_html=data.get("body_html", ""),
            variables=data.get("variables", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def render(self, context: dict[str, Any]) -> tuple[str, str, str]:
        subject = self._render_string(self.subject, context)
        body_text = self._render_string(self.body_text, context)
        body_html = self._render_string(self.body_html, context)
        return subject, body_text, body_html

    def _render_string(self, template: str, context: dict[str, Any]) -> str:
        result = template
        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))
        return result

    def extract_variables(self) -> list[str]:
        pattern = r'\{\{(\w+)\}\}'
        subject_vars = re.findall(pattern, self.subject)
        body_vars = re.findall(pattern, self.body_text)
        html_vars = re.findall(pattern, self.body_html)
        return list(set(subject_vars + body_vars + html_vars))


class TemplateManager:
    """邮件模板管理器"""

    def __init__(self, template_dir: str = "data/email_templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self._templates: dict[str, EmailTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        for template_file in self.template_dir.glob("*.json"):
            try:
                with open(template_file, encoding="utf-8") as f:
                    data = json.load(f)
                    template = EmailTemplate.from_dict(data)
                    self._templates[template.name] = template
            except Exception:
                pass

    def get_template(self, name: str) -> EmailTemplate | None:
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        return list(self._templates.keys())

    def save_template(self, template: EmailTemplate) -> bool:
        try:
            now = datetime.now().isoformat()
            if not template.created_at:
                template.created_at = now
            template.updated_at = now

            template.variables = template.extract_variables()

            self._templates[template.name] = template

            template_file = self.template_dir / f"{template.name}.json"
            with open(template_file, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    def delete_template(self, name: str) -> bool:
        if name not in self._templates:
            return False

        try:
            del self._templates[name]
            template_file = self.template_dir / f"{name}.json"
            if template_file.exists():
                template_file.unlink()
            return True
        except Exception:
            return False

    def render_template(self, name: str, context: dict[str, Any]) -> tuple[str, str, str] | None:
        template = self.get_template(name)
        if not template:
            return None
        return template.render(context)
