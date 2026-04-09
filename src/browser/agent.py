"""
PyAgent 浏览器自动化模块 - AI 驱动的浏览器代理

提供 AI 驱动的浏览器代理系统，能够理解自然语言任务并自动执行。
参考 browser-use 项目的 Agent 设计实现。
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel

from .event_bus import EventBus
from .loop_detector import LoopDetector
from .registry import ActionResult, Registry
from .state import BrowserState, StateManager

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AgentState(str, Enum):
    """代理状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class AgentStatus(BaseModel):
    """代理状态信息"""
    state: AgentState = AgentState.IDLE
    current_step: int = 0
    max_steps: int = 100
    current_url: str | None = None
    current_task: str | None = None
    started_at: float | None = None
    elapsed_time: float = 0.0
    actions_taken: int = 0
    errors_count: int = 0


@dataclass
class AgentHistory:
    """代理历史记录"""
    step: int
    action: str
    params: dict[str, Any]
    result: ActionResult
    state: BrowserState | None = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class StepResult:
    """步骤执行结果"""
    success: bool
    action_result: ActionResult | None = None
    error: str | None = None
    should_continue: bool = True
    state: BrowserState | None = None


class MessageManager:
    """消息管理器"""

    def __init__(
        self,
        task: str,
        system_prompt: str | None = None,
    ):
        """
        初始化消息管理器
        
        Args:
            task: 任务描述
            system_prompt: 系统提示词
        """
        self.task = task
        self.system_prompt = system_prompt or self._default_system_prompt()
        self._messages: list[dict[str, Any]] = []

    def _default_system_prompt(self) -> str:
        """默认系统提示词"""
        return """You are an intelligent browser automation agent. Your goal is to complete the user's task by interacting with web pages.

You can perform actions like:
- Navigate to URLs
- Click on elements
- Type text into input fields
- Scroll the page
- Extract information

Always think step by step and explain your reasoning before taking an action."""

    def build_initial_messages(self) -> list[dict[str, Any]]:
        """构建初始消息列表"""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Task: {self.task}"},
        ]

    def add_message(
        self,
        role: str,
        content: str,
        images: list[dict] | None = None,
    ) -> None:
        """添加消息"""
        message = {"role": role, "content": content}
        if images:
            message["images"] = images
        self._messages.append(message)

    def add_action_result(
        self,
        action: str,
        result: ActionResult,
    ) -> None:
        """添加动作结果消息"""
        content = f"Action: {action}\n"

        if result.success:
            content += "Result: Success\n"
            if result.extracted_content:
                content += f"Extracted: {result.extracted_content}\n"
        else:
            content += "Result: Failed\n"
            if result.error:
                content += f"Error: {result.error}\n"

        if result.is_done:
            content += "\nTask is marked as complete."

        self.add_message("assistant", content)

    def get_messages(self) -> list[dict[str, Any]]:
        """获取所有消息"""
        return self._messages.copy()

    def get_last_message(self) -> dict[str, Any] | None:
        """获取最后一条消息"""
        return self._messages[-1] if self._messages else None

    def clear(self) -> None:
        """清除消息历史"""
        self._messages.clear()


class BrowserAgent:
    """AI 驱动的浏览器代理"""

    def __init__(
        self,
        task: str,
        registry: Registry | None = None,
        event_bus: EventBus | None = None,
        state_manager: StateManager | None = None,
        loop_detector: LoopDetector | None = None,
        max_steps: int = 100,
        use_vision: bool = False,
        system_prompt: str | None = None,
    ):
        """
        初始化浏览器代理
        
        Args:
            task: 任务描述
            registry: 动作注册中心
            event_bus: 事件总线
            state_manager: 状态管理器
            loop_detector: 循环检测器
            max_steps: 最大步数
            use_vision: 是否使用视觉能力
            system_prompt: 系统提示词
        """
        self.task = task
        self.registry = registry or Registry()
        self.event_bus = event_bus or EventBus()
        self.state_manager = state_manager
        self.loop_detector = loop_detector or LoopDetector()

        self.max_steps = max_steps
        self.use_vision = use_vision

        self.message_manager = MessageManager(
            task=task,
            system_prompt=system_prompt,
        )

        self.status = AgentStatus(max_steps=max_steps)
        self._history: list[AgentHistory] = []
        self._llm_client: Any = None
        self._browser_session: Any = None

    def set_llm_client(self, client: Any) -> None:
        """设置 LLM 客户端"""
        self._llm_client = client

    def set_browser_session(self, session: Any) -> None:
        """设置浏览器会话"""
        self._browser_session = session

    async def run(self) -> ActionResult:
        """
        运行代理
        
        Returns:
            ActionResult: 最终结果
        """
        self.status.state = AgentState.RUNNING
        self.status.started_at = time.time()

        logger.info(f"Starting agent with task: {self.task}")

        try:
            while self.status.current_step < self.max_steps:
                self.status.current_step += 1

                step_result = await self._execute_step()

                if not step_result.should_continue:
                    self.status.state = AgentState.COMPLETED
                    return step_result.action_result or ActionResult(
                        is_done=True,
                        success=True,
                    )

                if step_result.action_result and step_result.action_result.is_done:
                    self.status.state = AgentState.COMPLETED
                    return step_result.action_result

                alerts = self.loop_detector.detect()
                if alerts:
                    for alert in alerts:
                        logger.warning(f"Loop detected: {alert.message}")
                        self.message_manager.add_message(
                            "system",
                            f"Warning: {alert.suggestion}",
                        )

                await asyncio.sleep(0.1)

            self.status.state = AgentState.COMPLETED
            return ActionResult(
                is_done=True,
                success=False,
                error=f"Max steps ({self.max_steps}) reached",
            )

        except Exception as e:
            self.status.state = AgentState.ERROR
            logger.error(f"Agent error: {e}")
            return ActionResult(
                is_done=True,
                success=False,
                error=str(e),
            )

    async def _execute_step(self) -> StepResult:
        """
        执行单步
        
        Returns:
            StepResult: 步骤结果
        """
        try:
            action, params = await self._get_next_action()

            if action is None:
                return StepResult(
                    success=False,
                    error="No action returned by LLM",
                    should_continue=True,
                )

            result = await self.registry.execute_action(
                action_name=action,
                params=params,
                browser_session=self._browser_session,
                agent=self,
            )

            self.status.actions_taken += 1

            if not result.success:
                self.status.errors_count += 1

            self._record_history(action, params, result)

            self.message_manager.add_action_result(action, result)

            state = None
            if self.state_manager:
                state = await self.state_manager.capture_state(
                    self._browser_session
                )
                self.loop_detector.record_page(
                    url=state.url or "",
                    title=state.title or "",
                    content=str(state.dom_state) if state.dom_state else "",
                    element_count=len(state.dom_state.elements) if state.dom_state else 0,
                    interactive_count=len(state.dom_state.get_interactive_elements()) if state.dom_state else 0,
                )

            return StepResult(
                success=result.success,
                action_result=result,
                should_continue=not result.is_done,
                state=state,
            )

        except Exception as e:
            logger.error(f"Step execution error: {e}")
            return StepResult(
                success=False,
                error=str(e),
                should_continue=True,
            )

    async def _get_next_action(self) -> tuple[str | None, dict[str, Any] | None]:
        """
        获取下一个动作
        
        Returns:
            (action_name, params) 元组
        """
        if self._llm_client is None:
            logger.warning("No LLM client set, returning default action")
            return "wait", {"seconds": 1}

        messages = self.message_manager.get_messages()

        action_schemas = self.registry.get_action_schemas()
        action_descriptions = self.registry.get_action_descriptions()

        tools = []
        for name, schema in action_schemas.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": action_descriptions.get(name, ""),
                    "parameters": schema,
                },
            })

        try:
            response = await self._llm_client.chat.completions.create(
                model=self._llm_client.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )

            choice = response.choices[0]

            if choice.message.tool_calls:
                tool_call = choice.message.tool_calls[0]
                action_name = tool_call.function.name
                params = json.loads(tool_call.function.arguments)
                return action_name, params

            content = choice.message.content or ""
            self.message_manager.add_message("assistant", content)

            return None, None

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None, None

    def _record_history(
        self,
        action: str,
        params: dict[str, Any],
        result: ActionResult,
    ) -> None:
        """记录历史"""
        state = None
        if self.state_manager:
            state = self.state_manager._current_state

        history = AgentHistory(
            step=self.status.current_step,
            action=action,
            params=params,
            result=result,
            state=state,
        )

        self._history.append(history)

    def get_history(self) -> list[AgentHistory]:
        """获取历史记录"""
        return self._history.copy()

    def get_last_n_history(self, n: int = 5) -> list[AgentHistory]:
        """获取最近 N 条历史记录"""
        return self._history[-n:] if len(self._history) >= n else self._history.copy()

    def pause(self) -> None:
        """暂停代理"""
        self.status.state = AgentState.PAUSED
        logger.info("Agent paused")

    def resume(self) -> None:
        """恢复代理"""
        if self.status.state == AgentState.PAUSED:
            self.status.state = AgentState.RUNNING
            logger.info("Agent resumed")

    def stop(self) -> None:
        """停止代理"""
        self.status.state = AgentState.COMPLETED
        logger.info("Agent stopped")

    def get_status(self) -> AgentStatus:
        """获取状态"""
        if self.status.started_at:
            self.status.elapsed_time = time.time() - self.status.started_at
        return self.status

    def reset(self) -> None:
        """重置代理"""
        self.status = AgentStatus(max_steps=self.max_steps)
        self._history.clear()
        self.message_manager.clear()
        self.loop_detector.reset()
        logger.info("Agent reset")
