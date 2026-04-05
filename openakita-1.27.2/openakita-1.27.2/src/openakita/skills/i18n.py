"""
技能国际化支持

通过 agents/openai.yaml 的 i18n 字段为技能提供多语言名称和描述。
向后兼容旧的 .openakita-i18n.json sidecar 文件。
- 内置技能：预置翻译（agents/openai.yaml）
- 市场安装技能：安装后自动调用 LLM 翻译生成
- 用户创建技能：skill-creator 引导创建
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from ..core.brain import Brain

logger = logging.getLogger(__name__)

LEGACY_I18N_FILENAME = ".openakita-i18n.json"
OPENAI_YAML_PATH = "agents/openai.yaml"


def read_i18n(skill_dir: Path) -> dict[str, dict[str, str]]:
    """读取技能的 i18n 数据。

    优先从 agents/openai.yaml 的 ``i18n`` 字段读取，
    回退到旧的 .openakita-i18n.json 格式。

    Returns:
        {lang: {"name": ..., "description": ...}, ...} 或空 dict
    """
    result = _read_i18n_from_yaml(skill_dir)
    if result:
        return result
    return _read_i18n_from_json(skill_dir)


def _read_i18n_from_yaml(skill_dir: Path) -> dict[str, dict[str, str]]:
    """从 agents/openai.yaml 的 i18n 字段读取。"""
    yaml_file = skill_dir / OPENAI_YAML_PATH
    if not yaml_file.exists():
        return {}
    try:
        content = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if not isinstance(content, dict):
            return {}
        i18n = content.get("i18n")
        if not isinstance(i18n, dict):
            return {}
        result: dict[str, dict[str, str]] = {}
        for lang, fields in i18n.items():
            if isinstance(fields, dict):
                entry: dict[str, str] = {}
                if "name" in fields:
                    entry["name"] = str(fields["name"])
                if "description" in fields:
                    entry["description"] = str(fields["description"])
                if entry:
                    result[lang] = entry
        return result
    except Exception as e:
        logger.warning(f"Failed to read i18n from agents/openai.yaml for {skill_dir.name}: {e}")
    return {}


def _read_i18n_from_json(skill_dir: Path) -> dict[str, dict[str, str]]:
    """从旧的 .openakita-i18n.json 读取（向后兼容）。"""
    i18n_file = skill_dir / LEGACY_I18N_FILENAME
    if not i18n_file.exists():
        return {}
    try:
        data = json.loads(i18n_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception as e:
        logger.warning(f"Failed to read legacy i18n for {skill_dir.name}: {e}")
    return {}


def write_i18n(skill_dir: Path, data: dict[str, dict[str, str]]) -> None:
    """将 i18n 数据写入 agents/openai.yaml。

    如果 agents/openai.yaml 已存在，合并 i18n 字段；否则创建新文件。
    """
    yaml_file = skill_dir / OPENAI_YAML_PATH
    existing: dict = {}
    if yaml_file.exists():
        try:
            existing = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        except Exception:
            existing = {}

    existing["i18n"] = data

    yaml_file.parent.mkdir(parents=True, exist_ok=True)
    yaml_file.write_text(
        yaml.dump(existing, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def _extract_json(text: str) -> dict | None:
    """从 LLM 输出中提取 JSON（兼容 markdown code block 包裹）。"""
    # 尝试直接解析
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # 尝试从 ```json ... ``` 中提取
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    return None


async def auto_translate_skill(
    skill_dir: Path,
    name: str,
    description: str,
    brain: "Brain",
) -> bool:
    """安装后自动翻译技能名和描述，写入 agents/openai.yaml 的 i18n 字段。

    如果已有 i18n 数据（无论来源），则跳过。

    Args:
        skill_dir: 技能目录
        name: 技能英文名 (如 "code-reviewer")
        description: 技能英文描述
        brain: Brain 实例，用于调用 LLM

    Returns:
        True 表示成功写入翻译，False 表示跳过或失败
    """
    if read_i18n(skill_dir):
        return False

    prompt = (
        "将以下 AI 技能的名称和描述翻译为简体中文。\n"
        "名称应简短精炼（2-6个汉字），描述应通顺自然。\n"
        "仅返回纯 JSON，不要 markdown 包裹：\n"
        f'{{"name": "{name}", "description": "{description}"}}'
    )

    try:
        resp = await brain.think_lightweight(prompt, max_tokens=512)
        parsed = _extract_json(resp.content)
        if not parsed or "name" not in parsed or "description" not in parsed:
            logger.warning(f"LLM translation returned unexpected format for {name}")
            return False

        i18n_data = {
            "zh": {
                "name": str(parsed["name"]),
                "description": str(parsed["description"]),
            }
        }
        write_i18n(skill_dir, i18n_data)
        logger.info(f"Auto-translated skill {name} -> {parsed['name']}")
        return True

    except Exception as e:
        logger.warning(f"Auto-translate failed for skill {name}: {e}")
        return False
