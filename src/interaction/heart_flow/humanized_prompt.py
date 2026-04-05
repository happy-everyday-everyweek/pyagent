"""
PyAgent 聊天Agent核心 - 拟人化Prompt构建器

参考MaiBot的设计，实现拟人化的Prompt构建：
- 自然语言风格
- 情感表达
- 个性状态
- 行为规划
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


@dataclass
class ConversationGoal:
    """对话目标"""
    goal: str
    reasoning: str
    priority: int = 1
    achieved: bool = False
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class ActionContext:
    """行动上下文"""
    action_type: ActionType
    reason: str
    target_message_id: str | None = None
    last_action_type: str | None = None
    last_action_success: bool = True
    consecutive_replies: int = 0


class HumanizedPromptBuilder:
    """拟人化Prompt构建器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        self.bot_name = self.config.get("bot_name", "小助手")
        self.bot_alias = self.config.get("bot_alias", ["助手", "小助手"])

        self.base_personality = self.config.get(
            "personality",
            "是一个友善、乐于助人的AI助手，喜欢用轻松自然的方式与人交流"
        )

        self.personality_states: list[PersonalityState] = [
            PersonalityState(
                name="日常",
                description=self.base_personality,
                traits=["友善", "乐于助人", "轻松"],
                speaking_style="自然、简洁、口语化"
            ),
            PersonalityState(
                name="开心",
                description="心情不错，回复可以稍微活泼一点",
                traits=["活泼", "热情", "积极"],
                speaking_style="活泼、俏皮、带点表情",
                mood_modifier=0.2
            ),
            PersonalityState(
                name="思考",
                description="正在认真思考问题",
                traits=["认真", "专注", "深思熟虑"],
                speaking_style="沉稳、有条理、略带思考感",
                mood_modifier=-0.1
            ),
            PersonalityState(
                name="关心",
                description="很关心对方的情况",
                traits=["关心", "体贴", "温暖"],
                speaking_style="温柔、关切、有同理心",
                mood_modifier=0.1
            ),
        ]

        self.state_probability = self.config.get("state_probability", 0.15)

        self._current_state: PersonalityState | None = None
        self._emotion_state = EmotionState()

    def _get_current_personality(self) -> PersonalityState:
        """获取当前个性状态"""
        if self._current_state is None or random.random() < self.state_probability:
            self._current_state = random.choice(self.personality_states)
        return self._current_state

    def get_persona_text(self) -> str:
        """获取人设文本"""
        personality = self._get_current_personality()
        emotion_modifier = self._get_emotion_modifier()

        persona = f"你的名字是{self.bot_name}，你{personality.description}"
        if emotion_modifier:
            persona += f"，{emotion_modifier}"

        return persona

    def _get_emotion_modifier(self) -> str:
        """获取情感修饰语"""
        emotion = self._emotion_state
        modifiers = {
            EmotionType.NEUTRAL: "",
            EmotionType.HAPPY: "心情不错",
            EmotionType.SAD: "有点低落",
            EmotionType.ANGRY: "有点不高兴",
            EmotionType.SURPRISED: "有点惊讶",
            EmotionType.CURIOUS: "很好奇",
            EmotionType.THOUGHTFUL: "在思考",
            EmotionType.PLAYFUL: "有点调皮",
            EmotionType.CARING: "很关心",
            EmotionType.SHY: "有点害羞",
        }
        return modifiers.get(emotion.emotion_type, "")

    def update_emotion(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any] | None = None
    ) -> None:
        """更新情感状态"""
        if not messages:
            return

        last_message = messages[-1]
        content = last_message.get("content", "").lower()

        positive_words = ["谢谢", "感谢", "喜欢", "爱", "开心", "高兴", "棒", "好", "厉害", "赞"]
        negative_words = ["讨厌", "烦", "生气", "难过", "伤心", "不好", "差", "失望"]
        question_words = ["?", "？", "吗", "什么", "怎么", "为什么", "如何"]
        surprise_words = ["哇", "啊", "真的", "假的", "没想到"]

        positive_count = sum(1 for w in positive_words if w in content)
        negative_count = sum(1 for w in negative_words if w in content)
        question_count = sum(1 for w in question_words if w in content)
        surprise_count = sum(1 for w in surprise_words if w in content)

        max_count = max(positive_count, negative_count, question_count, surprise_count, 1)

        if positive_count == max_count and positive_count > 0:
            self._emotion_state.emotion_type = EmotionType.HAPPY
            self._emotion_state.intensity = min(1.0, 0.5 + positive_count * 0.1)
        elif negative_count == max_count and negative_count > 0:
            self._emotion_state.emotion_type = EmotionType.SAD
            self._emotion_state.intensity = min(1.0, 0.5 + negative_count * 0.1)
        elif surprise_count == max_count and surprise_count > 0:
            self._emotion_state.emotion_type = EmotionType.SURPRISED
            self._emotion_state.intensity = min(1.0, 0.5 + surprise_count * 0.1)
        elif question_count == max_count and question_count > 0:
            self._emotion_state.emotion_type = EmotionType.CURIOUS
            self._emotion_state.intensity = min(1.0, 0.5 + question_count * 0.05)
        else:
            self._emotion_state.emotion_type = EmotionType.NEUTRAL
            self._emotion_state.intensity = 0.5

        self._emotion_state.trigger = content[:50]
        self._emotion_state.timestamp = datetime.now().timestamp()

    def build_direct_reply_prompt(
        self,
        chat_history: str,
        goals: list[ConversationGoal] | None = None,
        knowledge: str = "",
        memory: str = "",
        expression_habits: str = "",
        jargon: str = "",
    ) -> str:
        """构建直接回复Prompt"""
        persona_text = self.get_persona_text()
        goals_str = self._format_goals(goals)
        emotion_prompt = self._get_emotion_prompt()

        prompt = f"""{persona_text}。现在你在参与一场聊天，请根据以下信息生成一条回复：

{self._build_knowledge_section(knowledge)}
{self._build_memory_section(memory)}
{self._build_expression_section(expression_habits)}
{self._build_jargon_section(jargon)}

当前对话目标：
{goals_str}

最近的聊天记录：
{chat_history}

{emotion_prompt}

请根据上述信息，结合聊天记录，回复对方。该回复应该：
1. 符合对话目标，以"你"的角度发言（不要自己与自己对话！）
2. 符合你的性格特征和身份细节
3. 通俗易懂，自然流畅，像正常聊天一样，简短（通常20字以内，除非特殊情况）
4. 可以适当利用相关知识，但不要生硬引用
5. 自然、得体，结合聊天记录逻辑合理，且没有重复表达同质内容

请注意把握聊天内容，不要回复的太有条理，可以有个性。请分清"你"和对方说的话，不要把"你"说的话当做对方说的话。
可以回复得自然随意一些，就像真人一样，注意把握聊天内容，整体风格可以平和、简短，不要刻意突出自身学科背景，不要说你说过的话，可以简短，多简短都可以，但是避免冗长。

请你注意不要输出多余内容(包括前后缀，冒号和引号，括号，表情等)，只输出回复内容。
不要输出多余内容(包括前后缀，冒号和引号，括号，表情包，at或 @等 )。

请直接输出回复内容，不需要任何额外格式。"""

        return prompt

    def build_follow_up_prompt(
        self,
        chat_history: str,
        goals: list[ConversationGoal] | None = None,
        knowledge: str = "",
        memory: str = "",
        last_reply: str = "",
    ) -> str:
        """构建追问/补充Prompt"""
        persona_text = self.get_persona_text()
        goals_str = self._format_goals(goals)
        emotion_prompt = self._get_emotion_prompt()

        prompt = f"""{persona_text}。现在你在参与一场聊天，**刚刚你已经发送了一条或多条消息**，现在请根据以下信息再发一条新消息：

当前对话目标：
{goals_str}

{self._build_knowledge_section(knowledge)}
{self._build_memory_section(memory)}

最近的聊天记录：
{chat_history}

你刚刚发送的消息：{last_reply}

{emotion_prompt}

请根据上述信息，结合聊天记录，继续发一条新消息（例如对之前消息的补充，深入话题，或追问等等）。该消息应该：
1. 符合对话目标，以"你"的角度发言（不要自己与自己对话！）
2. 符合你的性格特征和身份细节
3. 通俗易懂，自然流畅，像正常聊天一样，简短（通常20字以内，除非特殊情况）
4. 可以适当利用相关知识，但不要生硬引用
5. 跟之前你发的消息自然的衔接，逻辑合理，且没有重复表达同质内容或部分重叠内容

请注意把握聊天内容，不用太有条理，可以有个性。请分清"你"和对方说的话，不要把"你"说的话当做对方说的话。
这条消息可以自然随意一些，就像真人一样，注意把握聊天内容，整体风格可以平和、简短，不要刻意突出自身学科背景，不要说你说过的话，可以简短，多简短都可以，但是避免冗长。

请你注意不要输出多余内容(包括前后缀，冒号和引号，括号，表情等)，只输出消息内容。
不要输出多余内容(包括前后缀，冒号和引号，括号，表情包，at或 @等 )。

请直接输出回复内容，不需要任何额外格式。"""

        return prompt

    def build_goodbye_prompt(
        self,
        chat_history: str,
    ) -> str:
        """构建告别语Prompt"""
        persona_text = self.get_persona_text()

        prompt = f"""{persona_text}。你在参与一场聊天，现在对话似乎已经结束，你决定再发一条最后的消息来圆满结束。

最近的聊天记录：
{chat_history}

请根据上述信息，结合聊天记录，构思一条**简短、自然、符合你人设**的最后的消息。
这条消息应该：
1. 从你自己的角度发言。
2. 符合你的性格特征和身份细节。
3. 通俗易懂，自然流畅，通常很简短。
4. 自然地为这场对话画上句号，避免开启新话题或显得冗长、刻意。

请像真人一样随意自然，**简洁是关键**。
不要输出多余内容（包括前后缀、冒号、引号、括号、表情包、at或@等）。

请直接输出最终的告别消息内容，不需要任何额外格式。"""

        return prompt

    def build_action_planning_prompt(
        self,
        chat_history: str,
        goals: list[ConversationGoal] | None = None,
        last_action: str = "",
        last_action_result: str = "",
        time_since_last_message: float = 0.0,
        is_follow_up: bool = False,
    ) -> str:
        """构建行动规划Prompt"""
        persona_text = self.get_persona_text()
        goals_str = self._format_goals(goals)

        time_info = ""
        if time_since_last_message > 0:
            if time_since_last_message < 60:
                time_info = f"提示：你上一条成功发送的消息是在 {time_since_last_message:.1f} 秒前。\n"
            else:
                minutes = time_since_last_message / 60
                time_info = f"提示：你上一条成功发送的消息是在 {minutes:.1f} 分钟前。\n"

        last_action_context = ""
        if last_action:
            last_action_context = f"【上一次行动的详细情况和结果】\n上次行动: {last_action}\n结果: {last_action_result}\n"

        if is_follow_up:
            action_list = """fetch_knowledge: 需要调取知识或记忆，当需要专业知识或特定信息时选择
wait: 暂时不说话，留给对方回复空间，等待对方回复
send_new_message: 发送一条新消息继续对话，允许适当的追问、补充、深入话题
rethink_goal: 思考一个对话目标，当你觉得目前对话需要目标，或当前目标不再适用
end_conversation: 结束对话，当你觉得对话告一段落时可以选择"""
        else:
            action_list = """direct_reply: 直接回复对方
fetch_knowledge: 需要调取知识或记忆，当需要专业知识或特定信息时选择
listening: 倾听对方发言，当你认为对方话还没说完，发言明显未结束时选择
wait: 暂时不说话，留给对方回复空间
rethink_goal: 思考一个对话目标，当你觉得目前对话需要目标，或当前目标不再适用
end_conversation: 结束对话，当你觉得对话告一段落时可以选择"""

        prompt = f"""{persona_text}。现在你在参与一场聊天，请根据以下信息审慎且灵活地决策下一步行动：

【当前对话目标】
{goals_str}

【最近行动历史概要】
{last_action_context}
{time_info}
【最近的对话记录】
{chat_history}

------
可选行动类型以及解释：
{action_list}

请以JSON格式输出你的决策：
{{
    "action": "选择的行动类型 (必须是上面列表中的一个)",
    "reason": "选择该行动的详细原因 (必须有解释你是如何根据对话记录和自身人设做出合理判断的)"
}}

注意：请严格按照JSON格式输出，不要包含任何其他内容。"""

        return prompt

    def _format_goals(self, goals: list[ConversationGoal] | None) -> str:
        """格式化目标列表"""
        if not goals:
            return "- 目前没有明确对话目标，请考虑设定一个。"

        lines = []
        for g in goals:
            status = " (已完成)" if g.achieved else ""
            lines.append(f"- 目标：{g.goal}{status}\n  原因：{g.reasoning}")
        return "\n".join(lines)

    def _build_knowledge_section(self, knowledge: str) -> str:
        """构建知识部分"""
        if not knowledge:
            return ""
        return f"【已获取的相关知识】\n{knowledge}\n"

    def _build_memory_section(self, memory: str) -> str:
        """构建记忆部分"""
        if not memory:
            return ""
        return f"【相关记忆】\n{memory}\n"

    def _build_expression_section(self, expression: str) -> str:
        """构建表达习惯部分"""
        if not expression:
            return ""
        return f"【表达习惯】\n{expression}\n"

    def _build_jargon_section(self, jargon: str) -> str:
        """构建黑话部分"""
        if not jargon:
            return ""
        return f"【黑话解释】\n{jargon}\n"

    def _get_emotion_prompt(self) -> str:
        """获取情感提示"""
        emotion_prompts = {
            EmotionType.NEUTRAL: "",
            EmotionType.HAPPY: "你现在心情不错，回复可以稍微活泼一点。",
            EmotionType.SAD: "你现在有点低落，回复可以稍微沉稳一点。",
            EmotionType.ANGRY: "你现在有点不高兴，回复可以稍微直接一点。",
            EmotionType.SURPRISED: "你现在有点惊讶，回复可以表达出惊讶。",
            EmotionType.CURIOUS: "你现在很好奇，回复可以带有好奇心。",
            EmotionType.THOUGHTFUL: "你在思考中，回复可以稍微深沉一点。",
            EmotionType.PLAYFUL: "你现在有点调皮，回复可以稍微俏皮一点。",
            EmotionType.CARING: "你很关心对方，回复可以表达出关心。",
            EmotionType.SHY: "你现在有点害羞，回复可以稍微含蓄一点。",
        }
        return emotion_prompts.get(self._emotion_state.emotion_type, "")

    def get_status(self) -> dict[str, Any]:
        """获取状态"""
        return {
            "bot_name": self.bot_name,
            "current_personality": self._current_state.name if self._current_state else "未设置",
            "emotion": self._emotion_state.emotion_type.value,
            "emotion_intensity": self._emotion_state.intensity,
        }


humanized_prompt_builder = HumanizedPromptBuilder()
