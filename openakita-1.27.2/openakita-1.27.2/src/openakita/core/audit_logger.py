"""
L5: 持久化审计日志

将安全策略判定记录追加写入 JSONL 文件，
确保即使进程崩溃也不丢失审计记录。
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """Append-only JSONL audit logger for policy decisions."""

    def __init__(self, path: str = "data/audit/policy_decisions.jsonl") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        tool_name: str,
        decision: str,
        reason: str,
        policy: str = "",
        params_preview: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "ts": time.time(),
            "tool": tool_name,
            "decision": decision,
            "reason": reason,
            "policy": policy,
            "params": params_preview[:200],
        }
        if metadata:
            entry["meta"] = metadata
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[Audit] Failed to write audit log: {e}")

    def tail(self, n: int = 50) -> list[dict[str, Any]]:
        """Read the last *n* entries."""
        if not self._path.exists():
            return []
        try:
            lines = self._path.read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(line) for line in lines[-n:]]
        except Exception:
            return []


_global_audit: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    global _global_audit
    if _global_audit is None:
        try:
            from .policy import get_policy_engine
            cfg = get_policy_engine().config.self_protection
            _global_audit = AuditLogger(path=cfg.audit_path)
        except Exception:
            _global_audit = AuditLogger()
    return _global_audit
