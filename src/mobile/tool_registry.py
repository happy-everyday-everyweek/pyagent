"""
PyAgent 移动端模块 - 工具注册表

提供移动端工具的统一注册、管理和执行接口。
v0.8.0: 新增移动端工具注册支持

参考: Operit项目 ToolRegistration模块
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    SYSTEM = "system"
    SCREEN = "screen"
    NOTIFICATION = "notification"
    SMS = "sms"
    PACKAGE = "package"
    WORKFLOW = "workflow"
    MNN = "mnn"
    FILE = "file"
    NETWORK = "network"
    OTHER = "other"


class ToolState(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    DORMANT = "dormant"
    ERROR = "error"


@dataclass
class ToolParameter:
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None
    choices: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "choices": self.choices,
        }


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str = ""
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class ToolInfo:
    name: str
    description: str = ""
    category: ToolCategory = ToolCategory.OTHER
    parameters: list[ToolParameter] = field(default_factory=list)
    returns: str = ""
    examples: list[str] = field(default_factory=list)
    requires_root: bool = False
    requires_permission: list[str] = field(default_factory=list)
    state: ToolState = ToolState.IDLE
    call_count: int = 0
    last_call_time: float | None = None
    avg_execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [p.to_dict() for p in self.parameters],
            "returns": self.returns,
            "examples": self.examples,
            "requires_root": self.requires_root,
            "requires_permission": self.requires_permission,
            "state": self.state.value,
            "call_count": self.call_count,
            "last_call_time": self.last_call_time,
            "avg_execution_time_ms": self.avg_execution_time_ms,
        }


class MobileTool:
    def __init__(
        self,
        name: str,
        handler: Callable,
        info: ToolInfo | None = None,
        on_activate: Callable | None = None,
        on_dormant: Callable | None = None,
    ):
        self.name = name
        self._handler = handler
        self._info = info or ToolInfo(name=name)
        self._on_activate = on_activate
        self._on_dormant = on_dormant
        self._state = ToolState.IDLE
        self._lock = threading.Lock()
        self._total_execution_time = 0.0

    @property
    def info(self) -> ToolInfo:
        return self._info

    @property
    def state(self) -> ToolState:
        return self._state

    def activate(self) -> bool:
        with self._lock:
            if self._state == ToolState.ACTIVE:
                return True

            try:
                if self._on_activate:
                    if asyncio.iscoroutinefunction(self._on_activate):
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self._on_activate())
                        else:
                            loop.run_until_complete(self._on_activate())
                    else:
                        self._on_activate()

                self._state = ToolState.ACTIVE
                self._info.state = ToolState.ACTIVE
                logger.debug(f"Tool activated: {self.name}")
                return True

            except Exception as e:
                logger.error(f"Failed to activate tool {self.name}: {e}")
                self._state = ToolState.ERROR
                self._info.state = ToolState.ERROR
                return False

    def dormant(self) -> bool:
        with self._lock:
            if self._state == ToolState.DORMANT:
                return True

            try:
                if self._on_dormant:
                    if asyncio.iscoroutinefunction(self._on_dormant):
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self._on_dormant())
                        else:
                            loop.run_until_complete(self._on_dormant())
                    else:
                        self._on_dormant()

                self._state = ToolState.DORMANT
                self._info.state = ToolState.DORMANT
                logger.debug(f"Tool dormant: {self.name}")
                return True

            except Exception as e:
                logger.error(f"Failed to dormant tool {self.name}: {e}")
                self._state = ToolState.ERROR
                self._info.state = ToolState.ERROR
                return False

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        start_time = time.time()

        if self._state == ToolState.IDLE:
            self.activate()

        if self._state == ToolState.ERROR:
            return ToolResult(
                success=False,
                error=f"Tool is in error state: {self.name}",
            )

        try:
            self._state = ToolState.ACTIVE
            self._info.state = ToolState.ACTIVE

            if asyncio.iscoroutinefunction(self._handler):
                result = await self._handler(params)
            else:
                result = self._handler(params)

            execution_time = (time.time() - start_time) * 1000

            self._info.call_count += 1
            self._info.last_call_time = time.time()
            self._total_execution_time += execution_time
            self._info.avg_execution_time_ms = (
                self._total_execution_time / self._info.call_count
            )

            if isinstance(result, ToolResult):
                result.execution_time_ms = execution_time
                return result

            return ToolResult(
                success=True,
                data=result,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tool execution failed: {self.name}, error: {e}")

            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )


class MobileToolRegistry:
    _instance: Optional["MobileToolRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MobileToolRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._tools: dict[str, MobileTool] = {}
        self._categories: dict[ToolCategory, list[str]] = {
            cat: [] for cat in ToolCategory
        }
        self._initialized = True

        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        self.register_tool(
            name="screen_capture",
            handler=self._tool_screen_capture,
            info=ToolInfo(
                name="screen_capture",
                description="Capture screen screenshot",
                category=ToolCategory.SCREEN,
                parameters=[
                    ToolParameter(name="save_path", type="string", required=False),
                ],
                returns="Screenshot file path or base64 data",
            ),
        )

        self.register_tool(
            name="screen_tap",
            handler=self._tool_screen_tap,
            info=ToolInfo(
                name="screen_tap",
                description="Tap on screen at specified coordinates",
                category=ToolCategory.SCREEN,
                parameters=[
                    ToolParameter(name="x", type="integer", required=True),
                    ToolParameter(name="y", type="integer", required=True),
                ],
                returns="Success status",
            ),
        )

        self.register_tool(
            name="screen_swipe",
            handler=self._tool_screen_swipe,
            info=ToolInfo(
                name="screen_swipe",
                description="Swipe on screen from one point to another",
                category=ToolCategory.SCREEN,
                parameters=[
                    ToolParameter(name="x1", type="integer", required=True),
                    ToolParameter(name="y1", type="integer", required=True),
                    ToolParameter(name="x2", type="integer", required=True),
                    ToolParameter(name="y2", type="integer", required=True),
                    ToolParameter(name="duration", type="integer", required=False, default=300),
                ],
                returns="Success status",
            ),
        )

        self.register_tool(
            name="list_packages",
            handler=self._tool_list_packages,
            info=ToolInfo(
                name="list_packages",
                description="List installed packages",
                category=ToolCategory.PACKAGE,
                parameters=[
                    ToolParameter(
                        name="type",
                        type="string",
                        required=False,
                        default="all",
                        choices=["all", "system", "third_party"],
                    ),
                ],
                returns="List of package info",
            ),
        )

        self.register_tool(
            name="get_package_info",
            handler=self._tool_get_package_info,
            info=ToolInfo(
                name="get_package_info",
                description="Get detailed info of a package",
                category=ToolCategory.PACKAGE,
                parameters=[
                    ToolParameter(name="package_name", type="string", required=True),
                ],
                returns="Package info",
            ),
        )

        self.register_tool(
            name="launch_package",
            handler=self._tool_launch_package,
            info=ToolInfo(
                name="launch_package",
                description="Launch an application by package name",
                category=ToolCategory.PACKAGE,
                parameters=[
                    ToolParameter(name="package_name", type="string", required=True),
                ],
                returns="Success status",
            ),
        )

        self.register_tool(
            name="stop_package",
            handler=self._tool_stop_package,
            info=ToolInfo(
                name="stop_package",
                description="Force stop an application",
                category=ToolCategory.PACKAGE,
                parameters=[
                    ToolParameter(name="package_name", type="string", required=True),
                ],
                returns="Success status",
            ),
        )

        self.register_tool(
            name="get_running_packages",
            handler=self._tool_get_running_packages,
            info=ToolInfo(
                name="get_running_packages",
                description="Get list of running packages",
                category=ToolCategory.PACKAGE,
                parameters=[],
                returns="List of running packages",
            ),
        )

        self.register_tool(
            name="get_notifications",
            handler=self._tool_get_notifications,
            info=ToolInfo(
                name="get_notifications",
                description="Get active notifications",
                category=ToolCategory.NOTIFICATION,
                parameters=[
                    ToolParameter(name="limit", type="integer", required=False, default=50),
                ],
                returns="List of notifications",
            ),
        )

        self.register_tool(
            name="send_sms",
            handler=self._tool_send_sms,
            info=ToolInfo(
                name="send_sms",
                description="Send SMS message",
                category=ToolCategory.SMS,
                parameters=[
                    ToolParameter(name="to", type="string", required=True),
                    ToolParameter(name="body", type="string", required=True),
                ],
                returns="Success status",
            ),
        )

        self.register_tool(
            name="mnn_load_model",
            handler=self._tool_mnn_load_model,
            info=ToolInfo(
                name="mnn_load_model",
                description="Load MNN model for inference",
                category=ToolCategory.MNN,
                parameters=[
                    ToolParameter(name="model_name", type="string", required=True),
                ],
                returns="Success status",
            ),
        )

        self.register_tool(
            name="mnn_inference",
            handler=self._tool_mnn_inference,
            info=ToolInfo(
                name="mnn_inference",
                description="Run MNN inference",
                category=ToolCategory.MNN,
                parameters=[
                    ToolParameter(name="input", type="string", required=True),
                    ToolParameter(name="max_tokens", type="integer", required=False, default=512),
                ],
                returns="Inference result",
            ),
        )

        self.register_tool(
            name="workflow_create",
            handler=self._tool_workflow_create,
            info=ToolInfo(
                name="workflow_create",
                description="Create a new workflow",
                category=ToolCategory.WORKFLOW,
                parameters=[
                    ToolParameter(name="name", type="string", required=True),
                    ToolParameter(name="steps", type="array", required=True),
                    ToolParameter(name="description", type="string", required=False),
                ],
                returns="Created workflow info",
            ),
        )

        self.register_tool(
            name="workflow_execute",
            handler=self._tool_workflow_execute,
            info=ToolInfo(
                name="workflow_execute",
                description="Execute a workflow",
                category=ToolCategory.WORKFLOW,
                parameters=[
                    ToolParameter(name="workflow_id", type="string", required=True),
                    ToolParameter(name="context", type="object", required=False),
                ],
                returns="Execution result",
            ),
        )

        self.register_tool(
            name="workflow_list",
            handler=self._tool_workflow_list,
            info=ToolInfo(
                name="workflow_list",
                description="List all workflows",
                category=ToolCategory.WORKFLOW,
                parameters=[],
                returns="List of workflows",
            ),
        )

        self.register_tool(
            name="phone_operation",
            handler=self._tool_phone_operation,
            info=ToolInfo(
                name="phone_operation",
                description="手机操作工具，通过自然语言控制手机执行各种操作。支持打开应用、点击、滑动、输入文本等操作。",
                category=ToolCategory.WORKFLOW,
                parameters=[
                    ToolParameter(
                        name="intent",
                        type="string",
                        required=True,
                        description="自然语言操作意图，如：'打开微信发送消息给张三'、'打开设置关闭蓝牙'",
                    ),
                    ToolParameter(
                        name="target_app",
                        type="string",
                        required=False,
                        description="目标应用包名（可选），如：com.tencent.mm",
                    ),
                    ToolParameter(
                        name="max_steps",
                        type="integer",
                        required=False,
                        default=20,
                        description="最大执行步骤数，默认20",
                    ),
                    ToolParameter(
                        name="use_virtual_display",
                        type="boolean",
                        required=False,
                        default=False,
                        description="是否使用虚拟屏幕执行（不影响主屏幕），默认false",
                    ),
                ],
                returns="包含 success, message, steps_taken, final_state 的执行结果",
                examples=[
                    "打开微信发送消息给张三",
                    "打开设置关闭蓝牙",
                    "在支付宝中查看余额",
                ],
            ),
        )

    def register_tool(
        self,
        name: str,
        handler: Callable,
        info: ToolInfo | None = None,
        on_activate: Callable | None = None,
        on_dormant: Callable | None = None,
    ) -> bool:
        if name in self._tools:
            logger.warning(f"Tool already registered: {name}")
            return False

        tool = MobileTool(
            name=name,
            handler=handler,
            info=info or ToolInfo(name=name),
            on_activate=on_activate,
            on_dormant=on_dormant,
        )

        self._tools[name] = tool
        self._categories[tool.info.category].append(name)

        logger.info(f"Registered tool: {name} (category: {tool.info.category.value})")
        return True

    def unregister_tool(self, name: str) -> bool:
        if name not in self._tools:
            return False

        tool = self._tools.pop(name)
        if name in self._categories[tool.info.category]:
            self._categories[tool.info.category].remove(name)

        tool.dormant()
        logger.info(f"Unregistered tool: {name}")
        return True

    def get_tool(self, name: str) -> MobileTool | None:
        return self._tools.get(name)

    def list_tools(
        self,
        category: ToolCategory | None = None,
    ) -> list[ToolInfo]:
        if category:
            tool_names = self._categories.get(category, [])
            return [self._tools[n].info for n in tool_names if n in self._tools]

        return [t.info for t in self._tools.values()]

    async def execute_tool(
        self,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
            )

        return await tool.execute(params or {})

    def get_tools_by_category(self, category: ToolCategory) -> list[ToolInfo]:
        tool_names = self._categories.get(category, [])
        return [self._tools[n].info for n in tool_names if n in self._tools]

    async def _tool_screen_capture(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.screen_tools import ScreenTools

            tools = ScreenTools()
            result = await tools.capture_screen()

            return ToolResult(
                success=result.success,
                data=result.to_dict(),
                error=result.error,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_screen_tap(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.screen_tools import ScreenTools

            tools = ScreenTools()
            x = params.get("x", 0)
            y = params.get("y", 0)
            result = await tools.tap(x, y)

            return ToolResult(
                success=result.success,
                data=result.to_dict(),
                error=result.error,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_screen_swipe(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.screen_tools import ScreenTools

            tools = ScreenTools()
            x1 = params.get("x1", 0)
            y1 = params.get("y1", 0)
            x2 = params.get("x2", 0)
            y2 = params.get("y2", 0)
            duration = params.get("duration", 300)
            result = await tools.swipe(x1, y1, x2, y2, duration)

            return ToolResult(
                success=result.success,
                data=result.to_dict(),
                error=result.error,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_list_packages(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.package_manager import PackageType, package_manager

            pkg_type_str = params.get("type", "all")
            pkg_type = {
                "system": PackageType.SYSTEM,
                "third_party": PackageType.THIRD_PARTY,
                "all": PackageType.ALL,
            }.get(pkg_type_str, PackageType.ALL)

            packages = package_manager.list_packages(pkg_type)
            return ToolResult(
                success=True,
                data=[p.to_dict() for p in packages],
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_get_package_info(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.package_manager import package_manager

            package_name = params.get("package_name", "")
            info = package_manager.get_package_info(package_name)

            if info:
                return ToolResult(success=True, data=info.to_dict())
            return ToolResult(success=False, error="Package not found")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_launch_package(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.package_manager import package_manager

            package_name = params.get("package_name", "")
            success = package_manager.launch_package(package_name)

            return ToolResult(success=success, data={"package_name": package_name})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_stop_package(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.package_manager import package_manager

            package_name = params.get("package_name", "")
            success = package_manager.force_stop(package_name)

            return ToolResult(success=success, data={"package_name": package_name})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_get_running_packages(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.package_manager import package_manager

            packages = package_manager.get_running_packages()
            return ToolResult(
                success=True,
                data=[p.to_dict() for p in packages],
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_get_notifications(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.notification import NotificationReader

            reader = NotificationReader()
            notifications = await reader.get_notifications()

            return ToolResult(success=True, data=notifications)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_send_sms(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.sms import SMSTools

            tools = SMSTools()
            to = params.get("to", "")
            body = params.get("body", "")
            result = await tools.send_message(to, body)

            return ToolResult(
                success=result.success,
                data=result.to_dict(),
                error=result.error,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_mnn_load_model(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.mnn_inference import mnn_inference

            model_name = params.get("model_name", "")
            success = mnn_inference.load_model(model_name)

            return ToolResult(
                success=success,
                data={
                    "model_name": model_name,
                    "current_model": mnn_inference.current_model,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_mnn_inference(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.mnn_inference import mnn_inference

            input_text = params.get("input", "")
            max_tokens = params.get("max_tokens", 512)

            result = mnn_inference.run_inference(input_text, max_tokens=max_tokens)

            return ToolResult(
                success=result.success,
                data={
                    "text": result.text,
                    "tokens_generated": result.tokens_generated,
                    "inference_time_ms": result.inference_time_ms,
                    "tokens_per_second": result.tokens_per_second,
                },
                error=result.error,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_workflow_create(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.workflow import workflow_automation

            name = params.get("name", "")
            steps = params.get("steps", [])
            description = params.get("description", "")

            workflow = workflow_automation.create_workflow(
                name=name,
                steps=steps,
                description=description,
            )

            return ToolResult(
                success=True,
                data={
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_workflow_execute(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.workflow import workflow_automation

            workflow_id = params.get("workflow_id", "")
            context = params.get("context", {})

            execution = await workflow_automation.execute_workflow(
                workflow_id,
                context=context,
            )

            return ToolResult(
                success=execution.status.value == "completed",
                data=execution.to_dict(),
                error=execution.error,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_workflow_list(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.mobile.workflow import workflow_automation

            workflows = workflow_automation.list_workflows()

            return ToolResult(
                success=True,
                data=[w.to_dict() for w in workflows],
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _tool_phone_operation(self, params: dict[str, Any]) -> ToolResult:
        try:
            from src.llm import get_default_client
            from src.mobile.advanced_control.subagent import get_mobile_control_manager

            intent = params.get("intent", "")
            if not intent:
                return ToolResult(
                    success=False,
                    error="intent 参数是必需的",
                )

            target_app = params.get("target_app")
            max_steps = params.get("max_steps", 20)
            use_virtual_display = params.get("use_virtual_display", False)

            llm_client = get_default_client()
            manager = get_mobile_control_manager(llm_client)

            if use_virtual_display:
                result = await manager.run_subagent_virtual(
                    intent=intent,
                    max_steps=max_steps,
                    target_app=target_app,
                )
            else:
                result = await manager.run_subagent_main(
                    intent=intent,
                    max_steps=max_steps,
                    target_app=target_app,
                )

            return ToolResult(
                success=result.success,
                data={
                    "success": result.success,
                    "message": result.message,
                    "steps_taken": result.steps_taken,
                    "final_state": result.final_state,
                    "agent_id": result.agent_id,
                    "error": result.error,
                },
                error=result.error,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def cleanup(self) -> None:
        for tool in self._tools.values():
            tool.dormant()

        self._tools.clear()
        for category in self._categories:
            self._categories[category] = []

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance:
            cls._instance.cleanup()
            cls._instance = None


mobile_tool_registry = MobileToolRegistry()
