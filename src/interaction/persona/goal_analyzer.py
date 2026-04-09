"""
PyAgent 拟人化系统 - 对话目标分析器

分析对话并生成多个可能的对话目标。
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationGoal:
    """对话目标"""
    goal: str
    reasoning: str
    priority: int = 1
    achieved: bool = False
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "reasoning": self.reasoning,
            "priority": self.priority,
            "achieved": self.achieved,
            "created_at": self.created_at
        }


class GoalAnalyzer:
    """对话目标分析器"""

    MAX_GOALS = 3

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client

    async def analyze(
        self,
        chat_history: str,
        current_goals: list[ConversationGoal] | None = None,
        context: dict[str, Any] | None = None
    ) -> list[ConversationGoal]:
        """
        分析对话并生成目标
        
        Args:
            chat_history: 聊天历史
            current_goals: 当前目标
            context: 上下文信息
            
        Returns:
            list[ConversationGoal]: 目标列表
        """
        if not self.llm_client:
            return self._quick_analyze(chat_history, current_goals)

        try:
            return await self._llm_analyze(chat_history, current_goals, context)
        except Exception as e:
            logger.error(f"LLM goal analysis failed: {e}")
            return self._quick_analyze(chat_history, current_goals)

    def _quick_analyze(
        self,
        chat_history: str,
        current_goals: list[ConversationGoal] | None = None
    ) -> list[ConversationGoal]:
        """快速分析（基于规则）"""
        if current_goals and len(current_goals) >= self.MAX_GOALS:
            return current_goals[:self.MAX_GOALS]

        goals = list(current_goals) if current_goals else []

        if "帮我" in chat_history or "请帮我" in chat_history:
            goals.append(ConversationGoal(
                goal="帮助用户完成任务",
                reasoning="用户请求帮助",
                priority=1
            ))

        if "?" in chat_history or "？" in chat_history:
            goals.append(ConversationGoal(
                goal="回答用户问题",
                reasoning="用户提出了问题",
                priority=1
            ))

        if "谢谢" in chat_history or "感谢" in chat_history:
            goals.append(ConversationGoal(
                goal="礼貌回应感谢",
                reasoning="用户表示感谢",
                priority=2
            ))

        return goals[:self.MAX_GOALS]

    async def _llm_analyze(
        self,
        chat_history: str,
        current_goals: list[ConversationGoal] | None = None,
        context: dict[str, Any] | None = None
    ) -> list[ConversationGoal]:
        """LLM 分析"""
        current_goals_str = ""
        if current_goals:
            current_goals_str = "当前目标：\n"
            for g in current_goals:
                status = " (已完成)" if g.achieved else ""
                current_goals_str += f"- {g.goal}{status}\n"

        prompt = f"""请分析以下对话，生成最多{self.MAX_GOALS}个对话目标。

对话历史：
{chat_history}

{current_goals_str}

请以JSON格式输出目标列表：
```json
[
    {{
        "goal": "目标描述",
        "reasoning": "为什么这是目标",
        "priority": 1-3的优先级
    }}
]
```

注意：
1. 目标应该具体、可执行
2. 每个目标需要解释原因
3. 优先级1最高，3最低
4. 只输出JSON，不要其他内容"""

        response = await self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.get("content", "")
        goals_data = self._parse_json(content)

        if not goals_data:
            return self._quick_analyze(chat_history, current_goals)

        goals = []
        for item in goals_data[:self.MAX_GOALS]:
            goals.append(ConversationGoal(
                goal=item.get("goal", ""),
                reasoning=item.get("reasoning", ""),
                priority=item.get("priority", 1)
            ))

        return goals

    def _parse_json(self, content: str) -> list[dict] | None:
        """解析JSON"""
        try:
            json_match = content
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_match = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                json_match = content[start:end].strip()

            return json.loads(json_match)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return None

    def deduplicate(
        self,
        goals: list[ConversationGoal],
        existing_goals: list[ConversationGoal] | None = None
    ) -> list[ConversationGoal]:
        """
        去重目标
        
        Args:
            goals: 新目标列表
            existing_goals: 已有目标列表
            
        Returns:
            list[ConversationGoal]: 去重后的目标列表
        """
        if not existing_goals:
            return goals

        existing_texts = {g.goal.lower() for g in existing_goals}
        unique_goals = []

        for goal in goals:
            if goal.goal.lower() not in existing_texts:
                unique_goals.append(goal)
                existing_texts.add(goal.goal.lower())

        return unique_goals

    def merge_goals(
        self,
        current_goals: list[ConversationGoal],
        new_goals: list[ConversationGoal]
    ) -> list[ConversationGoal]:
        """
        合并目标
        
        Args:
            current_goals: 当前目标
            new_goals: 新目标
            
        Returns:
            list[ConversationGoal]: 合并后的目标列表
        """
        unique_new = self.deduplicate(new_goals, current_goals)
        merged = list(current_goals) + unique_new
        merged.sort(key=lambda g: g.priority)
        return merged[:self.MAX_GOALS]


goal_analyzer = GoalAnalyzer()
