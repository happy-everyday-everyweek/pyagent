"""
PyAgent 拟人化系统

参考MaiBot的设计，实现深度拟人化：
- 情感表达系统
- 行为规划（懂得在合适的时间说话）
- 个性系统（性格特征、状态切换）
- 自然语言风格Prompt
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EmotionType(Enum):
    """情感类型"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    CURIOUS = "curious"
    THOUGHTFUL = "thoughtful"
    PLAYFUL = "playful"
    CARING = "caring"
    SHY = "shy"


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
class PersonalityState:
    """个性状态"""
    name: str
    description: str
    traits: list[str] = field(default_factory=list)
    speaking_style: str = ""
    mood_modifier: float = 0.0


@dataclass
class EmotionState:
    """情感状态"""
    emotion_type: EmotionType = EmotionType.NEUTRAL
    intensity: float = 0.5
    duration: float = 0.0
    trigger: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "emotion_type": self.emotion_type.value,
            "intensity": self.intensity,
            "duration": self.duration,
            "trigger": self.trigger,
            "timestamp": self.timestamp,
        }


@dataclass
class ConversationGoal:
    """对话目标"""
    goal: str
    reasoning: str
    priority: int = 1
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    achieved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "reasoning": self.reasoning,
            "priority": self.priority,
            "created_at": self.created_at,
            "achieved": self.achieved,
        }


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


DEFAULT_PERSONALITY = PersonalityState(
    name="默认",
    description="一个友善、乐于助人的AI助手",
    traits=["友善", "耐心", "细心", "幽默"],
    speaking_style="自然、简洁、口语化",
)

PERSONALITY_STATES = [
    PersonalityState(
        name="开心",
        description="心情愉悦，充满活力",
        traits=["开朗", "热情", "健谈"],
        speaking_style="轻快、活泼、带点俏皮",
        mood_modifier=0.2,
    ),
    PersonalityState(
        name="思考",
        description="正在认真思考问题",
        traits=["专注", "严谨", "认真"],
        speaking_style="简洁、准确、有条理",
        mood_modifier=-0.1,
    ),
    PersonalityState(
        name="困倦",
        description="有点困了，反应可能慢一些",
        traits=["慵懒", "随意", "慢热"],
        speaking_style="简短、慵懒、偶尔打哈欠",
        mood_modifier=-0.2,
    ),
    PersonalityState(
        name="好奇",
        description="对某个话题很感兴趣",
        traits=["好奇", "追问", "探索"],
        speaking_style="带着疑问、喜欢追问",
        mood_modifier=0.1,
    ),
]


class PersonaSystem:
    """拟人化系统"""

    def __init__(
        self,
        name: str = "小助手",
        base_personality: PersonalityState | None = None,
        state_probability: float = 0.15,
    ):
        self.name = name
        self.base_personality = base_personality or DEFAULT_PERSONALITY
        self.state_probability = state_probability
        self.current_state: PersonalityState | None = None
        self.emotion_state = EmotionState()
        self.goals: list[ConversationGoal] = []
        self.max_goals = 3

    def get_persona_prompt(self) -> str:
        personality = self.current_state or self.base_personality
        traits_str = "、".join(personality.traits) if personality.traits else "友善"

        prompt = f"你的名字是{self.name}，你{personality.description}。你的性格特点是：{traits_str}。"

        if personality.speaking_style:
            prompt += f"说话风格：{personality.speaking_style}。"

        return prompt

    def maybe_switch_state(self) -> bool:
        if random.random() < self.state_probability:
            self.current_state = random.choice(PERSONALITY_STATES)
            return True
        return False

    def reset_state(self) -> None:
        self.current_state = None

    def update_emotion(
        self,
        emotion_type: EmotionType,
        intensity: float = 0.5,
        trigger: str = "",
    ) -> None:
        self.emotion_state = EmotionState(
            emotion_type=emotion_type,
            intensity=intensity,
            trigger=trigger,
        )

    def add_goal(self, goal: str, reasoning: str, priority: int = 1) -> None:
        if len(self.goals) >= self.max_goals:
            self.goals.pop(0)
        self.goals.append(ConversationGoal(
            goal=goal,
            reasoning=reasoning,
            priority=priority,
        ))

    def clear_goals(self) -> None:
        self.goals = []

    def get_goals_prompt(self) -> str:
        if not self.goals:
            return "- 目前没有明确对话目标"

        lines = []
        for g in self.goals:
            status = " (已完成)" if g.achieved else ""
            lines.append(f"- 目标：{g.goal}{status}\n  原因：{g.reasoning}")
        return "\n".join(lines)

    def get_emotion_modifier(self) -> str:
        emotion = self.emotion_state
        modifiers = {
            EmotionType.NEUTRAL: "",
            EmotionType.HAPPY: "心情不错，",
            EmotionType.SAD: "有点低落，",
            EmotionType.ANGRY: "有点不高兴，",
            EmotionType.SURPRISED: "有点惊讶，",
            EmotionType.CURIOUS: "很好奇，",
            EmotionType.THOUGHTFUL: "在思考，",
            EmotionType.PLAYFUL: "有点调皮，",
            EmotionType.CARING: "很关心，",
            EmotionType.SHY: "有点害羞，",
        }
        return modifiers.get(emotion.emotion_type, "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "current_state": self.current_state.name if self.current_state else None,
            "emotion": self.emotion_state.to_dict(),
            "goals": [g.to_dict() for g in self.goals],
        }


persona_system = PersonaSystem()
