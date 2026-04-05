"""
PyAgent 移动端支持 - 高级手机控制模块

参考 Operit 项目的 AutoGLM 子代理模式实现智能手机控制。
v0.8.0: 增强子代理执行流程，实现真正的循环执行
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.llm.client import get_default_client
from src.llm.types import TaskType
from src.mobile.screen_tools import ScreenTools
from src.tools.base import ToolContext, ToolResult

logger = logging.getLogger(__name__)


class SubAgentStatus(str, Enum):
    """子代理状态"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class SubAgentResult:
    """子代理执行结果"""
    success: bool
    message: str
    agent_id: str
    final_state: str | None = None
    steps_taken: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    completed_at: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class ActionStep:
    """操作步骤"""
    step_id: int
    action_type: str
    params: dict[str, Any]
    description: str
    screenshot_before: str | None = None
    screenshot_after: str | None = None
    result: str | None = None
    success: bool | None = None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    analysis: str | None = None
    verification: str | None = None


@dataclass
class ScreenAnalysis:
    """屏幕分析结果"""
    description: str
    interactive_elements: list[dict[str, Any]]
    current_app: str | None = None
    current_activity: str | None = None
    suggested_actions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PlannedAction:
    """规划的操作"""
    action_type: str
    params: dict[str, Any]
    description: str
    confidence: float = 0.8
    reason: str = ""


class MobileSubAgent:
    """手机操作子代理

    使用 screen-operation 垂类模型执行自然语言操作意图。
    实现循环执行流程：截图 -> 分析 -> 规划 -> 执行 -> 验证
    """

    MAX_STEPS = 20
    DEFAULT_WAIT_MS = 500

    def __init__(
        self,
        agent_id: str,
        llm_client: Any = None,
        target_app: str | None = None,
        is_virtual: bool = False,
        device_id: str = ""
    ):
        self.agent_id = agent_id
        self.llm_client = llm_client or get_default_client()
        self.target_app = target_app
        self.is_virtual = is_virtual
        self.device_id = device_id
        self._status = SubAgentStatus.IDLE
        self._context: dict[str, Any] = {}
        self._action_history: list[ActionStep] = []
        self._created_at = datetime.now().timestamp()
        self._screen_tools: ScreenTools | None = None
        self._tool_context: ToolContext | None = None
        self._current_screenshot: str | None = None
        self._intent: str = ""
        self._step_count: int = 0

    @property
    def status(self) -> SubAgentStatus:
        return self._status

    async def _init_screen_tools(self) -> bool:
        """初始化屏幕工具"""
        try:
            self._screen_tools = ScreenTools(device_id=self.device_id)
            self._tool_context = ToolContext(device_id=self.device_id)

            result = await self._screen_tools.activate(self._tool_context)
            if result:
                logger.info(f"ScreenTools activated for agent {self.agent_id}")
                return True
            else:
                logger.error(f"Failed to activate ScreenTools for agent {self.agent_id}")
                return False
        except Exception as e:
            logger.error(f"Error initializing ScreenTools: {e}")
            return False

    async def _capture_screen(self) -> str | None:
        """截取屏幕

        Returns:
            截图的 base64 编码，失败返回 None
        """
        if not self._screen_tools or not self._tool_context:
            logger.error("ScreenTools not initialized")
            return None

        try:
            result = await self._screen_tools.capture_screen()
            if result.success and result.data:
                base64_data = result.data.get("image_base64")
                self._current_screenshot = base64_data
                logger.debug(f"Screen captured, size: {len(base64_data) if base64_data else 0}")
                return base64_data
            else:
                logger.error(f"Failed to capture screen: {result.error}")
                return None
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None

    async def _analyze_screen(self, screenshot_base64: str) -> ScreenAnalysis | None:
        """分析屏幕内容

        Args:
            screenshot_base64: 截图的 base64 编码

        Returns:
            ScreenAnalysis 对象，失败返回 None
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self._build_analysis_prompt()
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ]

            response = await self.llm_client.generate_with_multimodal_fallback(
                messages=messages,
                system=self._build_system_prompt(),
                task_type=TaskType.SCREEN_OPERATION,
                temperature=0.3
            )

            content = response.content
            analysis = self._parse_analysis_response(content)

            if analysis:
                logger.info(f"Screen analyzed: {len(analysis.interactive_elements)} elements found")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            return None

    def _build_analysis_prompt(self) -> str:
        """构建分析提示词"""
        app_context = f"目标应用: {self.target_app}" if self.target_app else ""
        history_context = self._build_history_context()

        return f"""请分析当前屏幕内容，提取可操作的元素。

用户意图: {self._intent}
{app_context}

{history_context}

请以 JSON 格式输出分析结果：
```json
{{
    "description": "屏幕内容描述",
    "current_app": "当前应用包名（如果能识别）",
    "current_activity": "当前活动名称（如果能识别）",
    "interactive_elements": [
        {{
            "type": "button/input/icon/list_item/text",
            "text": "元素文本",
            "description": "元素描述",
            "bounds": {{"x": 0, "y": 0, "width": 100, "height": 50}},
            "action_hint": "点击此元素可能执行的操作"
        }}
    ],
    "suggested_actions": [
        {{
            "action": "tap/swipe/input_text/press_key/launch",
            "params": {{}},
            "description": "操作描述",
            "reason": "为什么建议此操作"
        }}
    ]
}}
```

注意：
1. 识别所有可见的可交互元素
2. 提供元素的准确位置信息
3. 根据用户意图推荐下一步操作
4. 如果任务已完成，在 suggested_actions 中包含 {{"action": "complete", "reason": "..."}}"""

    def _build_history_context(self) -> str:
        """构建历史操作上下文"""
        if not self._action_history:
            return "这是第一步操作。"

        recent_steps = self._action_history[-5:]
        history_lines = []
        for step in recent_steps:
            status = "成功" if step.success else "失败"
            history_lines.append(
                f"步骤 {step.step_id}: {step.action_type} - {step.description} [{status}]"
            )

        return "最近操作历史:\n" + "\n".join(history_lines)

    def _parse_analysis_response(self, content: str) -> ScreenAnalysis | None:
        """解析分析响应"""
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)

                return ScreenAnalysis(
                    description=data.get("description", ""),
                    interactive_elements=data.get("interactive_elements", []),
                    current_app=data.get("current_app"),
                    current_activity=data.get("current_activity"),
                    suggested_actions=data.get("suggested_actions", [])
                )
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")

        return None

    async def _plan_next_action(
        self,
        screen_analysis: ScreenAnalysis,
        screenshot_base64: str
    ) -> PlannedAction | None:
        """规划下一步操作

        Args:
            screen_analysis: 屏幕分析结果
            screenshot_base64: 当前截图

        Returns:
            PlannedAction 对象，失败返回 None
        """
        try:
            for action in screen_analysis.suggested_actions:
                if action.get("action") == "complete":
                    return PlannedAction(
                        action_type="complete",
                        params={},
                        description="任务已完成",
                        reason=action.get("reason", "目标已达成")
                    )

            if screen_analysis.suggested_actions:
                best_action = screen_analysis.suggested_actions[0]
                return PlannedAction(
                    action_type=best_action.get("action", "tap"),
                    params=best_action.get("params", {}),
                    description=best_action.get("description", ""),
                    reason=best_action.get("reason", "")
                )

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self._build_planning_prompt(screen_analysis)
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ]

            response = await self.llm_client.generate_with_multimodal_fallback(
                messages=messages,
                system=self._build_system_prompt(),
                task_type=TaskType.SCREEN_OPERATION,
                temperature=0.3
            )

            return self._parse_planning_response(response.content)

        except Exception as e:
            logger.error(f"Error planning next action: {e}")
            return None

    def _build_planning_prompt(self, screen_analysis: ScreenAnalysis) -> str:
        """构建规划提示词"""
        elements_desc = []
        for elem in screen_analysis.interactive_elements[:10]:
            elements_desc.append(
                f"- {elem.get('type', 'unknown')}: {elem.get('text', '')} "
                f"at ({elem.get('bounds', {}).get('x', 0)}, {elem.get('bounds', {}).get('y', 0)})"
            )

        return f"""根据当前屏幕内容和用户意图，规划下一步操作。

用户意图: {self._intent}
屏幕描述: {screen_analysis.description}

可交互元素:
{chr(10).join(elements_desc)}

{self._build_history_context()}

请以 JSON 格式输出下一步操作：
```json
{{
    "action": "tap/swipe/input_text/press_key/launch/complete",
    "params": {{
        "x": 100,
        "y": 200,
        "text": "输入文本",
        "key": "back/home/recent",
        "package": "应用包名"
    }},
    "description": "操作描述",
    "confidence": 0.8,
    "reason": "为什么选择此操作"
}}
```

如果任务已完成，使用 action: "complete"。"""

    def _parse_planning_response(self, content: str) -> PlannedAction | None:
        """解析规划响应"""
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)

                return PlannedAction(
                    action_type=data.get("action", "tap"),
                    params=data.get("params", {}),
                    description=data.get("description", ""),
                    confidence=data.get("confidence", 0.8),
                    reason=data.get("reason", "")
                )
        except Exception as e:
            logger.error(f"Failed to parse planning response: {e}")

        return None

    async def _execute_action(self, action: PlannedAction) -> ToolResult:
        """执行操作

        Args:
            action: 规划的操作

        Returns:
            ToolResult 执行结果
        """
        if not self._screen_tools or not self._tool_context:
            return ToolResult(success=False, error="ScreenTools not initialized")

        try:
            action_type = action.action_type
            params = action.params

            if action_type == "complete":
                return ToolResult(
                    success=True,
                    output="Task completed",
                    data={"completed": True, "reason": action.reason}
                )

            elif action_type == "tap":
                x = params.get("x", 0)
                y = params.get("y", 0)
                result = await self._screen_tools.tap(x, y)
                await self._wait_for_response()
                return result

            elif action_type == "swipe":
                result = await self._screen_tools.swipe(
                    params.get("x1", 0),
                    params.get("y1", 0),
                    params.get("x2", 0),
                    params.get("y2", 0),
                    params.get("duration", 300)
                )
                await self._wait_for_response()
                return result

            elif action_type == "input_text":
                text = params.get("text", "")
                result = await self._screen_tools.input_text(text)
                await self._wait_for_response()
                return result

            elif action_type == "press_key":
                key = params.get("key", "back")
                keycode = self._get_keycode(key)
                result = await self._screen_tools.press_key(keycode)
                await self._wait_for_response()
                return result

            elif action_type == "launch":
                package = params.get("package", "")
                if package:
                    result = await self._launch_app(package)
                    await self._wait_for_response(1000)
                    return result
                else:
                    return ToolResult(success=False, error="No package specified")

            elif action_type == "long_press":
                x = params.get("x", 0)
                y = params.get("y", 0)
                duration = params.get("duration", 1000)
                result = await self._screen_tools.long_press(x, y, duration)
                await self._wait_for_response()
                return result

            else:
                return ToolResult(success=False, error=f"Unknown action type: {action_type}")

        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return ToolResult(success=False, error=str(e))

    def _get_keycode(self, key: str) -> str:
        """获取按键代码"""
        key_map = {
            "back": "KEYCODE_BACK",
            "home": "KEYCODE_HOME",
            "recent": "KEYCODE_APP_SWITCH",
            "volume_up": "KEYCODE_VOLUME_UP",
            "volume_down": "KEYCODE_VOLUME_DOWN",
            "power": "KEYCODE_POWER",
            "menu": "KEYCODE_MENU",
            "enter": "KEYCODE_ENTER",
            "delete": "KEYCODE_DEL"
        }
        return key_map.get(key.lower(), f"KEYCODE_{key.upper()}")

    async def _launch_app(self, package: str) -> ToolResult:
        """启动应用"""
        import subprocess

        try:
            result = subprocess.run(
                ["adb", "shell", "monkey", "-p", package,
                 "-c", "android.intent.category.LAUNCHER", "1"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    output=f"Launched app: {package}"
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Failed to launch app: {result.stderr}"
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _wait_for_response(self, wait_ms: int | None = None):
        """等待界面响应"""
        wait_time = wait_ms or self.DEFAULT_WAIT_MS
        await asyncio.sleep(wait_time / 1000.0)

    def _is_task_complete(self, action: PlannedAction, result: ToolResult) -> bool:
        """判断任务是否完成

        Args:
            action: 执行的操作
            result: 执行结果

        Returns:
            任务是否完成
        """
        if action.action_type == "complete":
            return True

        if result.data and result.data.get("completed"):
            return True

        if self._step_count >= self.MAX_STEPS:
            logger.warning(f"Max steps reached: {self._step_count}")
            return True

        return False

    async def _verify_result(
        self,
        action: PlannedAction,
        result: ToolResult,
        screenshot_before: str | None,
        screenshot_after: str | None
    ) -> bool:
        """验证操作结果

        Args:
            action: 执行的操作
            result: 执行结果
            screenshot_before: 操作前截图
            screenshot_after: 操作后截图

        Returns:
            验证是否通过
        """
        if not result.success:
            return False

        if action.action_type == "complete":
            return True

        if not screenshot_after:
            return True

        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""验证操作是否成功执行。

操作: {action.action_type}
参数: {json.dumps(action.params)}
描述: {action.description}
执行结果: {result.output}

请判断操作是否成功执行，以及是否需要重试。
输出 JSON:
```json
{{
    "success": true/false,
    "reason": "判断理由",
    "need_retry": true/false,
    "suggestion": "如果需要重试，建议的操作"
}}
```"""
                        }
                    ]
                }
            ]

            response = await self.llm_client.generate(
                messages=messages,
                system=self._build_system_prompt(),
                task_type=TaskType.SCREEN_OPERATION,
                temperature=0.3
            )

            verification = self._parse_verification_response(response.content)
            return verification.get("success", True)

        except Exception as e:
            logger.error(f"Error verifying result: {e}")
            return True

    def _parse_verification_response(self, content: str) -> dict:
        """解析验证响应"""
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse verification response: {e}")

        return {"success": True}

    async def run(self, intent: str, max_steps: int = 20) -> SubAgentResult:
        """
        执行操作意图

        实现循环执行流程：截图 -> 分析 -> 规划 -> 执行 -> 验证

        Args:
            intent: 自然语言操作意图
            max_steps: 最大步骤数

        Returns:
            SubAgentResult: 执行结果
        """
        self._status = SubAgentStatus.RUNNING
        self._action_history.clear()
        self._intent = intent
        self._step_count = 0
        self.MAX_STEPS = max_steps

        try:
            if not await self._init_screen_tools():
                return SubAgentResult(
                    success=False,
                    message="Failed to initialize screen tools",
                    agent_id=self.agent_id,
                    error="ScreenTools initialization failed"
                )

            while self._step_count < self.MAX_STEPS:
                self._step_count += 1
                logger.info(f"Step {self._step_count}/{self.MAX_STEPS}")

                screenshot_before = await self._capture_screen()
                if not screenshot_before:
                    logger.warning("Failed to capture screen, retrying...")
                    await asyncio.sleep(1)
                    continue

                screen_analysis = await self._analyze_screen(screenshot_before)
                if not screen_analysis:
                    logger.warning("Failed to analyze screen, retrying...")
                    await asyncio.sleep(1)
                    continue

                planned_action = await self._plan_next_action(screen_analysis, screenshot_before)
                if not planned_action:
                    logger.warning("Failed to plan action, retrying...")
                    await asyncio.sleep(1)
                    continue

                if self._is_task_complete(planned_action, ToolResult(success=True)):
                    logger.info(f"Task completed at step {self._step_count}")
                    self._status = SubAgentStatus.COMPLETED
                    return SubAgentResult(
                        success=True,
                        message=planned_action.reason or "Task completed successfully",
                        agent_id=self.agent_id,
                        final_state="completed",
                        steps_taken=self._step_count,
                        data={
                            "intent": intent,
                            "action_history": [self._action_step_to_dict(s) for s in self._action_history]
                        }
                    )

                action_step = ActionStep(
                    step_id=self._step_count,
                    action_type=planned_action.action_type,
                    params=planned_action.params,
                    description=planned_action.description,
                    screenshot_before=screenshot_before,
                    analysis=screen_analysis.description
                )

                execute_result = await self._execute_action(planned_action)
                action_step.result = execute_result.output
                action_step.success = execute_result.success

                await self._wait_for_response()

                screenshot_after = await self._capture_screen()
                action_step.screenshot_after = screenshot_after

                verified = await self._verify_result(
                    planned_action,
                    execute_result,
                    screenshot_before,
                    screenshot_after
                )
                action_step.verification = "passed" if verified else "failed"

                self._action_history.append(action_step)

                if not verified:
                    logger.warning(f"Action verification failed at step {self._step_count}")

                if self._is_task_complete(planned_action, execute_result):
                    logger.info(f"Task completed at step {self._step_count}")
                    self._status = SubAgentStatus.COMPLETED
                    return SubAgentResult(
                        success=True,
                        message="Task completed successfully",
                        agent_id=self.agent_id,
                        final_state="completed",
                        steps_taken=self._step_count,
                        data={
                            "intent": intent,
                            "action_history": [self._action_step_to_dict(s) for s in self._action_history]
                        }
                    )

            logger.warning(f"Max steps reached: {self.MAX_STEPS}")
            self._status = SubAgentStatus.COMPLETED
            return SubAgentResult(
                success=False,
                message=f"Max steps ({self.MAX_STEPS}) reached without completion",
                agent_id=self.agent_id,
                final_state="incomplete",
                steps_taken=self._step_count,
                data={
                    "intent": intent,
                    "action_history": [self._action_step_to_dict(s) for s in self._action_history]
                }
            )

        except Exception as e:
            logger.error(f"SubAgent {self.agent_id} failed: {e}")
            self._status = SubAgentStatus.FAILED
            return SubAgentResult(
                success=False,
                message=f"执行失败: {str(e)}",
                agent_id=self.agent_id,
                error=str(e)
            )
        finally:
            if self._screen_tools and self._tool_context:
                try:
                    await self._screen_tools.dormant(self._tool_context)
                except Exception as e:
                    logger.error(f"Error deactivating ScreenTools: {e}")

    def _action_step_to_dict(self, step: ActionStep) -> dict:
        """将 ActionStep 转换为字典"""
        return {
            "step_id": step.step_id,
            "action_type": step.action_type,
            "params": step.params,
            "description": step.description,
            "result": step.result,
            "success": step.success,
            "timestamp": step.timestamp,
            "analysis": step.analysis,
            "verification": step.verification
        }

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        app_context = f"当前应用: {self.target_app}" if self.target_app else ""
        virtual_context = "运行在虚拟屏幕上，不影响主屏幕" if self.is_virtual else "运行在主屏幕上"

        return f"""你是一个手机操作助手，可以根据用户的自然语言意图执行手机操作。

{app_context}
运行模式: {virtual_context}

你可以执行以下操作:
- tap(x, y): 点击屏幕坐标
- double_tap(x, y): 双击坐标
- long_press(x, y, duration): 长按坐标
- swipe(x1, y1, x2, y2, duration_ms): 滑动
- input_text(text): 输入文本
- press_key(key): 按键 (back, home, recent, volume_up, volume_down)
- launch(package): 启动应用
- complete: 任务完成

注意:
1. 操作要精确，避免误触
2. 每次操作后等待界面响应
3. 如果找不到目标元素，尝试滚动或返回
4. 最多执行 {self.MAX_STEPS} 个步骤
5. 所有输出必须是有效的 JSON 格式"""

    def get_context(self) -> dict[str, Any]:
        """获取上下文"""
        return {
            "agent_id": self.agent_id,
            "status": self._status.value,
            "target_app": self.target_app,
            "is_virtual": self.is_virtual,
            "action_count": len(self._action_history),
            "created_at": self._created_at,
            "step_count": self._step_count
        }

    def pause(self) -> bool:
        """暂停执行"""
        if self._status == SubAgentStatus.RUNNING:
            self._status = SubAgentStatus.PAUSED
            return True
        return False

    def resume(self) -> bool:
        """恢复执行"""
        if self._status == SubAgentStatus.PAUSED:
            self._status = SubAgentStatus.RUNNING
            return True
        return False

    def get_action_history(self) -> list[dict[str, Any]]:
        """获取操作历史"""
        return [self._action_step_to_dict(s) for s in self._action_history]


class MobileControlManager:
    """手机控制管理器

    管理多个子代理的创建、执行和销毁。
    """

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client or get_default_client()
        self._virtual_displays: dict[str, MobileSubAgent] = {}
        self._cached_agent_id: str | None = None
        self._main_agent: MobileSubAgent | None = None

    async def run_subagent_main(
        self,
        intent: str,
        max_steps: int = 20,
        target_app: str | None = None,
        device_id: str = ""
    ) -> SubAgentResult:
        """
        在主屏幕执行操作

        Args:
            intent: 操作意图
            max_steps: 最大步骤数
            target_app: 目标应用
            device_id: 设备ID

        Returns:
            SubAgentResult: 执行结果
        """
        self._main_agent = MobileSubAgent(
            agent_id="main",
            llm_client=self.llm_client,
            target_app=target_app,
            is_virtual=False,
            device_id=device_id
        )

        logger.info(f"Running main agent with intent: {intent[:50]}...")
        return await self._main_agent.run(intent, max_steps)

    async def run_subagent_virtual(
        self,
        intent: str,
        agent_id: str | None = None,
        max_steps: int = 20,
        target_app: str | None = None,
        device_id: str = ""
    ) -> SubAgentResult:
        """
        在虚拟屏幕执行操作

        Args:
            intent: 操作意图
            agent_id: 代理ID（用于复用会话）
            max_steps: 最大步骤数
            target_app: 目标应用
            device_id: 设备ID

        Returns:
            SubAgentResult: 执行结果
        """
        if agent_id and agent_id in self._virtual_displays:
            agent = self._virtual_displays[agent_id]
            logger.info(f"Reusing virtual agent: {agent_id}")
        else:
            agent_id = agent_id or self._generate_agent_id()
            agent = MobileSubAgent(
                agent_id=agent_id,
                llm_client=self.llm_client,
                target_app=target_app,
                is_virtual=True,
                device_id=device_id
            )
            self._virtual_displays[agent_id] = agent
            logger.info(f"Created virtual agent: {agent_id}")

        self._cached_agent_id = agent_id
        return await agent.run(intent, max_steps)

    async def run_subagent_parallel(
        self,
        intents: list[dict[str, Any]]
    ) -> list[SubAgentResult]:
        """
        并行执行多个子代理

        Args:
            intents: 意图列表，每个包含 intent, agent_id, target_app, device_id

        Returns:
            list[SubAgentResult]: 执行结果列表
        """
        app_assignments: dict[str, str] = {}
        for item in intents:
            target_app = item.get("target_app")
            if target_app:
                if target_app in app_assignments:
                    if app_assignments[target_app] != item.get("agent_id"):
                        logger.warning(f"App conflict detected: {target_app}")
                        item["conflict"] = True
                else:
                    app_assignments[target_app] = item.get("agent_id", "")

        tasks = []
        for item in intents:
            if item.get("conflict"):
                tasks.append(asyncio.create_task(
                    self._create_conflict_result(item)
                ))
            else:
                tasks.append(asyncio.create_task(
                    self.run_subagent_virtual(
                        intent=item["intent"],
                        agent_id=item.get("agent_id"),
                        target_app=item.get("target_app"),
                        device_id=item.get("device_id", "")
                    )
                ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r if isinstance(r, SubAgentResult) else SubAgentResult(
                success=False,
                message=str(r),
                agent_id="error"
            )
            for r in results
        ]

    async def _create_conflict_result(self, item: dict) -> SubAgentResult:
        """创建冲突结果"""
        return SubAgentResult(
            success=False,
            message=f"应用冲突: {item.get('target_app')} 已被其他代理使用",
            agent_id=item.get("agent_id", "unknown"),
            error="App conflict"
        )

    def get_agent(self, agent_id: str) -> MobileSubAgent | None:
        """获取代理"""
        if agent_id == "main":
            return self._main_agent
        return self._virtual_displays.get(agent_id)

    def get_cached_agent_id(self) -> str | None:
        """获取缓存的代理ID"""
        return self._cached_agent_id

    def close_all_virtual_displays(self) -> int:
        """关闭所有虚拟屏幕"""
        count = len(self._virtual_displays)
        self._virtual_displays.clear()
        self._cached_agent_id = None
        logger.info(f"Closed {count} virtual displays")
        return count

    def _generate_agent_id(self) -> str:
        """生成代理ID"""
        return f"agent_{uuid.uuid4().hex[:8]}"

    def get_status(self) -> dict[str, Any]:
        """获取状态"""
        return {
            "virtual_displays": len(self._virtual_displays),
            "cached_agent_id": self._cached_agent_id,
            "main_agent_status": self._main_agent.status.value if self._main_agent else None,
            "agents": [
                agent.get_context()
                for agent in self._virtual_displays.values()
            ]
        }


mobile_control_manager: MobileControlManager | None = None


def get_mobile_control_manager(llm_client: Any = None) -> MobileControlManager:
    """获取手机控制管理器"""
    global mobile_control_manager
    if mobile_control_manager is None:
        mobile_control_manager = MobileControlManager(llm_client)
    return mobile_control_manager
