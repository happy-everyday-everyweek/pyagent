"""Debug system for tool call tracking and thought chain logging."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolCallLog:
    """Log entry for a tool call."""

    id: str
    tool_name: str
    arguments: dict[str, Any]
    result: Any
    success: bool
    duration_ms: int
    timestamp: datetime = field(default_factory=datetime.now)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": str(self.result)[:500] if self.result else None,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


@dataclass
class ThoughtStep:
    """A single step in the thought chain."""

    id: str
    content: str
    step_type: str
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class Scratchpad:
    """Scratchpad for debugging and thought tracking."""

    def __init__(self, storage_path: str = "data/debug"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._tool_calls: list[ToolCallLog] = []
        self._thoughts: dict[str, ThoughtStep] = []
        self._session_id: str | None = None
        self._enabled: bool = True

    def start_session(self, session_id: str) -> None:
        self._session_id = session_id
        self._tool_calls = []
        self._thoughts = {}

    def end_session(self) -> dict[str, Any]:
        if not self._session_id:
            return {}

        report = self.generate_report()
        self._save_session(report)
        return report

    def log_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        success: bool,
        duration_ms: int,
        error: str | None = None,
    ) -> ToolCallLog:
        import uuid

        log_entry = ToolCallLog(
            id=str(uuid.uuid4()),
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
            duration_ms=duration_ms,
            error=error,
        )
        self._tool_calls.append(log_entry)
        logger.debug("Tool call: %s (%dms)", tool_name, duration_ms)
        return log_entry

    def add_thought(
        self,
        content: str,
        step_type: str = "reasoning",
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtStep:
        import uuid

        thought = ThoughtStep(
            id=str(uuid.uuid4()),
            content=content,
            step_type=step_type,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        self._thoughts[thought.id] = thought

        if parent_id and parent_id in self._thoughts:
            self._thoughts[parent_id].children.append(thought.id)

        return thought

    def get_thought_chain(self, root_id: str | None = None) -> list[ThoughtStep]:
        if root_id:
            root = self._thoughts.get(root_id)
            if not root:
                return []
            return self._build_chain(root)
        else:
            roots = [t for t in self._thoughts.values() if t.parent_id is None]
            chains = []
            for root in roots:
                chains.extend(self._build_chain(root))
            return chains

    def _build_chain(self, thought: ThoughtStep) -> list[ThoughtStep]:
        chain = [thought]
        for child_id in thought.children:
            if child_id in self._thoughts:
                chain.extend(self._build_chain(self._thoughts[child_id]))
        return chain

    def generate_report(self) -> dict[str, Any]:
        successful_calls = [c for c in self._tool_calls if c.success]
        failed_calls = [c for c in self._tool_calls if not c.success]
        total_duration = sum(c.duration_ms for c in self._tool_calls)

        return {
            "session_id": self._session_id,
            "timestamp": datetime.now().isoformat(),
            "tool_calls": {
                "total": len(self._tool_calls),
                "successful": len(successful_calls),
                "failed": len(failed_calls),
                "total_duration_ms": total_duration,
                "calls": [c.to_dict() for c in self._tool_calls],
            },
            "thoughts": {
                "total": len(self._thoughts),
                "chain": [
                    {"id": t.id, "content": t.content, "type": t.step_type}
                    for t in self.get_thought_chain()
                ],
            },
        }

    def _save_session(self, report: dict[str, Any]) -> None:
        if not self._session_id:
            return

        filepath = self._storage_path / f"{self._session_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Saved debug session to: %s", filepath)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def get_tool_call_stats(self) -> dict[str, Any]:
        if not self._tool_calls:
            return {"total": 0}

        by_tool: dict[str, list[ToolCallLog]] = {}
        for call in self._tool_calls:
            if call.tool_name not in by_tool:
                by_tool[call.tool_name] = []
            by_tool[call.tool_name].append(call)

        stats = {"total": len(self._tool_calls), "by_tool": {}}
        for tool_name, calls in by_tool.items():
            stats["by_tool"][tool_name] = {
                "count": len(calls),
                "success_rate": sum(1 for c in calls if c.success) / len(calls),
                "avg_duration_ms": sum(c.duration_ms for c in calls) / len(calls),
            }

        return stats


_scratchpad: Scratchpad | None = None


def get_scratchpad() -> Scratchpad:
    global _scratchpad
    if _scratchpad is None:
        _scratchpad = Scratchpad()
    return _scratchpad
