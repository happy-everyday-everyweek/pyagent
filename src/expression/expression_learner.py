"""
PyAgent 表达学习系统 - 表达学习器

参考MaiBot的ExpressionLearner设计，学习用户的表达方式。
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Expression:
    """表达方式"""
    content: str
    context: str = ""
    source: str = ""
    usage_count: int = 0
    last_used: float = 0.0


@dataclass
class JargonEntry:
    """黑话条目"""
    term: str
    meaning: str = ""
    examples: list[str] = field(default_factory=list)
    source: str = ""


class ExpressionLearner:
    """表达学习器"""

    def __init__(self, data_dir: str = "data/expressions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.expressions: list[Expression] = []
        self.jargons: dict[str, JargonEntry] = {}

        self._load_data()

        self._jargon_patterns = [
            r"[a-zA-Z]{2,}",
            r"[^\w\s]{2,}",
            r"\d{2,}",
        ]

    def _load_data(self) -> None:
        """加载数据"""
        expressions_file = self.data_dir / "expressions.json"
        if expressions_file.exists():
            try:
                with open(expressions_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.expressions = [
                        Expression(**e) for e in data.get("expressions", [])
                    ]
                    self.jargons = {
                        k: JargonEntry(**v)
                        for k, v in data.get("jargons", {}).items()
                    }
            except Exception:
                pass

    def _save_data(self) -> None:
        """保存数据"""
        expressions_file = self.data_dir / "expressions.json"

        try:
            data = {
                "expressions": [
                    {
                        "content": e.content,
                        "context": e.context,
                        "source": e.source,
                        "usage_count": e.usage_count,
                        "last_used": e.last_used
                    }
                    for e in self.expressions
                ],
                "jargons": {
                    k: {
                        "term": v.term,
                        "meaning": v.meaning,
                        "examples": v.examples,
                        "source": v.source
                    }
                    for k, v in self.jargons.items()
                }
            }

            with open(expressions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    async def learn_and_store(
        self,
        message: str,
        user_id: str = "",
        context: str = ""
    ) -> dict[str, Any]:
        """学习并存储表达方式"""
        result = {
            "expressions_learned": 0,
            "jargons_found": 0
        }

        expressions = self._extract_expressions(message)
        for expr in expressions:
            if self._should_store_expression(expr):
                self._store_expression(expr, context, user_id)
                result["expressions_learned"] += 1

        jargons = self._extract_jargons(message)
        for jargon in jargons:
            if jargon not in self.jargons:
                self.jargons[jargon] = JargonEntry(
                    term=jargon,
                    source=user_id
                )
                result["jargons_found"] += 1

        if result["expressions_learned"] > 0 or result["jargons_found"] > 0:
            self._save_data()

        return result

    def _extract_expressions(self, message: str) -> list[str]:
        """提取表达方式"""
        sentences = re.split(r"[。！？\n]+", message)

        expressions = []
        for sentence in sentences:
            sentence = sentence.strip()
            if 5 <= len(sentence) <= 50:
                if self._is_valid_expression(sentence):
                    expressions.append(sentence)

        return expressions

    def _is_valid_expression(self, text: str) -> bool:
        """判断是否是有效表达"""
        if not text:
            return False

        if re.match(r"^[\d\s\W]+$", text):
            return False

        if len(text) < 3:
            return False

        return True

    def _should_store_expression(self, expression: str) -> bool:
        """判断是否应该存储表达"""
        for existing in self.expressions:
            if existing.content == expression:
                existing.usage_count += 1
                return False

        return True

    def _store_expression(
        self,
        expression: str,
        context: str,
        source: str
    ) -> None:
        """存储表达方式"""
        import time

        expr = Expression(
            content=expression,
            context=context,
            source=source,
            usage_count=1,
            last_used=time.time()
        )
        self.expressions.append(expr)

        if len(self.expressions) > 1000:
            self.expressions.sort(key=lambda x: x.usage_count, reverse=True)
            self.expressions = self.expressions[:500]

    def _extract_jargons(self, message: str) -> list[str]:
        """提取黑话"""
        jargons = set()

        words = re.findall(r"[\u4e00-\u9fff]+", message)
        for word in words:
            if 2 <= len(word) <= 4:
                if self._is_potential_jargon(word, message):
                    jargons.add(word)

        abbreviations = re.findall(r"\b[A-Z]{2,}\b", message)
        jargons.update(abbreviations)

        return list(jargons)

    def _is_potential_jargon(self, word: str, context: str) -> bool:
        """判断是否可能是黑话"""
        common_words = {
            "的", "是", "在", "有", "和", "了", "不", "我",
            "你", "他", "她", "它", "这", "那", "什么", "怎么"
        }

        if word in common_words:
            return False

        return True

    def get_random_expression(self) -> str | None:
        """获取随机表达"""
        if not self.expressions:
            return None

        import random
        expr = random.choice(self.expressions)
        return expr.content

    def get_expressions_by_context(self, context: str) -> list[str]:
        """根据上下文获取表达"""
        return [
            e.content for e in self.expressions
            if context.lower() in e.context.lower()
        ]

    def get_jargon_meaning(self, term: str) -> str | None:
        """获取黑话含义"""
        entry = self.jargons.get(term)
        if entry:
            return entry.meaning
        return None

    def update_jargon_meaning(
        self,
        term: str,
        meaning: str,
        example: str = ""
    ) -> None:
        """更新黑话含义"""
        if term in self.jargons:
            self.jargons[term].meaning = meaning
            if example:
                self.jargons[term].examples.append(example)
        else:
            self.jargons[term] = JargonEntry(
                term=term,
                meaning=meaning,
                examples=[example] if example else []
            )

        self._save_data()

    def get_all_jargons(self) -> dict[str, JargonEntry]:
        """获取所有黑话"""
        return self.jargons.copy()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_expressions": len(self.expressions),
            "total_jargons": len(self.jargons),
            "top_expressions": [
                {"content": e.content, "usage_count": e.usage_count}
                for e in sorted(
                    self.expressions,
                    key=lambda x: x.usage_count,
                    reverse=True
                )[:10]
            ]
        }


expression_learner = ExpressionLearner()
