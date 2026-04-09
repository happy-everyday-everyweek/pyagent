"""
PyAgent 交互模块 - 意图识别器

使用LLM识别用户输入的意图。
"""

import json
import re
import time
from typing import Any

from .intent_types import Intent, IntentContext, IntentType


class IntentRecognizer:
    """意图识别器"""

    def __init__(self, llm_client: Any | None = None, config: dict[str, Any] | None = None):
        self.llm_client = llm_client
        self.config = config or {}
        self.confidence_threshold = self.config.get("confidence_threshold", 0.6)
        self.use_cache = self.config.get("use_cache", True)
        self._cache: dict[str, tuple[Intent, float]] = {}
        self._cache_ttl = self.config.get("cache_ttl", 300)

    async def recognize(
        self,
        user_input: str,
        context: IntentContext | None = None
    ) -> Intent:
        """
        识别用户输入的意图
        
        Args:
            user_input: 用户输入文本
            context: 意图上下文
            
        Returns:
            Intent: 识别出的意图
        """
        if not user_input.strip():
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                content="",
                raw_input=user_input
            )

        cached_intent = self._get_cached_intent(user_input)
        if cached_intent:
            return cached_intent

        quick_intent = self._quick_classify(user_input)
        if quick_intent and quick_intent.confidence >= 0.9:
            self._cache_intent(user_input, quick_intent)
            return quick_intent

        if not self.llm_client:
            return quick_intent or Intent(
                type=IntentType.CHAT,
                confidence=0.5,
                content=user_input,
                raw_input=user_input
            )

        intent = await self._llm_classify(user_input, context)
        self._cache_intent(user_input, intent)
        return intent

    def _quick_classify(self, user_input: str) -> Intent | None:
        """
        快速分类 - 基于规则的初步分类
        
        Args:
            user_input: 用户输入
            
        Returns:
            Intent | None: 快速分类结果，如果无法确定则返回None
        """
        input_lower = user_input.lower().strip()

        open_file_patterns = [
            r"^[/#!]open\s+(.+)$",
            r"^打开(文件|文档)?\s*(.+)$",
            r"^打开我的(.+)$",
            r"^查看(.+)文件",
        ]
        for pattern in open_file_patterns:
            match = re.match(pattern, user_input)
            if match:
                file_name = match.group(match.lastindex) if match.lastindex else ""
                return Intent(
                    type=IntentType.OPEN_FILE,
                    confidence=0.9,
                    content=user_input,
                    entities={"file_name": file_name.strip()},
                    raw_input=user_input
                )

        open_app_patterns = {
            r"^[/#!]calendar$": ("calendar", "日历"),
            r"^[/#!]tasks?$": ("tasks", "任务"),
            r"^[/#!]email$": ("email", "邮件"),
            r"^[/#!]notes?$": ("notes", "笔记"),
            r"^[/#!]browser$": ("browser", "浏览器"),
            r"^[/#!]files?$": ("files", "文件"),
            r"^[/#!]word$": ("word", "Word文档"),
            r"^[/#!]ppt$": ("ppt", "PPT"),
            r"^[/#!]excel$": ("excel", "Excel"),
            r"^[/#!]settings?$": ("settings", "设置"),
            r"^[/#!]日历$": ("calendar", "日历"),
            r"^[/#!]任务$": ("tasks", "任务"),
            r"^[/#!]邮件$": ("email", "邮件"),
            r"^[/#!]笔记$": ("notes", "笔记"),
            r"^[/#!]浏览器$": ("browser", "浏览器"),
            r"^[/#!]文件$": ("files", "文件"),
            r"^[/#!]设置$": ("settings", "设置"),
            r"^打开(日历|任务|邮件|笔记|浏览器|文件|设置)$": None,
            r"^打开(Word|PPT|Excel)$": None,
        }
        for pattern, app_info in open_app_patterns.items():
            if re.match(pattern, input_lower):
                if app_info:
                    app_id, app_name = app_info
                else:
                    match = re.match(pattern, user_input)
                    app_name = match.group(1) if match else ""
                    app_id = app_name.lower()
                return Intent(
                    type=IntentType.OPEN_APP,
                    confidence=0.95,
                    content=user_input,
                    entities={"app_id": app_id, "app_name": app_name},
                    raw_input=user_input
                )

        create_event_patterns = [
            r"^[/#!]event\s+(.+)$",
            r"^创建?日程[:：]?\s*(.+)$",
            r"^添加日程[:：]?\s*(.+)$",
            r"^新建日程[:：]?\s*(.+)$",
            r"^(明天|后天|下周|周[一二三四五六日]).*?(开会|会议|约会|安排)",
            r"^提醒我.*?(开会|会议)",
        ]
        for pattern in create_event_patterns:
            match = re.match(pattern, user_input)
            if match:
                event_content = match.group(match.lastindex) if match.lastindex else user_input
                return Intent(
                    type=IntentType.CREATE_EVENT,
                    confidence=0.9,
                    content=user_input,
                    entities={"event_content": event_content.strip()},
                    raw_input=user_input
                )

        create_todo_patterns = [
            r"^[/#!]todo\s+(.+)$",
            r"^创建?待办[:：]?\s*(.+)$",
            r"^添加待办[:：]?\s*(.+)$",
            r"^新建待办[:：]?\s*(.+)$",
            r"^提醒我\s+(.+)$",
            r"^待办[:：]\s*(.+)$",
        ]
        for pattern in create_todo_patterns:
            match = re.match(pattern, user_input)
            if match:
                todo_content = match.group(match.lastindex) if match.lastindex else user_input
                return Intent(
                    type=IntentType.CREATE_TODO,
                    confidence=0.9,
                    content=user_input,
                    entities={"todo_content": todo_content.strip()},
                    raw_input=user_input
                )

        modify_settings_patterns = [
            r"^[/#!]settings?\s+(.+)$",
            r"^修改设置[:：]?\s*(.+)$",
            r"^更改设置[:：]?\s*(.+)$",
            r"^把(.+)改成(.+)$",
            r"^设置(.+)为(.+)$",
        ]
        for pattern in modify_settings_patterns:
            match = re.match(pattern, user_input)
            if match:
                return Intent(
                    type=IntentType.MODIFY_SETTINGS,
                    confidence=0.9,
                    content=user_input,
                    entities={"settings_input": user_input},
                    raw_input=user_input
                )

        command_patterns = [
            r"^[/#!]\w+",
            r"^(help|帮助|菜单|功能列表)$",
            r"^(clear|清空|重置)",
            r"^(status|状态|设置|config)",
        ]
        for pattern in command_patterns:
            if re.match(pattern, input_lower):
                return Intent(
                    type=IntentType.COMMAND,
                    confidence=0.95,
                    content=user_input,
                    entities={"command": input_lower.lstrip("/#!")},
                    raw_input=user_input
                )

        task_keywords = [
            "帮我", "请帮我", "帮我做", "帮我写", "帮我创建",
            "执行", "完成", "处理", "实现", "开发", "构建",
            "修复", "优化", "重构", "分析", "生成"
        ]
        for keyword in task_keywords:
            if keyword in input_lower:
                return Intent(
                    type=IntentType.TASK,
                    confidence=0.85,
                    content=user_input,
                    entities={"task_hint": keyword},
                    raw_input=user_input
                )

        query_patterns = [
            r"^(什么|什么是|什么是\w+)",
            r"^(怎么|如何|怎样)",
            r"^(为什么|为啥)",
            r"^(谁|哪里|哪个|哪些)",
            r"^(查询|搜索|查找|找一下)",
            r"\?$",
            r"吗[？?]?$",
        ]
        for pattern in query_patterns:
            if re.search(pattern, input_lower):
                return Intent(
                    type=IntentType.QUERY,
                    confidence=0.85,
                    content=user_input,
                    raw_input=user_input
                )

        return None

    async def _llm_classify(
        self,
        user_input: str,
        context: IntentContext | None = None
    ) -> Intent:
        """
        使用LLM进行意图分类
        
        Args:
            user_input: 用户输入
            context: 意图上下文
            
        Returns:
            Intent: 分类结果
        """
        prompt = self._build_classify_prompt(user_input, context)

        try:
            from src.llm import Message
            messages = [Message(role="user", content=prompt)]
            response = await self.llm_client.generate(messages=messages)
            content = response.content
        except Exception as e:
            return Intent(
                type=IntentType.CHAT,
                confidence=0.5,
                content=user_input,
                metadata={"error": str(e)},
                raw_input=user_input
            )

        intent = self._parse_llm_response(content, user_input)
        return intent

    def _build_classify_prompt(
        self,
        user_input: str,
        context: IntentContext | None = None
    ) -> str:
        """构建分类提示词"""
        context_info = ""
        if context and context.conversation_history:
            recent_history = context.conversation_history[-3:]
            history_text = "\n".join([
                f"{h.get('role', 'user')}: {h.get('content', '')}"
                for h in recent_history
            ])
            context_info = f"\n\n最近对话历史:\n{history_text}"

        prompt = f"""请分析以下用户输入的意图类型。

用户输入: {user_input}{context_info}

意图类型说明:
1. CHAT - 普通聊天、闲聊、问候、情感表达
2. TASK - 任务请求，需要执行具体操作（如写代码、创建文件、执行命令等）
3. QUERY - 信息查询，询问问题、搜索信息
4. COMMAND - 系统命令，如/help、/status等指令
5. OPEN_FILE - 打开文件，如"打开我的文档"、"/open 文件名"
6. OPEN_APP - 打开应用，如"打开日历"、"/calendar"
7. CREATE_EVENT - 创建日程，如"明天下午3点开会"、"/event 日程内容"
8. CREATE_TODO - 创建待办，如"提醒我交报告"、"/todo 待办内容"
9. MODIFY_SETTINGS - 修改设置，如"把模型改成GPT-4"、"/settings model GPT-4"
10. UNKNOWN - 无法识别的意图

请以JSON格式返回结果:
```json
{{
    "intent_type": "CHAT|TASK|QUERY|COMMAND|OPEN_FILE|OPEN_APP|CREATE_EVENT|CREATE_TODO|MODIFY_SETTINGS|UNKNOWN",
    "confidence": 0.0-1.0,
    "content": "用户的核心意图描述",
    "entities": {{
        "key": "提取的关键实体"
    }}
}}
```

只返回JSON，不要其他解释。"""

        return prompt

    def _parse_llm_response(self, response: str, user_input: str) -> Intent:
        """解析LLM响应"""
        try:
            json_pattern = r"```json\s*(.*?)\s*```"
            matches = re.findall(json_pattern, response, re.DOTALL)

            if matches:
                json_str = matches[0]
            else:
                json_str = response

            json_str = re.sub(r"//.*?\n", "\n", json_str)
            json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)

            data = json.loads(json_str.strip())

            intent_type_str = data.get("intent_type", "UNKNOWN").upper()
            intent_type = IntentType[intent_type_str] if intent_type_str in IntentType.__members__ else IntentType.UNKNOWN

            return Intent(
                type=intent_type,
                confidence=float(data.get("confidence", 0.5)),
                content=data.get("content", user_input),
                entities=data.get("entities", {}),
                raw_input=user_input
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return Intent(
                type=IntentType.CHAT,
                confidence=0.5,
                content=user_input,
                raw_input=user_input
            )

    def extract_entities(self, text: str, intent_type: IntentType) -> dict[str, Any]:
        """
        提取实体信息
        
        Args:
            text: 输入文本
            intent_type: 意图类型
            
        Returns:
            dict: 提取的实体
        """
        entities: dict[str, Any] = {}

        if intent_type == IntentType.COMMAND:
            match = re.match(r"^[/#!](\w+)", text.strip())
            if match:
                entities["command"] = match.group(1)

        elif intent_type == IntentType.TASK:
            task_patterns = {
                "file_path": r"([a-zA-Z]:\\[\w\\.-]+|/[\w/.-]+|\w+/\w+)",
                "language": r"(python|java|javascript|typescript|go|rust|cpp|c\+\+)",
                "action": r"(创建|修改|删除|读取|执行|运行|测试)"
            }
            for entity_name, pattern in task_patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    entities[entity_name] = matches[0] if len(matches) == 1 else matches

        elif intent_type == IntentType.QUERY:
            question_words = re.findall(r"(什么|怎么|如何|为什么|谁|哪里|哪个)", text)
            if question_words:
                entities["question_type"] = question_words[0]

        return entities

    def _get_cached_intent(self, user_input: str) -> Intent | None:
        """获取缓存的意图"""
        if not self.use_cache:
            return None

        cache_key = user_input.strip().lower()
        if cache_key in self._cache:
            intent, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return intent
            del self._cache[cache_key]

        return None

    def _cache_intent(self, user_input: str, intent: Intent) -> None:
        """缓存意图"""
        if not self.use_cache:
            return

        cache_key = user_input.strip().lower()
        self._cache[cache_key] = (intent, time.time())

        if len(self._cache) > 1000:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
