"""
PyAgent 移动端模块 - 工作流自动化

提供工作流自动化功能，支持创建、执行、调度自动化任务。
v0.8.0: 新增工作流自动化支持

参考: Operit项目 Workflow模块
"""

import asyncio
import json
import logging
import subprocess
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowTriggerType(Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    CONDITION = "condition"


class WorkflowNodeType(Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    DELAY = "delay"
    LOOP = "loop"
    PARALLEL = "parallel"


class WorkflowStepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    id: str
    type: WorkflowNodeType
    name: str = ""
    description: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    position: tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "position": list(self.position),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowNode":
        return cls(
            id=data["id"],
            type=WorkflowNodeType(data["type"]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=data.get("config", {}),
            position=tuple(data.get("position", [0.0, 0.0])),
        )


@dataclass
class WorkflowConnection:
    id: str
    source_node_id: str
    target_node_id: str
    condition: str | None = None
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "condition": self.condition,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowConnection":
        return cls(
            id=data["id"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            condition=data.get("condition"),
            label=data.get("label", ""),
        )


@dataclass
class WorkflowTrigger:
    id: str
    type: WorkflowTriggerType
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "config": self.config,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowTrigger":
        return cls(
            id=data["id"],
            type=WorkflowTriggerType(data["type"]),
            config=data.get("config", {}),
            enabled=data.get("enabled", True),
        )


@dataclass
class WorkflowStep:
    id: str
    node_id: str
    name: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    result: Any = None
    error: str = ""
    start_time: float | None = None
    end_time: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.IDLE
    steps: list[WorkflowStep] = field(default_factory=list)
    current_step_index: int = 0
    start_time: float | None = None
    end_time: float | None = None
    error: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "current_step_index": self.current_step_index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error": self.error,
            "context": self.context,
        }


@dataclass
class Workflow:
    id: str
    name: str
    description: str = ""
    nodes: list[WorkflowNode] = field(default_factory=list)
    connections: list[WorkflowConnection] = field(default_factory=list)
    triggers: list[WorkflowTrigger] = field(default_factory=list)
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_execution: float | None = None
    execution_count: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "connections": [c.to_dict() for c in self.connections],
            "triggers": [t.to_dict() for t in self.triggers],
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_execution": self.last_execution,
            "execution_count": self.execution_count,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            nodes=[WorkflowNode.from_dict(n) for n in data.get("nodes", [])],
            connections=[WorkflowConnection.from_dict(c) for c in data.get("connections", [])],
            triggers=[WorkflowTrigger.from_dict(t) for t in data.get("triggers", [])],
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            last_execution=data.get("last_execution"),
            execution_count=data.get("execution_count", 0),
            tags=data.get("tags", []),
        )


@dataclass
class WorkflowConfig:
    data_dir: str = "data/mobile/workflows"
    max_concurrent_executions: int = 5
    execution_timeout_seconds: int = 300
    step_timeout_seconds: int = 60
    auto_save: bool = True
    schedule_check_interval: float = 60.0


class WorkflowAutomation:
    _instance: Optional["WorkflowAutomation"] = None
    _lock = threading.Lock()

    def __new__(cls, config: WorkflowConfig | None = None) -> "WorkflowAutomation":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: WorkflowConfig | None = None):
        if self._initialized:
            return

        self._config = config or WorkflowConfig()
        self._workflows: dict[str, Workflow] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._running_executions: dict[str, asyncio.Task] = {}
        self._scheduled_tasks: dict[str, asyncio.Task] = {}
        self._action_handlers: dict[str, Callable] = {}
        self._event_handlers: dict[str, list[Callable]] = {}
        self._scheduler_running: bool = False
        self._scheduler_task: asyncio.Task | None = None
        self._execution_lock = asyncio.Lock()
        self._initialized = True

        self._register_default_actions()
        self._load_workflows()

    def _register_default_actions(self) -> None:
        self._action_handlers["log"] = self._action_log
        self._action_handlers["delay"] = self._action_delay
        self._action_handlers["set_variable"] = self._action_set_variable
        self._action_handlers["condition"] = self._action_condition
        self._action_handlers["http_request"] = self._action_http_request
        self._action_handlers["shell_command"] = self._action_shell_command
        self._action_handlers["notification"] = self._action_notification
        self._action_handlers["launch_app"] = self._action_launch_app
        self._action_handlers["stop_app"] = self._action_stop_app

    def _load_workflows(self) -> None:
        data_dir = Path(self._config.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        for workflow_file in data_dir.glob("*.json"):
            try:
                with open(workflow_file, encoding="utf-8") as f:
                    data = json.load(f)
                workflow = Workflow.from_dict(data)
                self._workflows[workflow.id] = workflow
                logger.info(f"Loaded workflow: {workflow.name} ({workflow.id})")
            except Exception as e:
                logger.error(f"Failed to load workflow {workflow_file}: {e}")

    def _save_workflow(self, workflow: Workflow) -> bool:
        if not self._config.auto_save:
            return True

        try:
            data_dir = Path(self._config.data_dir)
            data_dir.mkdir(parents=True, exist_ok=True)

            workflow_file = data_dir / f"{workflow.id}.json"
            with open(workflow_file, "w", encoding="utf-8") as f:
                json.dump(workflow.to_dict(), f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved workflow: {workflow.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return False

    @property
    def config(self) -> WorkflowConfig:
        return self._config

    def create_workflow(
        self,
        name: str,
        steps: list[dict[str, Any]],
        description: str = "",
        triggers: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
    ) -> Workflow:
        workflow_id = str(uuid.uuid4())
        nodes: list[WorkflowNode] = []
        connections: list[WorkflowConnection] = []
        trigger_list: list[WorkflowTrigger] = []

        trigger_node = WorkflowNode(
            id=f"trigger_{uuid.uuid4().hex[:8]}",
            type=WorkflowNodeType.TRIGGER,
            name="Start",
            description="Workflow trigger",
        )
        nodes.append(trigger_node)

        prev_node_id = trigger_node.id
        for i, step in enumerate(steps):
            node = WorkflowNode(
                id=f"node_{i}_{uuid.uuid4().hex[:8]}",
                type=WorkflowNodeType.ACTION,
                name=step.get("name", f"Step {i + 1}"),
                description=step.get("description", ""),
                config={
                    "action": step.get("action", ""),
                    "params": step.get("params", {}),
                },
                position=(i * 200.0, 0.0),
            )
            nodes.append(node)

            connection = WorkflowConnection(
                id=f"conn_{uuid.uuid4().hex[:8]}",
                source_node_id=prev_node_id,
                target_node_id=node.id,
            )
            connections.append(connection)
            prev_node_id = node.id

        if triggers:
            for trigger_data in triggers:
                trigger = WorkflowTrigger(
                    id=f"trigger_{uuid.uuid4().hex[:8]}",
                    type=WorkflowTriggerType(trigger_data.get("type", "manual")),
                    config=trigger_data.get("config", {}),
                    enabled=trigger_data.get("enabled", True),
                )
                trigger_list.append(trigger)

        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            nodes=nodes,
            connections=connections,
            triggers=trigger_list,
            tags=tags or [],
        )

        self._workflows[workflow_id] = workflow
        self._save_workflow(workflow)

        logger.info(f"Created workflow: {name} ({workflow_id})")
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def list_workflows(self, enabled_only: bool = False) -> list[Workflow]:
        workflows = list(self._workflows.values())
        if enabled_only:
            workflows = [w for w in workflows if w.enabled]
        return workflows

    def update_workflow(self, workflow_id: str, **kwargs) -> bool:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False

        for key, value in kwargs.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)

        workflow.updated_at = time.time()
        self._save_workflow(workflow)

        logger.info(f"Updated workflow: {workflow.name}")
        return True

    def delete_workflow(self, workflow_id: str) -> bool:
        workflow = self._workflows.pop(workflow_id, None)
        if not workflow:
            return False

        try:
            workflow_file = Path(self._config.data_dir) / f"{workflow_id}.json"
            if workflow_file.exists():
                workflow_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete workflow file: {e}")

        if workflow_id in self._scheduled_tasks:
            self._scheduled_tasks[workflow_id].cancel()
            del self._scheduled_tasks[workflow_id]

        logger.info(f"Deleted workflow: {workflow.name}")
        return True

    async def execute_workflow(
        self,
        workflow_id: str,
        context: dict[str, Any] | None = None,
        on_step_complete: Callable[[WorkflowStep], None] | None = None,
    ) -> WorkflowExecution:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if not workflow.enabled:
            raise ValueError(f"Workflow is disabled: {workflow.name}")

        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            context=context or {},
        )

        for node in workflow.nodes:
            if node.type == WorkflowNodeType.TRIGGER:
                continue
            step = WorkflowStep(
                id=f"step_{uuid.uuid4().hex[:8]}",
                node_id=node.id,
                name=node.name,
                action=node.config.get("action", ""),
                params=node.config.get("params", {}),
            )
            execution.steps.append(step)

        self._executions[execution_id] = execution

        async with self._execution_lock:
            if len(self._running_executions) >= self._config.max_concurrent_executions:
                raise RuntimeError("Maximum concurrent executions reached")

            task = asyncio.create_task(
                self._execute_workflow_internal(
                    workflow, execution, on_step_complete
                )
            )
            self._running_executions[execution_id] = task

        try:
            await task
        finally:
            self._running_executions.pop(execution_id, None)
            workflow.last_execution = time.time()
            workflow.execution_count += 1
            self._save_workflow(workflow)

        return execution

    async def _execute_workflow_internal(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        on_step_complete: Callable[[WorkflowStep], None] | None,
    ) -> None:
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = time.time()

        logger.info(f"Starting workflow execution: {workflow.name} ({execution.id})")

        try:
            node_map = {n.id: n for n in workflow.nodes}
            connection_map: dict[str, list[WorkflowConnection]] = {}
            for conn in workflow.connections:
                if conn.source_node_id not in connection_map:
                    connection_map[conn.source_node_id] = []
                connection_map[conn.source_node_id].append(conn)

            trigger_nodes = [n for n in workflow.nodes if n.type == WorkflowNodeType.TRIGGER]
            if not trigger_nodes:
                raise ValueError("No trigger node found in workflow")

            current_nodes = [trigger_nodes[0].id]
            executed_nodes: set[str] = set()

            while current_nodes:
                for node_id in current_nodes:
                    if node_id in executed_nodes:
                        continue

                    node = node_map.get(node_id)
                    if not node:
                        continue

                    step = next(
                        (s for s in execution.steps if s.node_id == node_id),
                        None,
                    )

                    if step:
                        try:
                            step.status = WorkflowStepStatus.RUNNING
                            step.start_time = time.time()

                            result = await self._execute_node(node, execution.context)

                            step.end_time = time.time()
                            step.result = result
                            step.status = WorkflowStepStatus.SUCCESS

                            if on_step_complete:
                                on_step_complete(step)

                        except Exception as e:
                            step.end_time = time.time()
                            step.error = str(e)
                            step.status = WorkflowStepStatus.FAILED
                            execution.error = str(e)

                            if on_step_complete:
                                on_step_complete(step)

                            execution.status = WorkflowStatus.FAILED
                            execution.end_time = time.time()
                            logger.error(f"Workflow execution failed: {e}")
                            return

                    executed_nodes.add(node_id)

                next_nodes = []
                for node_id in current_nodes:
                    for conn in connection_map.get(node_id, []):
                        if conn.target_node_id not in executed_nodes:
                            if conn.condition:
                                if not self._evaluate_condition(
                                    conn.condition, execution.context
                                ):
                                    continue
                            next_nodes.append(conn.target_node_id)

                current_nodes = list(set(next_nodes))

            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = time.time()
            logger.info(
                f"Workflow execution completed: {workflow.name} "
                f"(duration: {execution.end_time - (execution.start_time or 0):.2f}s)"
            )

        except asyncio.CancelledError:
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = time.time()
            logger.info(f"Workflow execution cancelled: {workflow.name}")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.end_time = time.time()
            logger.error(f"Workflow execution error: {e}")

    async def _execute_node(
        self,
        node: WorkflowNode,
        context: dict[str, Any],
    ) -> Any:
        if node.type == WorkflowNodeType.TRIGGER:
            return None

        if node.type == WorkflowNodeType.DELAY:
            delay_seconds = node.config.get("seconds", 1)
            await asyncio.sleep(delay_seconds)
            return None

        if node.type == WorkflowNodeType.CONDITION:
            condition = node.config.get("condition", "")
            return self._evaluate_condition(condition, context)

        action = node.config.get("action", "")
        params = node.config.get("params", {})

        resolved_params = self._resolve_params(params, context)

        handler = self._action_handlers.get(action)
        if handler:
            if asyncio.iscoroutinefunction(handler):
                return await handler(resolved_params, context)
            return handler(resolved_params, context)

        logger.warning(f"No handler for action: {action}")
        return None

    def _resolve_params(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = context.get(var_name, value)
            else:
                resolved[key] = value
        return resolved

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        try:
            condition = condition.strip()
            if not condition:
                return True

            if condition.lower() in ("true", "1", "yes"):
                return True
            if condition.lower() in ("false", "0", "no"):
                return False

            return bool(eval(condition, {"__builtins__": {}}, context))

        except Exception as e:
            logger.warning(f"Condition evaluation failed: {condition}, error: {e}")
            return False

    async def _action_log(self, params: dict[str, Any], context: dict[str, Any]) -> Any:
        message = params.get("message", "")
        level = params.get("level", "info")

        log_msg = f"[Workflow] {message}"
        if level == "debug":
            logger.debug(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
        elif level == "error":
            logger.error(log_msg)
        else:
            logger.info(log_msg)

        return message

    async def _action_delay(self, params: dict[str, Any], context: dict[str, Any]) -> Any:
        seconds = params.get("seconds", 1)
        await asyncio.sleep(seconds)
        return None

    async def _action_set_variable(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        name = params.get("name", "")
        value = params.get("value")
        if name:
            context[name] = value
        return value

    async def _action_condition(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        condition = params.get("condition", "")
        return self._evaluate_condition(condition, context)

    async def _action_http_request(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        import aiohttp

        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        body = params.get("body")
        timeout = params.get("timeout", 30)

        try:
            async with aiohttp.ClientSession() as session, session.request(
                method,
                url,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if isinstance(body, str) else None,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                result = {
                    "status": response.status,
                    "headers": dict(response.headers),
                }
                try:
                    result["body"] = await response.json()
                except Exception:
                    result["body"] = await response.text()
                return result

        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return {"error": str(e)}

    async def _action_shell_command(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:

        command = params.get("command", "")
        timeout = params.get("timeout", 30)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {"error": "Command timeout"}
        except Exception as e:
            return {"error": str(e)}

    async def _action_notification(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        title = params.get("title", "")
        message = params.get("message", "")

        logger.info(f"Notification: {title} - {message}")
        return {"title": title, "message": message}

    async def _action_launch_app(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        package_name = params.get("package_name", "")

        try:
            from src.mobile.package_manager import package_manager

            success = package_manager.launch_package(package_name)
            return {"success": success, "package_name": package_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_stop_app(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        package_name = params.get("package_name", "")

        try:
            from src.mobile.package_manager import package_manager

            success = package_manager.force_stop(package_name)
            return {"success": success, "package_name": package_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def schedule_workflow(
        self,
        workflow_id: str,
        trigger: dict[str, Any],
    ) -> bool:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return False

        trigger_type = WorkflowTriggerType(trigger.get("type", "schedule"))
        trigger_config = trigger.get("config", {})

        new_trigger = WorkflowTrigger(
            id=f"trigger_{uuid.uuid4().hex[:8]}",
            type=trigger_type,
            config=trigger_config,
            enabled=True,
        )

        workflow.triggers.append(new_trigger)
        self._save_workflow(workflow)

        if trigger_type == WorkflowTriggerType.SCHEDULE:
            self._schedule_workflow_task(workflow_id, new_trigger)

        logger.info(f"Scheduled workflow: {workflow.name}")
        return True

    def _schedule_workflow_task(
        self,
        workflow_id: str,
        trigger: WorkflowTrigger,
    ) -> None:
        async def schedule_runner():
            while trigger.enabled:
                try:
                    interval = trigger.config.get("interval_seconds", 60)
                    await asyncio.sleep(interval)

                    workflow = self._workflows.get(workflow_id)
                    if workflow and workflow.enabled:
                        await self.execute_workflow(workflow_id)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Schedule runner error: {e}")
                    await asyncio.sleep(60)

        if workflow_id in self._scheduled_tasks:
            self._scheduled_tasks[workflow_id].cancel()

        self._scheduled_tasks[workflow_id] = asyncio.create_task(schedule_runner())

    def cancel_workflow(self, workflow_id: str) -> bool:
        cancelled = False

        for execution_id, task in list(self._running_executions.items()):
            execution = self._executions.get(execution_id)
            if execution and execution.workflow_id == workflow_id:
                task.cancel()
                cancelled = True

        if workflow_id in self._scheduled_tasks:
            self._scheduled_tasks[workflow_id].cancel()
            del self._scheduled_tasks[workflow_id]
            cancelled = True

        logger.info(f"Cancelled workflow: {workflow_id}")
        return cancelled

    def get_execution(self, execution_id: str) -> WorkflowExecution | None:
        return self._executions.get(execution_id)

    def list_executions(
        self,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
    ) -> list[WorkflowExecution]:
        executions = list(self._executions.values())

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        if status:
            executions = [e for e in executions if e.status == status]

        return executions

    def register_action(
        self,
        action_name: str,
        handler: Callable,
    ) -> None:
        self._action_handlers[action_name] = handler
        logger.info(f"Registered action: {action_name}")

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable,
    ) -> None:
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler: {event_type}")

    async def trigger_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
    ) -> None:
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

        for workflow in self._workflows.values():
            if not workflow.enabled:
                continue

            for trigger in workflow.triggers:
                if trigger.type == WorkflowTriggerType.EVENT and trigger.enabled:
                    event_filter = trigger.config.get("event_type")
                    if event_filter == event_type or event_filter == "*":
                        try:
                            await self.execute_workflow(
                                workflow.id,
                                context={"event": event_data},
                            )
                        except Exception as e:
                            logger.error(f"Event-triggered workflow error: {e}")

    def start_scheduler(self) -> None:
        if self._scheduler_running:
            return

        self._scheduler_running = True

        for workflow in self._workflows.values():
            for trigger in workflow.triggers:
                if trigger.type == WorkflowTriggerType.SCHEDULE and trigger.enabled:
                    self._schedule_workflow_task(workflow.id, trigger)

        logger.info("Workflow scheduler started")

    def stop_scheduler(self) -> None:
        self._scheduler_running = False

        for task in self._scheduled_tasks.values():
            task.cancel()
        self._scheduled_tasks.clear()

        logger.info("Workflow scheduler stopped")

    def cleanup(self) -> None:
        self.stop_scheduler()

        for task in self._running_executions.values():
            task.cancel()
        self._running_executions.clear()

        self._workflows.clear()
        self._executions.clear()
        self._action_handlers.clear()
        self._event_handlers.clear()

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance:
            cls._instance.cleanup()
            cls._instance = None


workflow_automation = WorkflowAutomation()
