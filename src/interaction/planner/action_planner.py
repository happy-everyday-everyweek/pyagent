"""
PyAgent 聊天Agent核心 - 动作规划器

参考MaiBot的ActionPlanner设计，使用LLM规划动作。
"""

import json
import re
import time
from datetime import datetime
from typing import Any

from .action_manager import ActionManager
from .action_modifier import ActionModifier
from .types import ActionInfo, ActionPlannerInfo


class ActionPlanner:
    """动作规划器"""

    def __init__(self, chat_id: str, action_manager: ActionManager, llm_client: Any | None = None):
        self.chat_id = chat_id
        self.log_prefix = f"[{chat_id}]"
        self.action_manager = action_manager
        self.action_modifier = ActionModifier(action_manager, chat_id)
        self.llm_client = llm_client

        self.last_obs_time_mark = 0.0
        self.plan_log: list[tuple[str, float, Any]] = []

        self.bot_name = "Assistant"
        self.bot_alias_names: list[str] = []
        self.plan_style = "根据聊天内容自然地选择合适的动作"

    async def plan(
        self,
        available_actions: dict[str, ActionInfo],
        loop_start_time: float = 0.0,
        force_reply_message: Any | None = None,
        chat_content: str = "",
        message_id_list: list[tuple[str, Any]] | None = None
    ) -> list[ActionPlannerInfo]:
        """规划动作"""
        modified_actions = await self.action_modifier.modify_actions()

        prompt = await self._build_planner_prompt(
            available_actions=modified_actions,
            chat_content=chat_content,
            message_id_list=message_id_list or []
        )

        reasoning, actions = await self._execute_planner_llm(prompt, modified_actions)

        if force_reply_message:
            actions = self._ensure_force_reply(actions, force_reply_message)

        self._add_plan_log(reasoning, actions)

        return actions

    async def _build_planner_prompt(
        self,
        available_actions: dict[str, ActionInfo],
        chat_content: str,
        message_id_list: list[tuple[str, Any]]
    ) -> str:
        """构建规划器提示词"""
        time_block = f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        name_block = f"你的名字是{self.bot_name}"
        if self.bot_alias_names:
            name_block += f"，也有人叫你{','.join(self.bot_alias_names)}"
        name_block += "，请注意哪些是你自己的发言。"

        chat_context_description = "你现在正在一个群聊中"

        action_options_text = self._build_action_options_text(available_actions)

        actions_before_now_block = self._get_plan_log_str()

        moderation_prompt = "请不要输出违法违规内容，不要输出色情，暴力，政治相关内容。"

        prompt = f"""{time_block}
{name_block}
{chat_context_description}，以下是具体的聊天内容
**聊天内容**
{chat_content}

**可选的action**
reply
动作描述：
1.你可以选择呼叫了你的名字，但是你没有做出回应的消息进行回复
2.你可以自然的顺着正在进行的聊天内容进行回复或自然的提出一个问题
3.最好一次对一个话题进行回复，免得啰嗦或者回复内容太乱。
4.不要选择回复你自己发送的消息
5.不要单独对表情包进行回复
{{"action":"reply", "target_message_id":"消息id(m+数字)"}}

no_reply
动作描述：
保持沉默，不回复直到有新消息
控制聊天频率，不要太过频繁的发言
{{"action":"no_reply"}}

{action_options_text}

**你之前的action执行和思考记录**
{actions_before_now_block}

请选择**可选的**且符合使用条件的action，并说明触发action的消息id(消息id格式:m+数字)
先输出你的简短的选择思考理由，再输出你选择的action，理由不要分点，精简。
**动作选择要求**
请你根据聊天内容,用户的最新消息和以下标准选择合适的动作:
{self.plan_style}
{moderation_prompt}

target_message_id为必填，表示触发消息的id
请选择所有符合使用要求的action，每个动作最多选择一次，但是可以选择多个动作；
动作用json格式输出，用```json包裹:
**示例**
// 理由文本（简短）
```json
{{"action":"动作名", "target_message_id":"m123", .....}}
{{"action":"动作名", "target_message_id":"m456", .....}}
```"""

        return prompt

    def _build_action_options_text(self, available_actions: dict[str, ActionInfo]) -> str:
        """构建动作选项文本"""
        if not available_actions:
            return ""

        action_options_block = ""
        for action_name, action_info in available_actions.items():
            param_text = ""
            if action_info.parameters:
                param_text = "\n"
                for param_name, param_description in action_info.parameters.items():
                    param_text += f'    "{param_name}":"{param_description}"\n'
                param_text = param_text.rstrip("\n")

            require_text = ""
            for require_item in action_info.requirements:
                require_text += f"- {require_item}\n"
            require_text = require_text.rstrip("\n")

            parallel_text = ""
            if not action_info.parallel_action:
                parallel_text = "(当选择这个动作时，请不要选择其他动作)"

            action_options_block += f"""
{action_name}
动作描述：{action_info.description}
使用条件{parallel_text}：
{require_text}
{{"action":"{action_name}",{param_text}, "target_message_id":"消息id(m+数字)"}}
"""

        return action_options_block

    async def _execute_planner_llm(
        self,
        prompt: str,
        available_actions: dict[str, ActionInfo]
    ) -> tuple[str, list[ActionPlannerInfo]]:
        """执行规划器LLM"""
        if not self.llm_client:
            return "LLM客户端未配置", [ActionPlannerInfo(
                action_type="no_reply",
                reasoning="LLM客户端未配置",
                available_actions=available_actions
            )]

        try:
            from src.llm import Message
            messages = [Message(role="user", content=prompt)]
            response = await self.llm_client.generate(messages=messages)
            content = response.content
        except Exception as e:
            return f"LLM调用失败: {e}", [ActionPlannerInfo(
                action_type="no_reply",
                reasoning=f"LLM调用失败: {e}",
                available_actions=available_actions
            )]

        json_objects, reasoning = self._extract_json_from_markdown(content)

        actions: list[ActionPlannerInfo] = []
        for json_obj in json_objects:
            action = self._parse_single_action(json_obj, reasoning, available_actions)
            actions.append(action)

        if not actions:
            actions = [ActionPlannerInfo(
                action_type="no_reply",
                reasoning="LLM没有返回可用动作",
                available_actions=available_actions
            )]

        return reasoning, actions

    def _extract_json_from_markdown(self, content: str) -> tuple[list[dict], str]:
        """从Markdown格式的内容中提取JSON对象和推理内容"""
        json_objects = []
        reasoning_content = ""

        json_pattern = r"```json\s*(.*?)\s*```"
        markdown_matches = re.findall(json_pattern, content, re.DOTALL)

        first_json_pos = len(content)
        if markdown_matches:
            first_json_pos = content.find("```json")
            if first_json_pos > 0:
                reasoning_content = content[:first_json_pos].strip()
                reasoning_content = re.sub(r"^//\s*", "", reasoning_content, flags=re.MULTILINE)
                reasoning_content = reasoning_content.strip()

        for match in markdown_matches:
            try:
                json_str = re.sub(r"//.*?\n", "\n", match)
                json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)
                if json_str := json_str.strip():
                    lines = [line.strip() for line in json_str.split("\n") if line.strip()]
                    for line in lines:
                        try:
                            json_obj = json.loads(line)
                            if isinstance(json_obj, dict) and json_obj:
                                json_objects.append(json_obj)
                            elif isinstance(json_obj, list):
                                for item in json_obj:
                                    if isinstance(item, dict) and item:
                                        json_objects.append(item)
                        except json.JSONDecodeError:
                            pass

                    if not json_objects:
                        json_obj = json.loads(json_str)
                        if isinstance(json_obj, dict) and json_obj:
                            json_objects.append(json_obj)
                        elif isinstance(json_obj, list):
                            for item in json_obj:
                                if isinstance(item, dict) and item:
                                    json_objects.append(item)
            except Exception:
                continue

        return json_objects, reasoning_content

    def _parse_single_action(
        self,
        json_obj: dict,
        reasoning: str,
        available_actions: dict[str, ActionInfo]
    ) -> ActionPlannerInfo:
        """解析单个动作"""
        action_type = json_obj.get("action", "no_reply")
        action_reasoning = reasoning or "未提供原因"
        action_data = {k: v for k, v in json_obj.items() if k != "action"}

        if action_type not in ["no_reply", "reply"] and action_type not in available_actions:
            action_type = "no_reply"
            action_reasoning = f"未知的动作类型: {json_obj.get('action')}"

        return ActionPlannerInfo(
            action_type=action_type,
            reasoning=action_reasoning,
            action_data=action_data,
            action_message=None,
            available_actions=available_actions,
            action_reasoning=reasoning
        )

    def _ensure_force_reply(
        self,
        actions: list[ActionPlannerInfo],
        force_reply_message: Any
    ) -> list[ActionPlannerInfo]:
        """确保强制回复"""
        has_reply = any(a.action_type == "reply" for a in actions)

        if not has_reply:
            actions = [a for a in actions if a.action_type != "no_reply"]
            actions.insert(0, ActionPlannerInfo(
                action_type="reply",
                reasoning="用户提及了我，必须回复",
                action_data={},
                action_message=force_reply_message,
                available_actions=actions[0].available_actions if actions else {}
            ))

        return actions

    def _add_plan_log(self, reasoning: str, actions: list[ActionPlannerInfo]) -> None:
        """添加规划日志"""
        self.plan_log.append((reasoning, time.time(), actions))
        if len(self.plan_log) > 20:
            self.plan_log.pop(0)

    def _get_plan_log_str(self, max_records: int = 2) -> str:
        """获取规划日志字符串"""
        if not self.plan_log:
            return "无"

        log_str = ""
        for reasoning, timestamp, content in self.plan_log[-max_records:]:
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            if isinstance(content, list):
                action_names = [a.action_type for a in content]
                log_str += f"{time_str}: {reasoning} | 选择了: {', '.join(action_names)}\n"
            else:
                log_str += f"{time_str}: {content}\n"

        return log_str.strip()
