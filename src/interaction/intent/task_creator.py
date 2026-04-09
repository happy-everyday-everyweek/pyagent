"""
PyAgent 交互模块 - 任务创建器

根据意图创建执行任务。
"""

from typing import Any

from src.execution import Task, TaskStatus

from .intent_types import Intent


class TaskCreator:
    """任务创建器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.default_priority = self.config.get("default_priority", 0)
        self.max_retries = self.config.get("max_retries", 3)
        self.timeout = self.config.get("timeout", 300)

    def create_task(
        self,
        intent: Intent,
        context: dict[str, Any] | None = None
    ) -> Task | None:
        """
        根据意图创建任务
        
        Args:
            intent: 识别出的意图
            context: 执行上下文
            
        Returns:
            Task | None: 创建的任务，如果不是任务意图则返回None
        """
        if not intent.is_task():
            return None

        prompt = self._build_prompt(intent)
        task_context = self._build_context(intent, context)
        priority = self._determine_priority(intent)
        tags = self._extract_tags(intent)

        task = Task(
            prompt=prompt,
            context=task_context,
            status=TaskStatus.PENDING,
            priority=priority,
            tags=tags,
            metadata={
                "intent_type": intent.type.value,
                "confidence": intent.confidence,
                "entities": intent.entities,
                "raw_input": intent.raw_input
            }
        )

        return task

    def create_task_from_text(
        self,
        text: str,
        context: dict[str, Any] | None = None
    ) -> Task:
        """
        直接从文本创建任务
        
        Args:
            text: 任务描述文本
            context: 执行上下文
            
        Returns:
            Task: 创建的任务
        """
        prompt = self._enhance_prompt(text)
        task_context = context or {}

        task = Task(
            prompt=prompt,
            context=task_context,
            status=TaskStatus.PENDING,
            priority=self.default_priority,
            tags=["direct"],
            metadata={
                "source": "direct_input",
                "raw_input": text
            }
        )

        return task

    def _build_prompt(self, intent: Intent) -> str:
        """
        构建任务提示词
        
        Args:
            intent: 意图对象
            
        Returns:
            str: 构建的提示词
        """
        base_prompt = intent.content

        entities = intent.entities
        enhancements = []

        if "file_path" in entities:
            file_path = entities["file_path"]
            enhancements.append(f"目标文件: {file_path}")

        if "language" in entities:
            language = entities["language"]
            enhancements.append(f"编程语言: {language}")

        if "action" in entities:
            action = entities["action"]
            enhancements.append(f"操作类型: {action}")

        if enhancements:
            enhancement_text = "\n".join(enhancements)
            prompt = f"{base_prompt}\n\n任务详情:\n{enhancement_text}"
        else:
            prompt = base_prompt

        prompt = self._add_execution_guidelines(prompt)

        return prompt

    def _enhance_prompt(self, text: str) -> str:
        """增强提示词"""
        return self._add_execution_guidelines(text)

    def _add_execution_guidelines(self, prompt: str) -> str:
        """添加执行指导"""
        guidelines = """

执行要求:
1. 分析任务需求，制定执行计划
2. 按步骤执行，确保每一步都正确完成
3. 遇到问题时，尝试分析和解决
4. 完成后验证结果是否符合预期
5. 提供清晰的执行报告"""

        return prompt + guidelines

    def _build_context(
        self,
        intent: Intent,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        构建任务上下文
        
        Args:
            intent: 意图对象
            context: 原始上下文
            
        Returns:
            dict: 构建的上下文
        """
        task_context = context or {}

        task_context["intent_metadata"] = {
            "type": intent.type.name,
            "confidence": intent.confidence,
            "entities": intent.entities
        }

        if intent.metadata:
            task_context["intent_metadata"].update(intent.metadata)

        task_context.setdefault("config", {}).update({
            "max_retries": self.max_retries,
            "timeout": self.timeout
        })

        return task_context

    def _determine_priority(self, intent: Intent) -> int:
        """
        确定任务优先级
        
        Args:
            intent: 意图对象
            
        Returns:
            int: 优先级（0-10）
        """
        priority = self.default_priority

        urgent_keywords = ["紧急", "urgent", "立即", "马上", "asap"]
        for keyword in urgent_keywords:
            if keyword in intent.content.lower():
                priority = max(priority, 8)
                break

        important_keywords = ["重要", "important", "关键", "critical"]
        for keyword in important_keywords:
            if keyword in intent.content.lower():
                priority = max(priority, 6)
                break

        if intent.confidence >= 0.9:
            priority = max(priority, 5)
        elif intent.confidence < 0.7:
            priority = min(priority, 3)

        return min(priority, 10)

    def _extract_tags(self, intent: Intent) -> list[str]:
        """
        提取任务标签
        
        Args:
            intent: 意图对象
            
        Returns:
            list: 标签列表
        """
        tags = ["intent_task"]

        content_lower = intent.content.lower()

        tag_keywords = {
            "code": ["代码", "code", "编程", "写", "实现"],
            "file": ["文件", "file", "创建", "修改", "删除"],
            "analysis": ["分析", "analyze", "检查", "check"],
            "search": ["搜索", "search", "查找", "find"],
            "test": ["测试", "test", "验证", "verify"],
            "doc": ["文档", "doc", "readme", "说明"]
        }

        for tag, keywords in tag_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    tags.append(tag)
                    break

        if "language" in intent.entities:
            lang = intent.entities["language"]
            if isinstance(lang, str):
                tags.append(f"lang_{lang.lower()}")

        return list(set(tags))

    def validate_task(self, task: Task) -> tuple[bool, str]:
        """
        验证任务是否有效
        
        Args:
            task: 任务对象
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if not task.prompt or not task.prompt.strip():
            return False, "任务提示词不能为空"

        if len(task.prompt) > 10000:
            return False, "任务提示词过长"

        return True, ""
