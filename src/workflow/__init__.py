"""Workflow engine for automation."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    WEBHOOK = "webhook"


class ActionType(Enum):
    HTTP_REQUEST = "http_request"
    SEND_MESSAGE = "send_message"
    EXECUTE_CODE = "execute_code"
    UPDATE_TODO = "update_todo"
    CALL_AGENT = "call_agent"
    CUSTOM = "custom"


@dataclass
class Trigger:
    id: str
    name: str
    trigger_type: TriggerType
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class Action:
    id: str
    name: str
    action_type: ActionType
    config: dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    triggers: list[Trigger] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class BaseActionHandler(ABC):
    @abstractmethod
    async def execute(self, action: Action, context: dict[str, Any]) -> dict[str, Any]:
        pass


class HttpRequestHandler(BaseActionHandler):
    async def execute(self, action: Action, context: dict[str, Any]) -> dict[str, Any]:
        import httpx

        config = action.config
        method = config.get("method", "GET")
        url = config.get("url", "")
        headers = config.get("headers", {})
        body = config.get("body")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=headers, json=body)
            return {"status_code": response.status_code, "body": response.text[:1000]}


class SendMessageHandler(BaseActionHandler):
    async def execute(self, action: Action, context: dict[str, Any]) -> dict[str, Any]:
        config = action.config
        platform = config.get("platform", "default")
        recipient = config.get("recipient", "")
        message = config.get("message", "")

        logger.info("Sending message to %s via %s: %s", recipient, platform, message[:50])
        return {"sent": True, "recipient": recipient}


class ExecuteCodeHandler(BaseActionHandler):
    async def execute(self, action: Action, context: dict[str, Any]) -> dict[str, Any]:
        config = action.config
        code = config.get("code", "")
        try:
            local_vars = {"context": context, "result": None}
            exec(code, {}, local_vars)
            return {"success": True, "result": str(local_vars.get("result", ""))}
        except Exception as e:
            return {"success": False, "error": str(e)}


class WorkflowEngine:
    def __init__(self):
        self._workflows: dict[str, Workflow] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._handlers: dict[ActionType, BaseActionHandler] = {
            ActionType.HTTP_REQUEST: HttpRequestHandler(),
            ActionType.SEND_MESSAGE: SendMessageHandler(),
            ActionType.EXECUTE_CODE: ExecuteCodeHandler(),
        }
        self._custom_handlers: dict[str, Callable] = {}
        self._scheduler_task: asyncio.Task | None = None

    def register_workflow(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow
        logger.info("Registered workflow: %s", workflow.name)

    def unregister_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        return list(self._workflows.values())

    def register_custom_handler(self, name: str, handler: Callable) -> None:
        self._custom_handlers[name] = handler

    async def execute(self, workflow_id: str, context: dict[str, Any] | None = None) -> WorkflowExecution:
        import uuid

        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if not workflow.enabled:
            raise ValueError(f"Workflow is disabled: {workflow_id}")

        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.now(),
        )
        self._executions[execution.id] = execution

        context = context or {}
        sorted_actions = sorted(workflow.actions, key=lambda a: a.order)

        for action in sorted_actions:
            try:
                handler = self._handlers.get(action.action_type)
                if handler:
                    result = await handler.execute(action, context)
                elif action.action_type == ActionType.CUSTOM:
                    custom_handler = self._custom_handlers.get(action.config.get("handler", ""))
                    if custom_handler:
                        result = await custom_handler(action, context)
                    else:
                        result = {"error": "Custom handler not found"}
                else:
                    result = {"error": "Unknown action type"}

                execution.results.append({"action_id": action.id, "result": result})

            except Exception as e:
                execution.results.append({"action_id": action.id, "error": str(e)})
                execution.status = "failed"
                execution.error = str(e)
                execution.completed_at = datetime.now()
                return execution

        execution.status = "completed"
        execution.completed_at = datetime.now()
        return execution

    def get_execution(self, execution_id: str) -> WorkflowExecution | None:
        return self._executions.get(execution_id)

    async def start_scheduler(self) -> None:
        self._scheduler_task = asyncio.create_task(self._schedule_loop())

    async def stop_scheduler(self) -> None:
        if self._scheduler_task:
            self._scheduler_task.cancel()
            self._scheduler_task = None

    async def _schedule_loop(self) -> None:
        while True:
            try:
                for workflow in self._workflows.values():
                    if not workflow.enabled:
                        continue
                    for trigger in workflow.triggers:
                        if trigger.trigger_type == TriggerType.SCHEDULE:
                            if self._should_trigger(trigger):
                                await self.execute(workflow.id)

                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler error: %s", e)
                await asyncio.sleep(60)

    def _should_trigger(self, trigger: Trigger) -> bool:
        import time

        config = trigger.config
        interval = config.get("interval", 3600)
        last_run = config.get("_last_run", 0)
        return time.time() - last_run >= interval


_engine: WorkflowEngine | None = None


def get_workflow_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
