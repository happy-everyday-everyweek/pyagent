"""
PyAgent 邮件模块 - AI邮件助手
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .client import Email


class EmailCategory(Enum):
    WORK = "work"
    PERSONAL = "personal"
    PROMOTIONAL = "promotional"
    SOCIAL = "social"
    FINANCIAL = "financial"
    TRAVEL = "travel"
    SHOPPING = "shopping"
    OTHER = "other"


class EmailUrgency(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ActionItem:
    description: str
    due_date: str | None = None
    priority: str = "medium"


class AIEmailAssistant:
    """AI邮件助手"""

    def __init__(self, llm_client: Any | None = None):
        self.llm_client = llm_client

    async def summarize_email(self, email_obj: Email) -> str:
        if not self.llm_client:
            return self._simple_summarize(email_obj)

        prompt = f"""请总结以下邮件的要点：

发件人: {email_obj.from_address}
主题: {email_obj.subject}
内容: {email_obj.body_text[:1000]}

请用简洁的语言总结邮件的主要内容（不超过100字）。"""

        try:
            response = await self.llm_client.chat(prompt)
            return response.get("content", self._simple_summarize(email_obj))
        except Exception:
            return self._simple_summarize(email_obj)

    def _simple_summarize(self, email_obj: Email) -> str:
        lines = email_obj.body_text.split("\n")
        meaningful_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 20]
        if meaningful_lines:
            text = meaningful_lines[0]
            return text[:100] + "..." if len(text) > 100 else text
        return f"来自 {email_obj.from_address} 的邮件: {email_obj.subject}"

    async def suggest_reply(self, email_obj: Email) -> str:
        if not self.llm_client:
            return "感谢您的邮件，我会尽快处理。"

        prompt = f"""请为以下邮件撰写一个回复：

发件人: {email_obj.from_address}
主题: {email_obj.subject}
内容: {email_obj.body_text[:1000]}

请撰写一个礼貌、专业的回复。"""

        try:
            response = await self.llm_client.chat(prompt)
            return response.get("content", "感谢您的邮件，我会尽快处理。")
        except Exception:
            return "感谢您的邮件，我会尽快处理。"

    def categorize_email(self, email_obj: Email) -> EmailCategory:
        subject_lower = email_obj.subject.lower()
        from_lower = email_obj.from_address.lower()
        body_lower = email_obj.body_text.lower()[:500]

        work_keywords = ["会议", "项目", "报告", "工作", "deadline", "meeting", "project", "report"]
        promo_keywords = ["优惠", "促销", "折扣", "sale", "discount", "offer", "deal"]
        social_keywords = ["邀请", "朋友", "聚会", "invite", "party", "friend"]
        financial_keywords = ["账单", "支付", "银行", "bill", "payment", "bank", "invoice"]
        travel_keywords = ["航班", "酒店", "预订", "flight", "hotel", "booking", "reservation"]
        shopping_keywords = ["订单", "配送", "购买", "order", "delivery", "purchase", "shipping"]

        all_text = f"{subject_lower} {from_lower} {body_lower}"

        if any(kw in all_text for kw in work_keywords):
            return EmailCategory.WORK
        if any(kw in all_text for kw in promo_keywords):
            return EmailCategory.PROMOTIONAL
        if any(kw in all_text for kw in social_keywords):
            return EmailCategory.SOCIAL
        if any(kw in all_text for kw in financial_keywords):
            return EmailCategory.FINANCIAL
        if any(kw in all_text for kw in travel_keywords):
            return EmailCategory.TRAVEL
        if any(kw in all_text for kw in shopping_keywords):
            return EmailCategory.SHOPPING

        return EmailCategory.OTHER

    def detect_urgency(self, email_obj: Email) -> EmailUrgency:
        subject_lower = email_obj.subject.lower()
        body_lower = email_obj.body_text.lower()[:500]

        high_keywords = ["紧急", "立即", "重要", "urgent", "immediately", "asap", "important", "critical"]
        medium_keywords = ["请回复", "尽快", "reply", "soon", "today"]

        all_text = f"{subject_lower} {body_lower}"

        if any(kw in all_text for kw in high_keywords):
            return EmailUrgency.HIGH
        if any(kw in all_text for kw in medium_keywords):
            return EmailUrgency.MEDIUM

        return EmailUrgency.LOW

    def extract_action_items(self, email_obj: Email) -> list[ActionItem]:
        items: list[ActionItem] = []
        text = email_obj.body_text

        patterns = [
            r"请(.+?)[。\n]",
            r"需要(.+?)[。\n]",
            r"务必(.+?)[。\n]",
            r"Please (.+?)[.\n]",
            r"Need to (.+?)[.\n]",
            r"Must (.+?)[.\n]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 5 and len(match) < 200:
                    items.append(ActionItem(description=match.strip()))

        return items[:5]

    async def analyze_email(self, email_obj: Email) -> dict[str, Any]:
        summary = await self.summarize_email(email_obj)
        category = self.categorize_email(email_obj)
        urgency = self.detect_urgency(email_obj)
        action_items = self.extract_action_items(email_obj)

        return {
            "summary": summary,
            "category": category.value,
            "urgency": urgency.value,
            "action_items": [{"description": item.description} for item in action_items],
            "has_attachments": len(email_obj.attachments) > 0,
            "attachment_count": len(email_obj.attachments),
        }
