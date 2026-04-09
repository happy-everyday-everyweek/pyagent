"""Browser action recording and playback system.

This module provides functionality to record browser interactions
and replay them automatically.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of browser actions that can be recorded."""

    NAVIGATE = "navigate"
    CLICK = "click"
    INPUT = "input"
    SCROLL = "scroll"
    SELECT = "select"
    HOVER = "hover"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"
    CUSTOM = "custom"


@dataclass
class RecordedAction:
    """A single recorded browser action."""

    action_type: ActionType
    timestamp: str
    params: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    selector: str | None = None
    element_description: str | None = None
    screenshot: str | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "timestamp": self.timestamp,
            "params": self.params,
            "result": self.result,
            "selector": self.selector,
            "element_description": self.element_description,
            "screenshot": self.screenshot,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecordedAction":
        return cls(
            action_type=ActionType(data["action_type"]),
            timestamp=data["timestamp"],
            params=data.get("params", {}),
            result=data.get("result", {}),
            selector=data.get("selector"),
            element_description=data.get("element_description"),
            screenshot=data.get("screenshot"),
            duration_ms=data.get("duration_ms", 0),
        )


@dataclass
class RecordingSession:
    """A recording session containing multiple actions."""

    name: str
    start_time: str
    end_time: str | None = None
    actions: list[RecordedAction] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "actions": [a.to_dict() for a in self.actions],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecordingSession":
        return cls(
            name=data["name"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            actions=[RecordedAction.from_dict(a) for a in data.get("actions", [])],
            metadata=data.get("metadata", {}),
        )


class BrowserRecorder:
    """Records browser interactions for later playback.

    Usage:
        recorder = BrowserRecorder()

        with recorder.session("login_flow"):
            recorder.record(ActionType.NAVIGATE, {"url": "https://example.com"})
            recorder.record(ActionType.INPUT, {"selector": "#username", "text": "user"})
            recorder.record(ActionType.CLICK, {"selector": "#submit"})

        recorder.save("recordings/login_flow.json")
    """

    def __init__(self, storage_dir: str = "data/recordings"):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._current_session: RecordingSession | None = None
        self._sessions: dict[str, RecordingSession] = {}

    def session(self, name: str, metadata: dict[str, Any] | None = None) -> "SessionContext":
        """Start a new recording session.

        Args:
            name: Session name.
            metadata: Optional metadata for the session.

        Returns:
            Session context manager.
        """
        return SessionContext(self, name, metadata)

    def start_session(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Start a new recording session.

        Args:
            name: Session name.
            metadata: Optional metadata.
        """
        if self._current_session:
            self.end_session()

        self._current_session = RecordingSession(
            name=name,
            start_time=datetime.now().isoformat(),
            metadata=metadata or {},
        )
        logger.info("Started recording session: %s", name)

    def end_session(self) -> RecordingSession | None:
        """End the current recording session.

        Returns:
            The completed session or None if no session was active.
        """
        if not self._current_session:
            return None

        self._current_session.end_time = datetime.now().isoformat()
        session = self._current_session
        self._sessions[session.name] = session
        self._current_session = None

        logger.info(
            "Ended recording session: %s (%d actions)",
            session.name,
            len(session.actions),
        )
        return session

    def record(
        self,
        action_type: ActionType,
        params: dict[str, Any],
        selector: str | None = None,
        element_description: str | None = None,
        result: dict[str, Any] | None = None,
        screenshot: str | None = None,
        duration_ms: int = 0,
    ) -> None:
        """Record a browser action.

        Args:
            action_type: Type of action.
            params: Action parameters.
            selector: CSS selector for the target element.
            element_description: Human-readable description of the element.
            result: Result of the action.
            screenshot: Base64-encoded screenshot (optional).
            duration_ms: Duration of the action in milliseconds.
        """
        if not self._current_session:
            logger.warning("No active recording session, action not recorded")
            return

        action = RecordedAction(
            action_type=action_type,
            timestamp=datetime.now().isoformat(),
            params=params,
            result=result or {},
            selector=selector,
            element_description=element_description,
            screenshot=screenshot,
            duration_ms=duration_ms,
        )
        self._current_session.actions.append(action)

    def save(self, filename: str) -> Path:
        """Save a recording session to file.

        Args:
            filename: Output filename (without extension).

        Returns:
            Path to the saved file.
        """
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = self._storage_dir / filename

        sessions_to_save = list(self._sessions.values())
        if self._current_session:
            sessions_to_save.append(self._current_session)

        data = {
            "version": "1.0",
            "sessions": [s.to_dict() for s in sessions_to_save],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("Saved recording to: %s", filepath)
        return filepath

    def load(self, filename: str) -> list[RecordingSession]:
        """Load recording sessions from file.

        Args:
            filename: Input filename (without extension).

        Returns:
            List of loaded sessions.
        """
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = self._storage_dir / filename

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        sessions = [RecordingSession.from_dict(s) for s in data.get("sessions", [])]
        for session in sessions:
            self._sessions[session.name] = session

        logger.info("Loaded %d sessions from: %s", len(sessions), filepath)
        return sessions

    def get_session(self, name: str) -> RecordingSession | None:
        """Get a recorded session by name.

        Args:
            name: Session name.

        Returns:
            The session or None if not found.
        """
        return self._sessions.get(name)

    def list_sessions(self) -> list[str]:
        """List all recorded session names.

        Returns:
            List of session names.
        """
        return list(self._sessions.keys())


class SessionContext:
    """Context manager for recording sessions."""

    def __init__(
        self,
        recorder: BrowserRecorder,
        name: str,
        metadata: dict[str, Any] | None = None,
    ):
        self._recorder = recorder
        self._name = name
        self._metadata = metadata

    def __enter__(self) -> "BrowserRecorder":
        self._recorder.start_session(self._name, self._metadata)
        return self._recorder

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._recorder.end_session()


class BrowserPlayer:
    """Plays back recorded browser actions.

    Usage:
        recorder = BrowserRecorder()
        recorder.load("login_flow")

        player = BrowserPlayer(browser_controller)
        await player.play("login_flow")
    """

    def __init__(self, browser_controller: Any):
        self._browser = browser_controller
        self._speed = 1.0
        self._stop_on_error = True
        self._variable_substitutions: dict[str, str] = {}

    def set_speed(self, speed: float) -> None:
        """Set playback speed multiplier.

        Args:
            speed: Speed multiplier (1.0 = normal, 2.0 = double speed).
        """
        self._speed = speed

    def set_stop_on_error(self, stop: bool) -> None:
        """Set whether to stop on errors.

        Args:
            stop: True to stop on errors, False to continue.
        """
        self._stop_on_error = stop

    def set_variable(self, name: str, value: str) -> None:
        """Set a variable for substitution during playback.

        Args:
            name: Variable name (e.g., "username").
            value: Variable value.
        """
        self._variable_substitutions[name] = value

    def set_variables(self, variables: dict[str, str]) -> None:
        """Set multiple variables for substitution.

        Args:
            variables: Dictionary of variable names and values.
        """
        self._variable_substitutions.update(variables)

    def _substitute(self, value: str) -> str:
        """Apply variable substitutions to a value.

        Args:
            value: String value with potential {{variable}} placeholders.

        Returns:
            Substituted string.
        """
        result = value
        for name, replacement in self._variable_substitutions.items():
            result = result.replace(f"{{{{{name}}}}}", replacement)
        return result

    async def play(self, session: RecordingSession) -> dict[str, Any]:
        """Play back a recorded session.

        Args:
            session: Recording session to play.

        Returns:
            Playback result with success status and any errors.
        """
        results = []
        errors = []

        for i, action in enumerate(session.actions):
            try:
                result = await self._execute_action(action)
                results.append({"action": i, "success": True, "result": result})
            except Exception as e:
                error_info = {"action": i, "success": False, "error": str(e)}
                errors.append(error_info)
                results.append(error_info)

                if self._stop_on_error:
                    break

        return {
            "session_name": session.name,
            "total_actions": len(session.actions),
            "executed_actions": len(results),
            "success_count": len(results) - len(errors),
            "error_count": len(errors),
            "results": results,
        }

    async def _execute_action(self, action: RecordedAction) -> dict[str, Any]:
        """Execute a single recorded action.

        Args:
            action: Action to execute.

        Returns:
            Execution result.
        """
        params = {}
        for key, value in action.params.items():
            if isinstance(value, str):
                params[key] = self._substitute(value)
            else:
                params[key] = value

        if action.action_type == ActionType.NAVIGATE:
            return await self._browser.navigate(params.get("url", ""))

        if action.action_type == ActionType.CLICK:
            selector = action.selector or params.get("selector")
            if selector:
                return await self._browser.click(selector)
            return await self._browser.click_at(params.get("x", 0), params.get("y", 0))

        if action.action_type == ActionType.INPUT:
            selector = action.selector or params.get("selector")
            text = params.get("text", "")
            if selector:
                return await self._browser.input_text(selector, text)
            raise ValueError("Input action requires a selector")

        if action.action_type == ActionType.SCROLL:
            direction = params.get("direction", "down")
            amount = params.get("amount", 300)
            return await self._browser.scroll(direction, amount)

        if action.action_type == ActionType.WAIT:
            duration = params.get("duration", 1.0) / self._speed
            import asyncio

            await asyncio.sleep(duration)
            return {"waited": duration}

        if action.action_type == ActionType.SCREENSHOT:
            return await self._browser.screenshot()

        if action.action_type == ActionType.EXTRACT:
            selector = action.selector or params.get("selector")
            return await self._browser.extract(selector)

        raise ValueError(f"Unknown action type: {action.action_type}")
