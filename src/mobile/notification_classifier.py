"""
PyAgent 移动端模块 - 通知分类器
移植自 OpenKiwi NotificationClassifier
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .notification import Notification, NotificationCategory


class NotificationImportance(Enum):
    """通知重要性"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    SPAM = "spam"


@dataclass
class ClassifiedNotification:
    """分类后的通知"""
    notification: Notification
    importance: NotificationImportance
    sub_category: str = ""
    action_required: bool = False
    suggested_action: str = ""
    keywords: list[str] = field(default_factory=list)
    entities: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification": self.notification.to_dict(),
            "importance": self.importance.value,
            "sub_category": self.sub_category,
            "action_required": self.action_required,
            "suggested_action": self.suggested_action,
            "keywords": self.keywords,
            "entities": self.entities,
        }


class NotificationClassifier:
    """通知分类器

    对通知进行智能分类和重要性评估。
    移植自 OpenKiwi 的 NotificationClassifier。
    """

    CRITICAL_KEYWORDS = [
        "紧急", "重要", "立即", "马上", "验证码", "校验码",
        "urgent", "important", "immediately", "verification", "code",
        "安全", "风险", "异常", "登录", "支付", "转账",
        "security", "risk", "login", "payment", "transfer",
    ]

    HIGH_KEYWORDS = [
        "快递", "取件", "配送", "外卖", "订单",
        "delivery", "package", "order", "food",
        "会议", "日程", "提醒", "预约",
        "meeting", "schedule", "reminder", "appointment",
        "来电", "missed call", "未接",
    ]

    SPAM_KEYWORDS = [
        "优惠", "促销", "折扣", "红包", "抽奖",
        "discount", "sale", "promotion", "coupon",
        "点击", "链接", "领取", "立即查看",
        "click", "link", "claim", "view now",
    ]

    VERIFICATION_PATTERNS = [
        re.compile(r"验证码[:：]?\s*\d{4,8}"),
        re.compile(r"校验码[:：]?\s*\d{4,8}"),
        re.compile(r"code[:：]?\s*\d{4,8}", re.IGNORECASE),
    ]

    DELIVERY_PATTERNS = [
        re.compile(r"快递.*?(\d{10,20})"),
        re.compile(r"取件码[:：]?\s*(\d{4,8})"),
        re.compile(r"快递员.*?(\d{11})"),
        re.compile(r"快递柜.*?(\w+)"),
    ]

    SCHEDULE_PATTERNS = [
        re.compile(r"(\d{1,2})月(\d{1,2})[日号].*?(\d{1,2}):(\d{2})"),
        re.compile(r"(\d{1,2}):(\d{2}).*?(?:会议|日程|预约)"),
        re.compile(r"(?:明天|后天|下周[一二三四五六日]).*?(\d{1,2}):(\d{2})"),
    ]

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def classify(self, notification: Notification) -> ClassifiedNotification:
        """分类通知

        Args:
            notification: 通知对象

        Returns:
            ClassifiedNotification: 分类后的通知
        """
        text = f"{notification.title} {notification.text}".lower()

        importance = self._assess_importance(notification, text)
        sub_category = self._detect_sub_category(notification, text)
        keywords = self._extract_keywords(text)
        entities = self._extract_entities(text)
        action_required, suggested_action = self._determine_action(
            notification, text, sub_category
        )

        return ClassifiedNotification(
            notification=notification,
            importance=importance,
            sub_category=sub_category,
            action_required=action_required,
            suggested_action=suggested_action,
            keywords=keywords,
            entities=entities,
        )

    def _assess_importance(
        self,
        notification: Notification,
        text: str
    ) -> NotificationImportance:
        """评估通知重要性"""
        for pattern in self.VERIFICATION_PATTERNS:
            if pattern.search(text):
                return NotificationImportance.CRITICAL

        for keyword in self.CRITICAL_KEYWORDS:
            if keyword.lower() in text:
                return NotificationImportance.CRITICAL

        for keyword in self.HIGH_KEYWORDS:
            if keyword.lower() in text:
                return NotificationImportance.HIGH

        for keyword in self.SPAM_KEYWORDS:
            if keyword.lower() in text:
                return NotificationImportance.SPAM

        if notification.category == NotificationCategory.CALL:
            return NotificationImportance.HIGH

        if notification.category == NotificationCategory.MESSAGE:
            return NotificationImportance.NORMAL

        if notification.category == NotificationCategory.SYSTEM:
            return NotificationImportance.LOW

        return NotificationImportance.NORMAL

    def _detect_sub_category(self, notification: Notification, text: str) -> str:
        """检测子类别"""
        for pattern in self.VERIFICATION_PATTERNS:
            if pattern.search(text):
                return "verification_code"

        for pattern in self.DELIVERY_PATTERNS:
            if pattern.search(text):
                return "delivery"

        for pattern in self.SCHEDULE_PATTERNS:
            if pattern.search(text):
                return "schedule"

        if any(kw in text for kw in ["银行", "支付", "转账", "bank", "payment"]):
            return "financial"

        if any(kw in text for kw in ["来电", "未接", "missed call"]):
            return "missed_call"

        return notification.category.value

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        keywords = []

        all_keywords = (
            self.CRITICAL_KEYWORDS +
            self.HIGH_KEYWORDS +
            self.SPAM_KEYWORDS
        )

        for keyword in all_keywords:
            if keyword.lower() in text:
                keywords.append(keyword)

        return keywords[:5]

    def _extract_entities(self, text: str) -> dict[str, Any]:
        """提取实体"""
        entities = {}

        phone_pattern = re.compile(r"(?:\+86)?1[3-9]\d{9}")
        phones = phone_pattern.findall(text)
        if phones:
            entities["phones"] = phones

        code_pattern = re.compile(r"\b\d{4,8}\b")
        codes = code_pattern.findall(text)
        if codes:
            entities["codes"] = codes

        time_pattern = re.compile(r"\d{1,2}:\d{2}")
        times = time_pattern.findall(text)
        if times:
            entities["times"] = times

        tracking_pattern = re.compile(r"\d{10,20}")
        tracking = tracking_pattern.findall(text)
        if tracking:
            entities["tracking_numbers"] = tracking

        return entities

    def _determine_action(
        self,
        notification: Notification,
        text: str,
        sub_category: str
    ) -> tuple[bool, str]:
        """确定是否需要操作及建议操作"""
        if sub_category == "verification_code":
            return True, "copy_code"

        if sub_category == "delivery":
            return True, "view_delivery"

        if sub_category == "missed_call":
            return True, "call_back"

        if sub_category == "schedule":
            return True, "add_to_calendar"

        if sub_category == "financial":
            return True, "review_transaction"

        return False, ""


notification_classifier = NotificationClassifier()
