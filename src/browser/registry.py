"""
PyAgent 浏览器自动化模块 - 动作注册中心

提供动作注册、发现和执行功能，支持装饰器注册和依赖注入。
参考 browser-use 项目的 Registry 设计实现。
"""

import asyncio
import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
Context = TypeVar("Context")


@dataclass
class RegisteredAction:
    """注册的动作信息"""
    name: str
    description: str
    param_model: type[BaseModel] | None
    handler: Callable
    terminates_sequence: bool = False
    timeout: float | None = None
    retry_count: int = 0
    retry_delay: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ActionModel(BaseModel):
    """动作参数基类
    
    所有动作参数模型应继承此类。
    支持动态字段定义和 JSON Schema 生成。
    """

    def get_index(self) -> int | None:
        """获取元素索引（如果存在）"""
        return getattr(self, "index", None)

    def get_text(self) -> str | None:
        """获取文本内容（如果存在）"""
        return getattr(self, "text", None)


class ActionResult(BaseModel):
    """动作执行结果"""

    is_done: bool = False
    success: bool | None = None
    error: str | None = None
    extracted_content: str | None = None
    long_term_memory: str | None = None
    include_extracted_content_only_once: bool = False
    attachments: list[str] | None = None
    images: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """自定义序列化"""
        return super().model_dump(exclude_none=True, **kwargs)


class Registry:
    """动作注册中心"""

    def __init__(self, exclude_actions: list[str] | None = None):
        """
        初始化注册中心
        
        Args:
            exclude_actions: 要排除的动作名称列表
        """
        self._actions: dict[str, RegisteredAction] = {}
        self._exclude_actions: set[str] = set(exclude_actions or [])

    def action(
        self,
        description: str,
        param_model: type[BaseModel] | None = None,
        terminates_sequence: bool = False,
        timeout: float | None = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
        **metadata,
    ) -> Callable:
        """
        装饰器：注册动作
        
        Args:
            description: 动作描述（供 LLM 理解）
            param_model: 参数模型类
            terminates_sequence: 是否终止动作序列
            timeout: 执行超时时间（秒）
            retry_count: 重试次数
            retry_delay: 重试延迟（秒）
            **metadata: 额外元数据
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            action_name = func.__name__

            if action_name in self._exclude_actions:
                logger.debug(f"Action '{action_name}' is excluded, skipping registration")
                return func

            if param_model is None:
                NoParamsModel = create_model(
                    "NoParamsAction",
                    __base__=ActionModel,
                )
                actual_param_model = NoParamsModel
            else:
                actual_param_model = param_model

            registered = RegisteredAction(
                name=action_name,
                description=description,
                param_model=actual_param_model,
                handler=func,
                terminates_sequence=terminates_sequence,
                timeout=timeout,
                retry_count=retry_count,
                retry_delay=retry_delay,
                metadata=metadata,
            )

            self._actions[action_name] = registered
            logger.debug(f"Registered action: {action_name}")

            return func

        return decorator

    def get_action(self, name: str) -> RegisteredAction | None:
        """
        获取注册的动作
        
        Args:
            name: 动作名称
            
        Returns:
            RegisteredAction 或 None
        """
        return self._actions.get(name)

    def list_actions(self) -> list[str]:
        """获取所有注册的动作名称"""
        return list(self._actions.keys())

    def get_action_descriptions(self) -> dict[str, str]:
        """获取所有动作的描述"""
        return {
            name: action.description
            for name, action in self._actions.items()
        }

    def get_action_schemas(self) -> dict[str, dict]:
        """获取所有动作的 JSON Schema"""
        schemas = {}
        for name, action in self._actions.items():
            if action.param_model:
                schemas[name] = action.param_model.model_json_schema()
            else:
                schemas[name] = {"type": "object", "properties": {}}
        return schemas

    def exclude_action(self, name: str) -> None:
        """
        排除动作
        
        Args:
            name: 动作名称
        """
        if name in self._actions:
            del self._actions[name]
            logger.debug(f"Excluded action: {name}")

    def has_action(self, name: str) -> bool:
        """检查动作是否已注册"""
        return name in self._actions

    async def execute_action(
        self,
        action_name: str,
        params: dict[str, Any] | BaseModel | None = None,
        **dependencies,
    ) -> ActionResult:
        """
        执行动作
        
        Args:
            action_name: 动作名称
            params: 动作参数
            **dependencies: 依赖注入参数
            
        Returns:
            ActionResult: 执行结果
        """
        action = self.get_action(action_name)
        if action is None:
            return ActionResult(
                success=False,
                error=f"Unknown action: {action_name}",
            )

        if params is None:
            params = {}

        if isinstance(params, BaseModel):
            params_dict = params.model_dump()
        else:
            params_dict = params

        if action.param_model:
            try:
                validated_params = action.param_model(**params_dict)
            except Exception as e:
                return ActionResult(
                    success=False,
                    error=f"Parameter validation failed: {e}",
                )
        else:
            validated_params = None

        handler = action.handler
        sig = inspect.signature(handler)

        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == "params":
                if validated_params:
                    kwargs[param_name] = validated_params
                elif params_dict:
                    if hasattr(action.param_model, "__annotations__"):
                        kwargs[param_name] = action.param_model(**params_dict)
                    else:
                        kwargs[param_name] = params_dict
            elif param_name in dependencies:
                kwargs[param_name] = dependencies[param_name]
            elif param_name in params_dict:
                kwargs[param_name] = params_dict[param_name]

        retry_count = action.retry_count
        last_error = None

        for attempt in range(retry_count + 1):
            try:
                if asyncio.iscoroutinefunction(handler):
                    if action.timeout:
                        result = await asyncio.wait_for(
                            handler(**kwargs),
                            timeout=action.timeout,
                        )
                    else:
                        result = await handler(**kwargs)
                else:
                    result = handler(**kwargs)

                if isinstance(result, ActionResult):
                    return result
                if isinstance(result, str):
                    return ActionResult(extracted_content=result)
                if result is None:
                    return ActionResult()
                return ActionResult(extracted_content=str(result))

            except asyncio.TimeoutError:
                last_error = f"Action '{action_name}' timed out after {action.timeout}s"
                logger.warning(last_error)
            except Exception as e:
                last_error = str(e)
                logger.error(f"Action '{action_name}' failed: {e}")

            if attempt < retry_count:
                await asyncio.sleep(action.retry_delay)

        return ActionResult(
            success=False,
            error=last_error or f"Action '{action_name}' failed",
        )


class Tools:
    """工具类 - 提供统一的动作注册接口"""

    def __init__(
        self,
        exclude_actions: list[str] | None = None,
        output_model: type[BaseModel] | None = None,
    ):
        """
        初始化工具系统
        
        Args:
            exclude_actions: 要排除的动作列表
            output_model: 结构化输出模型
        """
        self.registry = Registry(exclude_actions)
        self._output_model = output_model
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """注册默认动作"""

        @self.registry.action("Wait for a specified number of seconds")
        async def wait(seconds: int = 3) -> ActionResult:
            actual_seconds = min(max(seconds, 0), 30)
            await asyncio.sleep(actual_seconds)
            return ActionResult(
                extracted_content=f"Waited for {seconds} seconds",
                long_term_memory=f"Waited for {seconds} seconds",
            )

        @self.registry.action("Complete the task with a message")
        async def done(text: str = "", success: bool = True) -> ActionResult:
            return ActionResult(
                is_done=True,
                success=success,
                extracted_content=text,
                long_term_memory=f"Task completed: {success} - {text[:100]}",
            )

    def action(self, description: str, **kwargs) -> Callable:
        """装饰器：注册自定义动作"""
        return self.registry.action(description, **kwargs)

    def exclude_action(self, name: str) -> None:
        """排除动作"""
        self.registry.exclude_action(name)

    async def act(
        self,
        action: ActionModel,
        **dependencies,
    ) -> ActionResult:
        """
        执行动作
        
        Args:
            action: 动作模型实例
            **dependencies: 依赖注入
            
        Returns:
            ActionResult: 执行结果
        """
        action_dict = action.model_dump(exclude_none=True)

        for action_name, params in action_dict.items():
            if params is not None:
                return await self.registry.execute_action(
                    action_name=action_name,
                    params=params,
                    **dependencies,
                )

        return ActionResult(
            success=False,
            error="No valid action found",
        )

    def get_action_schemas(self) -> dict[str, dict]:
        """获取所有动作的 Schema"""
        return self.registry.get_action_schemas()

    def get_action_descriptions(self) -> dict[str, str]:
        """获取所有动作的描述"""
        return self.registry.get_action_descriptions()


Controller = Tools
