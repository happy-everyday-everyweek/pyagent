"""
PyAgent 聊天Agent核心 - 私聊回复生成器

参考MaiBot的PrivateReplyer设计，实现私聊场景的回复生成。
"""

from typing import Any

from .base_generator import BaseReplyer
from .types import ReplyConfig, ReplyContent, ReplySet


class PrivateReplyer(BaseReplyer):
    """私聊回复生成器"""

    def __init__(
        self,
        chat_id: str,
        llm_client: Any | None = None,
        config: ReplyConfig | None = None
    ):
        super().__init__(chat_id, llm_client, config)
        self.is_group = False

    async def generate_reply(
        self,
        chat_content: str,
        reply_reason: str = "",
        target_message: Any | None = None,
        available_actions: dict[str, Any] | None = None,
        chosen_actions: list[Any] | None = None,
        **kwargs
    ) -> tuple[bool, ReplySet | None]:
        """生成私聊回复"""
        prompt = await self._build_private_reply_prompt(
            chat_content=chat_content,
            reply_reason=reply_reason,
            target_message=target_message,
            available_actions=available_actions,
            chosen_actions=chosen_actions,
            **kwargs
        )

        content = await self._call_llm(prompt)

        reply_set = self._parse_reply_content(content)

        return True, reply_set

    async def _build_private_reply_prompt(
        self,
        chat_content: str,
        reply_reason: str = "",
        target_message: Any | None = None,
        available_actions: dict[str, Any] | None = None,
        chosen_actions: list[Any] | None = None,
        **kwargs
    ) -> str:
        """构建私聊回复提示词"""
        think_level = kwargs.get("think_level", 0)
        unknown_words = kwargs.get("unknown_words", [])

        prompt = f"""你正在一个私聊中，请根据以下聊天内容生成一个自然、友好的回复。

聊天内容：
{chat_content}

回复原因：{reply_reason}
"""

        if think_level > 0:
            prompt += """
请仔细思考后再回复，可以回忆之前的相关内容。
"""

        if unknown_words:
            prompt += f"""
请注意以下词语可能是不常用的表达或黑话：{', '.join(unknown_words)}
"""

        prompt += """
要求：
1. 回复要自然、友好，贴近人类习惯
2. 回复可以稍微详细一些，因为这是私聊
3. 回复要与聊天内容相关
4. 不要输出违法违规内容

请直接输出回复内容，不要输出其他内容。"""

        return prompt

    def _parse_reply_content(self, content: str) -> ReplySet:
        """解析回复内容"""
        reply_content = content.strip()
        if not reply_content:
            reply_content = "..."

        max_length = self.config.max_length * 2
        if len(reply_content) > max_length:
            reply_content = reply_content[:max_length - 3] + "..."

        return ReplySet(
            reply_data=[ReplyContent(content=reply_content)],
            selected_expressions=[],
            quote_message=False
        )
