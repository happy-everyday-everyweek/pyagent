"""
PyAgent 聊天Agent核心 - 回复生成器基类

参考MaiBot的Replyer设计，定义回复生成器的基类。
"""

from abc import ABC, abstractmethod
from typing import Any

from .types import ReplyConfig, ReplyContent, ReplySet


class BaseReplyer(ABC):
    """回复生成器基类"""

    def __init__(
        self,
        chat_id: str,
        llm_client: Any | None = None,
        config: ReplyConfig | None = None
    ):
        self.chat_id = chat_id
        self.llm_client = llm_client
        self.config = config or ReplyConfig()
        self.log_prefix = f"[{chat_id}]"

    @abstractmethod
    async def generate_reply(
        self,
        chat_content: str,
        reply_reason: str = "",
        target_message: Any | None = None,
        available_actions: dict[str, Any] | None = None,
        chosen_actions: list[Any] | None = None,
        **kwargs
    ) -> tuple[bool, ReplySet | None]:
        """生成回复"""

    async def _build_reply_prompt(
        self,
        chat_content: str,
        reply_reason: str = "",
        target_message: Any | None = None,
        **kwargs
    ) -> str:
        """构建回复提示词"""
        prompt = f"""请根据以下聊天内容生成一个自然、友好的回复。

聊天内容：
{chat_content}

回复原因：{reply_reason}

要求：
1. 回复要自然、友好，贴近人类习惯
2. 回复要简洁，不要过于啰嗦
3. 回复要与聊天内容相关
4. 不要输出违法违规内容

请直接输出回复内容，不要输出其他内容。"""

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        if not self.llm_client:
            return "抱歉，我现在无法回复。"

        try:
            from src.llm import Message
            messages = [Message(role="user", content=prompt)]
            response = await self.llm_client.generate(
                messages=messages,
                temperature=self.config.temperature
            )
            return response.content
        except Exception as e:
            return f"抱歉，生成回复时出错：{e}"

    def _parse_reply_content(self, content: str) -> ReplySet:
        """解析回复内容"""
        reply_content = content.strip()
        if not reply_content:
            reply_content = "..."

        return ReplySet(
            reply_data=[ReplyContent(content=reply_content)],
            selected_expressions=[],
            quote_message=False
        )
