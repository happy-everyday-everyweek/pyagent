import threading
from datetime import datetime
from typing import Optional, Callable, Set
from pathlib import Path
import json


class SaveManager:
    def __init__(
        self,
        auto_save_enabled: bool = True,
        auto_save_interval: int = 60,
        debounce_ms: int = 800,
    ):
        self._auto_save_enabled = auto_save_enabled
        self._auto_save_interval = auto_save_interval
        self._debounce_ms = debounce_ms
        self._last_save_time: Optional[datetime] = None
        self._is_dirty = False
        self._is_saving = False
        self._is_paused = False
        self._has_pending_save = False
        self._listeners: Set[Callable[[], None]] = set()
        self._save_timer: Optional[threading.Timer] = None
        self._auto_save_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    @property
    def auto_save_enabled(self) -> bool:
        return self._auto_save_enabled

    @auto_save_enabled.setter
    def auto_save_enabled(self, value: bool) -> None:
        self._auto_save_enabled = value
        if value:
            self._start_auto_save_timer()
        else:
            self._stop_auto_save_timer()

    @property
    def auto_save_interval(self) -> int:
        return self._auto_save_interval

    @auto_save_interval.setter
    def auto_save_interval(self, value: int) -> None:
        self._auto_save_interval = max(10, value)
        if self._auto_save_enabled:
            self._stop_auto_save_timer()
            self._start_auto_save_timer()

    @property
    def last_save_time(self) -> Optional[datetime]:
        return self._last_save_time

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @property
    def is_saving(self) -> bool:
        return self._is_saving

    def start(self) -> None:
        if self._auto_save_enabled:
            self._start_auto_save_timer()

    def stop(self) -> None:
        self._stop_auto_save_timer()
        self._clear_save_timer()

    def pause(self) -> None:
        self._is_paused = True
        self._clear_save_timer()

    def resume(self) -> None:
        self._is_paused = False
        if self._has_pending_save:
            self._queue_save()

    def mark_dirty(self) -> None:
        if self._is_paused:
            return
        self._is_dirty = True
        self._has_pending_save = True
        self._queue_save()
        self._notify()

    def save(self, project) -> bool:
        return self._save_now(project)

    def force_save(self, project) -> bool:
        self._has_pending_save = True
        return self._save_now(project)

    def _save_now(self, project) -> bool:
        with self._lock:
            if self._is_saving:
                return False
            if not self._has_pending_save:
                return True
            if self._is_paused:
                return False

            self._is_saving = True
            self._has_pending_save = False
            self._clear_save_timer()

        try:
            save_data = project.to_dict()
            save_path = Path("data/videos/projects") / f"{project.project_id}.json"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            self._last_save_time = datetime.now()
            self._is_dirty = False
            self._notify()
            return True
        except Exception:
            return False
        finally:
            self._is_saving = False
            if self._has_pending_save:
                self._queue_save()

    def _queue_save(self) -> None:
        if self._is_saving:
            return
        self._clear_save_timer()
        self._save_timer = threading.Timer(
            self._debounce_ms / 1000.0,
            self._on_debounce_timer,
        )
        self._save_timer.daemon = True
        self._save_timer.start()

    def _on_debounce_timer(self) -> None:
        pass

    def _start_auto_save_timer(self) -> None:
        self._stop_auto_save_timer()
        self._auto_save_timer = threading.Timer(
            self._auto_save_interval,
            self._on_auto_save_timer,
        )
        self._auto_save_timer.daemon = True
        self._auto_save_timer.start()

    def _stop_auto_save_timer(self) -> None:
        if self._auto_save_timer:
            self._auto_save_timer.cancel()
            self._auto_save_timer = None

    def _on_auto_save_timer(self) -> None:
        if self._is_dirty and self._auto_save_enabled:
            self._has_pending_save = True
        if self._auto_save_enabled:
            self._start_auto_save_timer()

    def _clear_save_timer(self) -> None:
        if self._save_timer:
            self._save_timer.cancel()
            self._save_timer = None

    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def _notify(self) -> None:
        for listener in self._listeners:
            listener()

    def get_status(self) -> dict:
        return {
            "auto_save_enabled": self._auto_save_enabled,
            "auto_save_interval": self._auto_save_interval,
            "last_save_time": self._last_save_time.isoformat() if self._last_save_time else None,
            "is_dirty": self._is_dirty,
            "is_saving": self._is_saving,
            "is_paused": self._is_paused,
            "has_pending_save": self._has_pending_save,
        }
