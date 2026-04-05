"""
PyAgent Mate模式

在Web UI上开启该模式后：
- 支持实时状态同步
- 支持协作模式开关
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .types import MateModeState


class MateModeManager:
    """Mate模式管理器"""

    def __init__(self, data_dir: str = "data/mate_mode"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.state = MateModeState()
        self._load_state()

    def _get_state_file(self) -> Path:
        return self.data_dir / "mate_state.json"

    def _load_state(self) -> None:
        file_path = self._get_state_file()
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self.state = MateModeState.from_dict(data.get("state", {}))
            except Exception:
                pass

    def _save_state(self) -> None:
        file_path = self._get_state_file()
        try:
            data = {
                "state": self.state.to_dict(),
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def enable(self) -> None:
        self.state.enabled = True
        self._save_state()

    def disable(self) -> None:
        self.state.enabled = False
        self._save_state()

    def toggle(self) -> bool:
        self.state.enabled = not self.state.enabled
        self._save_state()
        return self.state.enabled

    def is_enabled(self) -> bool:
        return self.state.enabled

    def set_collaboration_mode(self, enabled: bool) -> None:
        self.state.collaboration_enabled = enabled
        self._save_state()

    def is_collaboration_enabled(self) -> bool:
        return self.state.collaboration_enabled

    def get_state(self) -> MateModeState:
        return self.state

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.state.enabled,
            "collaboration_enabled": self.state.collaboration_enabled,
        }


mate_mode_manager = MateModeManager()
