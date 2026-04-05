"""
PyAgent 统一工具调用接口 - 工具基类

定义工具的生命周期、状态和统一调用接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolLifecycle(Enum):
    """工具生命周期阶段"""
    ACTIVATE = "activate"
    EXECUTE = "execute"
    DORMANT = "dormant"


class ToolState(Enum):
    """工具状态"""
    IDLE = "idle"
    ACTIVE = "active"
    DORMANT = "dormant"
    ERROR = "error"


@dataclass
class ToolContext:
    """工具执行上下文"""
    device_id: str = ""
    session_id: str = ""
    user_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "metadata": self.metadata
        }


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str = ""
    error: str = ""
    data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "data": self.data,
            "metadata": self.metadata
        }


class UnifiedTool(ABC):
    """统一工具抽象基类"""

    name: str = "unified_tool"
    description: str = "统一工具基类"

    def __init__(self, device_id: str = ""):
        self._state = ToolState.IDLE
        self._device_id = device_id
        self._last_error: str | None = None

    @property
    def state(self) -> ToolState:
        return self._state

    @property
    def device_id(self) -> str:
        return self._device_id

    @device_id.setter
    def device_id(self, value: str) -> None:
        self._device_id = value

    @abstractmethod
    async def activate(self, context: ToolContext) -> bool:
        """
        激活工具
        
        Args:
            context: 工具执行上下文
            
        Returns:
            激活是否成功
        """
        pass

    @abstractmethod
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            context: 工具执行上下文
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        pass

    @abstractmethod
    async def dormant(self, context: ToolContext) -> bool:
        """
        休眠工具
        
        Args:
            context: 工具执行上下文
            
        Returns:
            休眠是否成功
        """
        pass

    def _validate_state_transition(
        self,
        from_state: ToolState,
        to_state: ToolState,
        lifecycle: ToolLifecycle
    ) -> bool:
        """
        验证状态转换是否合法
        
        Args:
            from_state: 当前状态
            to_state: 目标状态
            lifecycle: 生命周期阶段
            
        Returns:
            状态转换是否合法
        """
        valid_transitions = {
            ToolLifecycle.ACTIVATE: {
                ToolState.IDLE: ToolState.ACTIVE,
                ToolState.ERROR: ToolState.ACTIVE
            },
            ToolLifecycle.EXECUTE: {
                ToolState.ACTIVE: ToolState.ACTIVE,
                ToolState.ACTIVE: ToolState.ERROR
            },
            ToolLifecycle.DORMANT: {
                ToolState.ACTIVE: ToolState.DORMANT,
                ToolState.ERROR: ToolState.DORMANT
            }
        }

        transitions = valid_transitions.get(lifecycle, {})
        return transitions.get(from_state) == to_state

    async def call(
        self,
        context: ToolContext | None = None,
        **kwargs
    ) -> ToolResult:
        """
        统一调用入口 - 实现三阶段调用流程
        
        Args:
            context: 工具执行上下文
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        if context is None:
            context = ToolContext(device_id=self._device_id)

        if self._device_id and not context.device_id:
            context.device_id = self._device_id

        try:
            if self._state == ToolState.DORMANT:
                return ToolResult(
                    success=False,
                    error=f"工具 {self.name} 处于休眠状态，无法调用"
                )

            if self._state == ToolState.ERROR:
                if not await self.activate(context):
                    return ToolResult(
                        success=False,
                        error=f"工具 {self.name} 激活失败"
                    )

            if self._state == ToolState.IDLE:
                if not await self.activate(context):
                    return ToolResult(
                        success=False,
                        error=f"工具 {self.name} 激活失败"
                    )

            if self._state != ToolState.ACTIVE:
                return ToolResult(
                    success=False,
                    error=f"工具 {self.name} 状态异常: {self._state.value}"
                )

            result = await self.execute(context, **kwargs)

            if not result.success:
                self._state = ToolState.ERROR
                self._last_error = result.error

            return result

        except Exception as e:
            self._state = ToolState.ERROR
            self._last_error = str(e)
            return ToolResult(
                success=False,
                error=f"工具 {self.name} 执行异常: {str(e)}"
            )

    async def sleep(self, context: ToolContext | None = None) -> bool:
        """
        将工具置于休眠状态
        
        Args:
            context: 工具执行上下文
            
        Returns:
            休眠是否成功
        """
        if context is None:
            context = ToolContext(device_id=self._device_id)

        if self._state == ToolState.DORMANT:
            return True

        if self._state not in (ToolState.ACTIVE, ToolState.ERROR):
            return False

        try:
            success = await self.dormant(context)
            if success:
                self._state = ToolState.DORMANT
            return success
        except Exception:
            return False

    async def wake(self, context: ToolContext | None = None) -> bool:
        """
        唤醒休眠中的工具
        
        Args:
            context: 工具执行上下文
            
        Returns:
            唤醒是否成功
        """
        if context is None:
            context = ToolContext(device_id=self._device_id)

        if self._state != ToolState.DORMANT:
            return True

        try:
            success = await self.activate(context)
            if success:
                self._state = ToolState.ACTIVE
                self._last_error = None
            return success
        except Exception:
            return False

    def reset(self) -> None:
        """重置工具状态"""
        self._state = ToolState.IDLE
        self._last_error = None

    def get_info(self) -> dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "state": self._state.value,
            "device_id": self._device_id,
            "last_error": self._last_error
        }
