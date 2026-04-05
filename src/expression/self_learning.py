"""
PyAgent 自我学习系统

参考MaiBot的设计，实现深度优化的自我学习功能：
- 表达学习：学习用户的表达方式和语言风格
- 黑话学习：识别和学习黑话/俚语/网络用语
- 记忆整理：定期整理和归纳记忆
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Expression:
    """表达方式"""
    id: str
    situation: str
    style: str
    content_list: list[str] = field(default_factory=list)
    count: int = 1
    checked: bool = False
    rejected: bool = False
    last_active_time: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "situation": self.situation,
            "style": self.style,
            "content_list": self.content_list,
            "count": self.count,
            "checked": self.checked,
            "rejected": self.rejected,
            "last_active_time": self.last_active_time,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Expression":
        return cls(
            id=data["id"],
            situation=data["situation"],
            style=data["style"],
            content_list=data.get("content_list", []),
            count=data.get("count", 1),
            checked=data.get("checked", False),
            rejected=data.get("rejected", False),
            last_active_time=data.get("last_active_time", time.time()),
            created_at=data.get("created_at", time.time()),
        )


@dataclass
class JargonEntry:
    """黑话条目"""
    id: str
    content: str
    meaning: str = ""
    raw_content: list[str] = field(default_factory=list)
    count: int = 1
    is_jargon: bool = True
    is_global: bool = False
    is_complete: bool = False
    last_inference_count: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "meaning": self.meaning,
            "raw_content": self.raw_content,
            "count": self.count,
            "is_jargon": self.is_jargon,
            "is_global": self.is_global,
            "is_complete": self.is_complete,
            "last_inference_count": self.last_inference_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JargonEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            meaning=data.get("meaning", ""),
            raw_content=data.get("raw_content", []),
            count=data.get("count", 1),
            is_jargon=data.get("is_jargon", True),
            is_global=data.get("is_global", False),
            is_complete=data.get("is_complete", False),
            last_inference_count=data.get("last_inference_count", 0),
            created_at=data.get("created_at", time.time()),
        )


class SelfLearningSystem:
    """自我学习系统"""

    def __init__(self, data_dir: str = "data/learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.expressions: dict[str, Expression] = {}
        self.jargons: dict[str, JargonEntry] = {}

        self._load_data()

        self._learning_lock = asyncio.Lock()

        self._common_words = {
            "的", "是", "在", "有", "和", "了", "不", "我",
            "你", "他", "她", "它", "这", "那", "什么", "怎么",
            "就", "都", "也", "要", "会", "能", "说", "对",
        }

    def _get_expressions_file(self) -> Path:
        return self.data_dir / "expressions.json"

    def _get_jargons_file(self) -> Path:
        return self.data_dir / "jargons.json"

    def _load_data(self) -> None:
        expressions_file = self._get_expressions_file()
        if expressions_file.exists():
            try:
                with open(expressions_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("expressions", []):
                        expr = Expression.from_dict(item)
                        self.expressions[expr.id] = expr
            except Exception:
                pass

        jargons_file = self._get_jargons_file()
        if jargons_file.exists():
            try:
                with open(jargons_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("jargons", []):
                        jargon = JargonEntry.from_dict(item)
                        self.jargons[jargon.id] = jargon
            except Exception:
                pass

    def _save_expressions(self) -> None:
        file_path = self._get_expressions_file()
        try:
            data = {
                "expressions": [e.to_dict() for e in self.expressions.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_jargons(self) -> None:
        file_path = self._get_jargons_file()
        try:
            data = {
                "jargons": [j.to_dict() for j in self.jargons.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_id(self, prefix: str = "expr") -> str:
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    async def learn_from_messages(
        self,
        messages: list[dict[str, Any]],
        llm_client: Any | None = None,
    ) -> dict[str, Any]:
        if not messages:
            return {"expressions": 0, "jargons": 0}

        async with self._learning_lock:
            result = {"expressions": 0, "jargons": 0}

            for msg in messages:
                content = msg.get("content", "")
                if not content or msg.get("is_bot", False):
                    continue

                expressions = self._extract_expressions(content, msg)
                for expr_data in expressions:
                    expr_id = self._find_or_create_expression(expr_data)
                    if expr_id:
                        result["expressions"] += 1

                jargons = self._extract_jargons(content)
                for jargon_content in jargons:
                    jargon_id = self._find_or_create_jargon(jargon_content, content)
                    if jargon_id:
                        result["jargons"] += 1

            if result["expressions"] > 0:
                self._save_expressions()
            if result["jargons"] > 0:
                self._save_jargons()

            return result

    def _extract_expressions(
        self,
        content: str,
        context: dict[str, Any],
    ) -> list[dict[str, str]]:
        expressions = []

        sentences = re.split(r'[。！？\n]+', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if not (5 <= len(sentence) <= 50):
                continue

            if self._is_valid_expression(sentence):
                situation = self._infer_situation(sentence, context)
                style = self._extract_style(sentence)

                if situation and style:
                    expressions.append({
                        "situation": situation,
                        "style": style,
                        "content": sentence,
                    })

        return expressions

    def _is_valid_expression(self, text: str) -> bool:
        if not text:
            return False

        if re.match(r'^[\d\s\W]+$', text):
            return False

        if len(text) < 3:
            return False

        return True

    def _infer_situation(self, text: str, context: dict[str, Any]) -> str:
        text_lower = text.lower()

        if any(w in text_lower for w in ["?", "？", "吗", "什么"]):
            return "询问信息时"
        elif any(w in text_lower for w in ["!", "！", "好", "厉害"]):
            return "表示赞叹时"
        elif any(w in text_lower for w in ["哈哈", "呵呵", "嘿嘿"]):
            return "轻松聊天时"
        elif any(w in text_lower for w in ["谢谢", "感谢", "辛苦"]):
            return "表示感谢时"
        else:
            return "日常交流时"

    def _extract_style(self, text: str) -> str:
        if len(text) <= 20:
            return f"使用 {text[:10]}"
        else:
            return f"使用 {text[:10]}..."

    def _find_or_create_expression(self, expr_data: dict[str, str]) -> str | None:
        situation = expr_data["situation"]
        style = expr_data["style"]
        content = expr_data["content"]

        for expr in self.expressions.values():
            if expr.situation == situation and expr.style == style:
                expr.count += 1
                expr.last_active_time = time.time()
                if content not in expr.content_list:
                    expr.content_list.append(content)
                return expr.id

            similarity = self._calculate_similarity(situation, expr.situation)
            if similarity >= 0.75:
                expr.count += 1
                expr.last_active_time = time.time()
                if content not in expr.content_list:
                    expr.content_list.append(content)
                return expr.id

        expr = Expression(
            id=self._generate_id("expr"),
            situation=situation,
            style=style,
            content_list=[content],
        )
        self.expressions[expr.id] = expr
        return expr.id

    def _extract_jargons(self, content: str) -> list[str]:
        jargons = set()

        abbreviations = re.findall(r'\b[A-Z]{2,}\b', content)
        jargons.update(abbreviations)

        lower_abbr = re.findall(r'\b[a-z]{2,}\b', content)
        for abbr in lower_abbr:
            if len(abbr) <= 5 and abbr not in self._common_words:
                jargons.add(abbr)

        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', content)
        for word in chinese_words:
            if word not in self._common_words:
                if self._is_potential_jargon(word, content):
                    jargons.add(word)

        return list(jargons)

    def _is_potential_jargon(self, word: str, context: str) -> bool:
        if word in self._common_words:
            return False

        if re.match(r'^[\u4e00-\u9fff]{2}$', word):
            common_two_chars = {"什么", "怎么", "这样", "那样", "这个", "那个"}
            if word in common_two_chars:
                return False

        return True

    def _find_or_create_jargon(self, content: str, context: str) -> str | None:
        content = content.strip()
        if not content:
            return None

        for jargon in self.jargons.values():
            if jargon.content.lower() == content.lower():
                jargon.count += 1
                if context not in jargon.raw_content:
                    jargon.raw_content.append(context)
                return jargon.id

        jargon = JargonEntry(
            id=self._generate_id("jargon"),
            content=content,
            raw_content=[context],
        )
        self.jargons[jargon.id] = jargon
        return jargon.id

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        if text1 == text2:
            return 1.0

        words1 = set(text1.lower())
        words2 = set(text2.lower())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    async def infer_jargon_meaning(
        self,
        jargon_id: str,
        llm_client: Any | None = None,
    ) -> str | None:
        jargon = self.jargons.get(jargon_id)
        if not jargon:
            return None

        if jargon.is_complete:
            return jargon.meaning

        thresholds = [3, 6, 10, 20, 40, 60, 100]
        should_infer = False
        for threshold in thresholds:
            if jargon.count >= threshold and jargon.last_inference_count < threshold:
                should_infer = True
                break

        if not should_infer:
            return jargon.meaning

        if llm_client:
            try:
                context_text = "\n".join(jargon.raw_content[-5:])
                prompt = f"""请根据以下上下文，推断"{jargon.content}"这个词条的含义。

上下文：
{context_text}

要求：
1. 如果这是黑话、俚语或网络用语，请推断其含义
2. 如果含义明确，也请说明
3. 输出格式：{{"meaning": "含义说明", "is_jargon": true/false}}

请直接输出JSON："""

                response = await llm_client.generate(prompt)
                if response:
                    try:
                        result = json.loads(response.strip())
                        jargon.meaning = result.get("meaning", "")
                        jargon.is_jargon = result.get("is_jargon", True)
                    except json.JSONDecodeError:
                        jargon.meaning = response.strip()

                jargon.last_inference_count = jargon.count

                if jargon.count >= 100:
                    jargon.is_complete = True

                self._save_jargons()
                return jargon.meaning
            except Exception:
                pass

        return jargon.meaning

    def get_valid_expressions(self, limit: int = 20) -> list[Expression]:
        valid = [
            e for e in self.expressions.values()
            if not e.rejected and e.count >= 2
        ]
        valid.sort(key=lambda x: x.count, reverse=True)
        return valid[:limit]

    def get_jargons_with_meaning(self, limit: int = 20) -> list[JargonEntry]:
        valid = [
            j for j in self.jargons.values()
            if j.is_jargon and j.meaning
        ]
        valid.sort(key=lambda x: x.count, reverse=True)
        return valid[:limit]

    def format_expressions_for_prompt(self, limit: int = 10) -> str:
        expressions = self.get_valid_expressions(limit)
        if not expressions:
            return ""

        lines = ["## 学到的表达方式"]
        for expr in expressions:
            lines.append(f"- 当{expr.situation}，可以{expr.style}")

        return "\n".join(lines)

    def format_jargons_for_prompt(self, limit: int = 10) -> str:
        jargons = self.get_jargons_with_meaning(limit)
        if not jargons:
            return ""

        lines = ["## 已知黑话/俚语"]
        for jargon in jargons:
            if jargon.meaning:
                lines.append(f"- {jargon.content}: {jargon.meaning}")

        return "\n".join(lines)

    def get_statistics(self) -> dict[str, Any]:
        return {
            "total_expressions": len(self.expressions),
            "valid_expressions": len([e for e in self.expressions.values() if not e.rejected]),
            "total_jargons": len(self.jargons),
            "jargons_with_meaning": len([j for j in self.jargons.values() if j.meaning]),
        }


self_learning_system = SelfLearningSystem()
