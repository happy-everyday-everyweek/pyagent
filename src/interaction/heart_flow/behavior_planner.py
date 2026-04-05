"""
PyAgent 聊天Agent核心 - 行为规划系统

参考MaiBot的设计，实现智能行为规划：
- 懂得在合适的时间说话
- 主动问候
- 时机控制
- 频率控制
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Any


class ActionType(Enum):
    """行动类型"""
    DIRECT_REPLY = "direct_reply"
    SEND_NEW_MESSAGE = "send_new_message"
    WAIT = "wait"
    LISTENING = "listening"
    END_CONVERSATION = "end_conversation"
    SAY_GOODBYE = "say_goodbye"
    FETCH_KNOWLEDGE = "fetch_knowledge"
    RETHINK_GOAL = "rethink_goal"


@dataclass
class ActionDecision:
    """行动决策"""
    action: ActionType
    reason: str
    confidence: float = 0.8
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "reason": self.reason,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


@dataclass
class ConversationContext:
    """对话上下文"""
    message_count: int = 0
    user_message_count: int = 0
    bot_message_count: int = 0
    consecutive_bot_messages: int = 0
    consecutive_user_silence: int = 0
    last_bot_action: str | None = None
    last_user_message_time: float = 0.0
    conversation_duration: float = 0.0
    topics_discussed: list[str] = field(default_factory=list)


class BehaviorPlanner:
    """行为规划器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        self.max_consecutive_replies = self.config.get("max_consecutive_replies", 3)
        self.silence_threshold = self.config.get("silence_threshold", 300)
        self.greeting_probability = self.config.get("greeting_probability", 0.1)
        self.follow_up_probability = self.config.get("follow_up_probability", 0.3)

        self._greeting_times = self._get_greeting_times()
        self._last_greeting_date: str | None = None
        self._greeted_today = False

    def _get_greeting_times(self) -> dict[str, tuple[time, time]]:
        """获取问候时间段"""
        return {
            "morning": (time(6, 0), time(9, 0)),
            "noon": (time(11, 0), time(13, 0)),
            "afternoon": (time(14, 0), time(16, 0)),
            "evening": (time(18, 0), time(20, 0)),
            "night": (time(22, 0), time(23, 59)),
        }

    def should_greet(self) -> tuple[bool, str]:
        """判断是否应该问候"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        if self._last_greeting_date == today and self._greeted_today:
            return False, ""

        current_time = now.time()

        for greeting_type, (start, end) in self._greeting_times.items():
            if start <= current_time <= end:
                if random.random() < self.greeting_probability:
                    self._last_greeting_date = today
                    self._greeted_today = True
                    return True, greeting_type

        return False, ""

    def get_greeting_message(self, greeting_type: str) -> str:
        """获取问候消息"""
        greetings = {
            "morning": ["早安", "早上好", "早啊"],
            "noon": ["中午好", "吃午饭了吗"],
            "afternoon": ["下午好", "下午愉快"],
            "evening": ["晚上好", "傍晚好"],
            "night": ["晚安", "早点休息"],
        }

        messages = greetings.get(greeting_type, ["你好"])
        return random.choice(messages)

    def plan_action(
        self,
        context: ConversationContext,
        is_mentioned: bool = False,
        is_at: bool = False,
        force_reply: bool = False,
    ) -> ActionDecision:
        """规划行动"""

        if force_reply or is_at or is_mentioned:
            return ActionDecision(
                action=ActionType.DIRECT_REPLY,
                reason="用户提及了我，必须回复",
                confidence=1.0,
            )

        if context.consecutive_bot_messages >= self.max_consecutive_replies:
            return ActionDecision(
                action=ActionType.WAIT,
                reason="已经连续发送多条消息，等待对方回复",
                confidence=0.9,
            )

        if context.consecutive_user_silence >= 5:
            should_greet, greeting_type = self.should_greet()
            if should_greet:
                return ActionDecision(
                    action=ActionType.SEND_NEW_MESSAGE,
                    reason=f"用户长时间沉默，主动问候（{greeting_type}）",
                    confidence=0.7,
                )
            return ActionDecision(
                action=ActionType.WAIT,
                reason="用户长时间沉默，继续等待",
                confidence=0.8,
            )

        if context.last_bot_action == "direct_reply":
            if random.random() < self.follow_up_probability:
                return ActionDecision(
                    action=ActionType.SEND_NEW_MESSAGE,
                    reason="补充或追问",
                    confidence=0.6,
                )

        if context.conversation_duration > 1800:
            return ActionDecision(
                action=ActionType.END_CONVERSATION,
                reason="对话持续时间较长，考虑结束",
                confidence=0.5,
            )

        return ActionDecision(
            action=ActionType.DIRECT_REPLY,
            reason="正常回复",
            confidence=0.8,
        )

    def should_follow_up(
        self,
        last_reply: str,
        context: ConversationContext,
    ) -> bool:
        """判断是否应该追问"""
        if context.consecutive_bot_messages >= self.max_consecutive_replies:
            return False

        question_indicators = ["?", "？", "吗", "呢", "啊"]
        has_question = any(indicator in last_reply for indicator in question_indicators)

        if has_question:
            return False

        return random.random() < self.follow_up_probability

    def get_follow_up_type(self, last_reply: str, context: ConversationContext) -> str:
        """获取追问类型"""
        if context.message_count < 5:
            return "elaborate"

        if "?" in last_reply or "？" in last_reply:
            return "clarify"

        return random.choice(["elaborate", "clarify", "digress"])

    def calculate_reply_timing(
        self,
        message_length: int,
        is_urgent: bool = False,
    ) -> float:
        """计算回复时机"""
        base_delay = 0.5

        typing_speed = 0.05
        typing_delay = message_length * typing_speed

        natural_variation = random.uniform(0.1, 0.5)

        if is_urgent:
            return base_delay + typing_delay * 0.5

        return base_delay + typing_delay + natural_variation

    def should_end_conversation(
        self,
        context: ConversationContext,
        last_messages: list[str],
    ) -> bool:
        """判断是否应该结束对话"""
        end_indicators = [
            "再见", "拜拜", "晚安", "下次聊", "先这样",
            "好的", "嗯", "行", "知道了", "明白了",
        ]

        if last_messages:
            last_message = last_messages[-1].lower()
            for indicator in end_indicators:
                if indicator in last_message:
                    return True

        if context.consecutive_user_silence >= 10:
            return True

        if context.conversation_duration > 3600:
            return True

        return False

    def get_end_conversation_message(self) -> str:
        """获取结束对话消息"""
        messages = [
            "好的，那先这样",
            "嗯，有需要再找我",
            "好的，随时找我",
            "嗯嗯，下次聊",
        ]
        return random.choice(messages)


behavior_planner = BehaviorPlanner()
