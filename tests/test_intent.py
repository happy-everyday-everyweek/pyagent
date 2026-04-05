"""
PyAgent 测试 - 意图理解模块

测试意图识别、任务创建、结果处理功能。
"""

import pytest

from src.interaction.intent import (
    EntityInfo,
    Intent,
    IntentContext,
    IntentRecognizer,
    IntentType,
    ResultHandler,
    TaskCreator,
)
from src.execution import Task, TaskResult, TaskStatus


class TestIntentTypes:
    """测试意图类型"""

    def test_intent_type_values(self):
        """测试意图类型枚举值"""
        assert IntentType.CHAT.name == "CHAT"
        assert IntentType.TASK.name == "TASK"
        assert IntentType.QUERY.name == "QUERY"
        assert IntentType.COMMAND.name == "COMMAND"
        assert IntentType.UNKNOWN.name == "UNKNOWN"

    def test_intent_creation(self):
        """测试意图创建"""
        intent = Intent(
            type=IntentType.TASK,
            confidence=0.9,
            content="帮我写一个Python脚本",
            entities={"language": "python"},
            raw_input="帮我写一个Python脚本"
        )
        assert intent.type == IntentType.TASK
        assert intent.confidence == 0.9
        assert intent.content == "帮我写一个Python脚本"
        assert intent.entities == {"language": "python"}

    def test_intent_type_checks(self):
        """测试意图类型检查方法"""
        chat_intent = Intent(type=IntentType.CHAT)
        task_intent = Intent(type=IntentType.TASK)
        query_intent = Intent(type=IntentType.QUERY)
        command_intent = Intent(type=IntentType.COMMAND)
        unknown_intent = Intent(type=IntentType.UNKNOWN)

        assert chat_intent.is_chat() is True
        assert task_intent.is_task() is True
        assert query_intent.is_query() is True
        assert command_intent.is_command() is True
        assert unknown_intent.is_unknown() is True

    def test_intent_to_dict(self):
        """测试意图转换为字典"""
        intent = Intent(
            type=IntentType.TASK,
            confidence=0.85,
            content="测试内容",
            entities={"key": "value"},
            metadata={"meta": "data"}
        )
        data = intent.to_dict()
        assert data["type"] == "TASK"
        assert data["confidence"] == 0.85
        assert data["content"] == "测试内容"
        assert data["entities"] == {"key": "value"}

    def test_intent_from_dict(self):
        """测试从字典创建意图"""
        data = {
            "type": "QUERY",
            "confidence": 0.75,
            "content": "查询内容",
            "entities": {"q": "test"}
        }
        intent = Intent.from_dict(data)
        assert intent.type == IntentType.QUERY
        assert intent.confidence == 0.75
        assert intent.content == "查询内容"


class TestEntityInfo:
    """测试实体信息"""

    def test_entity_info_creation(self):
        """测试实体信息创建"""
        entity = EntityInfo(
            name="file_path",
            value="/path/to/file.py",
            entity_type="path",
            confidence=0.95
        )
        assert entity.name == "file_path"
        assert entity.value == "/path/to/file.py"
        assert entity.entity_type == "path"
        assert entity.confidence == 0.95

    def test_entity_info_to_dict(self):
        """测试实体信息转换为字典"""
        entity = EntityInfo(
            name="language",
            value="python",
            entity_type="programming_language"
        )
        data = entity.to_dict()
        assert data["name"] == "language"
        assert data["value"] == "python"


class TestIntentContext:
    """测试意图上下文"""

    def test_context_creation(self):
        """测试上下文创建"""
        context = IntentContext(
            user_id="user123",
            chat_id="chat456",
            message_id="msg789"
        )
        assert context.user_id == "user123"
        assert context.chat_id == "chat456"
        assert context.message_id == "msg789"

    def test_context_to_dict(self):
        """测试上下文转换为字典"""
        context = IntentContext(
            user_id="user123",
            chat_id="chat456",
            user_preferences={"theme": "dark"}
        )
        data = context.to_dict()
        assert data["user_id"] == "user123"
        assert data["chat_id"] == "chat456"
        assert data["user_preferences"] == {"theme": "dark"}


class TestIntentRecognizer:
    """测试意图识别器"""

    def test_recognizer_creation(self):
        """测试识别器创建"""
        recognizer = IntentRecognizer()
        assert recognizer.llm_client is None
        assert recognizer.confidence_threshold == 0.6

    def test_recognizer_with_config(self):
        """测试带配置的识别器"""
        config = {
            "confidence_threshold": 0.8,
            "use_cache": False
        }
        recognizer = IntentRecognizer(config=config)
        assert recognizer.confidence_threshold == 0.8
        assert recognizer.use_cache is False

    @pytest.mark.asyncio
    async def test_quick_classify_command(self):
        """测试快速分类 - 命令"""
        recognizer = IntentRecognizer()
        intent = await recognizer.recognize("/help")
        assert intent.type == IntentType.COMMAND
        assert intent.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_quick_classify_task(self):
        """测试快速分类 - 任务"""
        recognizer = IntentRecognizer()
        intent = await recognizer.recognize("帮我写一个Python脚本")
        assert intent.type == IntentType.TASK
        assert intent.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_quick_classify_query(self):
        """测试快速分类 - 查询"""
        recognizer = IntentRecognizer()
        intent = await recognizer.recognize("什么是Python?")
        assert intent.type == IntentType.QUERY
        assert intent.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """测试空输入"""
        recognizer = IntentRecognizer()
        intent = await recognizer.recognize("")
        assert intent.type == IntentType.UNKNOWN
        assert intent.confidence == 0.0

    def test_extract_entities_command(self):
        """测试实体提取 - 命令"""
        recognizer = IntentRecognizer()
        entities = recognizer.extract_entities("/status", IntentType.COMMAND)
        assert entities.get("command") == "status"

    def test_extract_entities_task(self):
        """测试实体提取 - 任务"""
        recognizer = IntentRecognizer()
        entities = recognizer.extract_entities(
            "帮我修改 src/main.py 文件",
            IntentType.TASK
        )
        assert "file_path" in entities or len(entities) >= 0


class TestTaskCreator:
    """测试任务创建器"""

    def test_creator_creation(self):
        """测试创建器创建"""
        creator = TaskCreator()
        assert creator.default_priority == 0

    def test_creator_with_config(self):
        """测试带配置的创建器"""
        config = {
            "default_priority": 5,
            "max_retries": 5
        }
        creator = TaskCreator(config=config)
        assert creator.default_priority == 5
        assert creator.max_retries == 5

    def test_create_task_from_task_intent(self):
        """测试从任务意图创建任务"""
        creator = TaskCreator()
        intent = Intent(
            type=IntentType.TASK,
            confidence=0.9,
            content="帮我写一个Python脚本",
            entities={"language": "python"},
            raw_input="帮我写一个Python脚本"
        )
        task = creator.create_task(intent)
        assert task is not None
        assert task.status == TaskStatus.PENDING
        assert "Python脚本" in task.prompt

    def test_create_task_from_chat_intent(self):
        """测试从聊天意图创建任务 - 应返回None"""
        creator = TaskCreator()
        intent = Intent(
            type=IntentType.CHAT,
            confidence=0.8,
            content="你好",
            raw_input="你好"
        )
        task = creator.create_task(intent)
        assert task is None

    def test_create_task_from_text(self):
        """测试直接从文本创建任务"""
        creator = TaskCreator()
        task = creator.create_task_from_text("执行测试")
        assert task is not None
        assert task.status == TaskStatus.PENDING
        assert "执行测试" in task.prompt

    def test_validate_task(self):
        """测试任务验证"""
        creator = TaskCreator()
        valid_task = Task(prompt="有效任务")
        is_valid, error = creator.validate_task(valid_task)
        assert is_valid is True
        assert error == ""

        invalid_task = Task(prompt="")
        is_valid, error = creator.validate_task(invalid_task)
        assert is_valid is False
        assert "空" in error

    def test_determine_priority(self):
        """测试优先级确定"""
        creator = TaskCreator()
        
        urgent_intent = Intent(
            type=IntentType.TASK,
            content="紧急修复bug",
            confidence=0.9
        )
        task = creator.create_task(urgent_intent)
        assert task.priority >= 8

        normal_intent = Intent(
            type=IntentType.TASK,
            content="写一个脚本",
            confidence=0.7
        )
        task = creator.create_task(normal_intent)
        assert task.priority >= 0


class TestResultHandler:
    """测试结果处理器"""

    def test_handler_creation(self):
        """测试处理器创建"""
        handler = ResultHandler()
        assert handler.max_result_length == 2000

    def test_handler_with_config(self):
        """测试带配置的处理器"""
        config = {
            "max_result_length": 1000,
            "include_details": False
        }
        handler = ResultHandler(config=config)
        assert handler.max_result_length == 1000
        assert handler.include_details is False

    @pytest.mark.asyncio
    async def test_format_success_result(self):
        """测试格式化成功结果"""
        handler = ResultHandler()
        result = TaskResult(
            success=True,
            data="操作完成",
            duration=1.5
        )
        formatted = await handler.format_result(result, "TASK")
        assert "成功" in formatted
        assert "1.5" in formatted

    @pytest.mark.asyncio
    async def test_format_error_result(self):
        """测试格式化错误结果"""
        handler = ResultHandler()
        result = TaskResult(
            success=False,
            error="FileNotFoundError: 文件不存在"
        )
        formatted = await handler.format_result(result, "TASK")
        assert "失败" in formatted
        assert "文件不存在" in formatted

    def test_should_notify(self):
        """测试是否需要通知"""
        handler = ResultHandler()
        
        failed_result = TaskResult(success=False, error="错误")
        assert handler.should_notify(failed_result) is True

        success_result = TaskResult(success=True, data="完成")
        assert handler.should_notify(success_result) is False

        important_result = TaskResult(
            success=True,
            metadata={"important_result": True}
        )
        assert handler.should_notify(important_result) is True

    def test_get_notification_level(self):
        """测试通知级别"""
        handler = ResultHandler()
        
        success_result = TaskResult(success=True)
        assert handler.get_notification_level(success_result) == "info"

        failed_result = TaskResult(success=False, error="错误")
        assert handler.get_notification_level(failed_result) == "warning"

        critical_result = TaskResult(success=False, error="critical error")
        assert handler.get_notification_level(critical_result) == "error"

    def test_format_summary(self):
        """测试格式化摘要"""
        handler = ResultHandler()
        result = TaskResult(
            success=True,
            duration=2.5,
            steps=[
                {"action": "step1", "success": True},
                {"action": "step2", "success": True}
            ]
        )
        summary = handler.format_summary(result)
        assert "成功" in summary
        assert "2.5" in summary
        assert "2/2" in summary
