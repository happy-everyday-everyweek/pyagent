"""
Logs routes:
- GET  /api/logs/service   — 后端服务日志尾部
- POST /api/logs/frontend  — 前端日志上报（Web/Capacitor 模式）
- GET  /api/logs/frontend  — 前端日志尾部
- GET  /api/logs/combined  — 合并返回前后端日志（供日志导出）

远程模式下，前端通过这些 API 获取/上报日志，替代 Tauri 本地文件读取。
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Frontend log file settings ──
_FRONTEND_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_FRONTEND_LOG_BACKUP_COUNT = 5
_frontend_log_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _log_file_path() -> Path:
    """Return the main service log file path from settings."""
    try:
        from openakita.config import settings

        return settings.log_file_path
    except Exception:
        return Path.cwd() / "logs" / "openakita.log"


def _frontend_log_path() -> Path:
    """Return the frontend log file path."""
    try:
        from openakita.config import settings

        return settings.log_dir_path / "frontend.log"
    except Exception:
        return Path.cwd() / "logs" / "frontend.log"


def _read_log_tail(log_path: Path, tail_bytes: int) -> dict:
    """Read the tail of a log file. Shared logic for service/frontend log reading."""
    path_str = str(log_path)
    if not log_path.exists():
        return {"path": path_str, "content": "", "truncated": False}
    try:
        file_size = log_path.stat().st_size
        start = max(0, file_size - tail_bytes)
        truncated = start > 0
        with open(log_path, "rb") as f:
            if start > 0:
                f.seek(start)
            raw = f.read()
        content = raw.decode("utf-8", errors="replace")
        return {"path": path_str, "content": content, "truncated": truncated}
    except Exception as e:
        logger.error("Failed to read log %s: %s", log_path, e)
        return {"path": path_str, "content": "", "truncated": False, "error": str(e)}


def _rotate_frontend_log(path: Path) -> None:
    """Simple size-based rotation: frontend.log → frontend.log.1 → .2 …"""
    if not path.exists():
        return
    try:
        if path.stat().st_size < _FRONTEND_LOG_MAX_BYTES:
            return
    except OSError:
        return

    # Shift existing backups: .4→delete, .3→.4, .2→.3, .1→.2
    for i in range(_FRONTEND_LOG_BACKUP_COUNT, 0, -1):
        old = path.parent / f"{path.name}.{i}"
        if i == _FRONTEND_LOG_BACKUP_COUNT:
            old.unlink(missing_ok=True)
        elif old.exists():
            old.rename(path.parent / f"{path.name}.{i + 1}")

    # Rename current to .1
    try:
        path.rename(path.parent / f"{path.name}.1")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/api/logs/service")
async def service_log(
    tail_bytes: int = Query(default=60000, ge=0, le=400000, description="读取尾部字节数"),
):
    """读取后端服务日志文件尾部内容。"""
    return _read_log_tail(_log_file_path(), tail_bytes)


class FrontendLogPayload(BaseModel):
    lines: list[str] = Field(..., max_length=100)


@router.post("/api/logs/frontend")
async def receive_frontend_log(request: Request):
    """
    接收前端批量日志并追加到 logs/frontend.log。

    支持 JSON body 和 sendBeacon（beacon 发送的 content-type 可能不是 application/json，
    所以这里也处理原始 body 解析）。
    """
    try:
        body = await request.json()
        lines = body.get("lines", [])
    except Exception:
        return {"ok": False, "error": "invalid JSON"}

    if not isinstance(lines, list) or len(lines) == 0:
        return {"ok": True, "written": 0}

    # Cap at 100 lines per request
    lines = lines[:100]

    log_path = _frontend_log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with _frontend_log_lock:
            _rotate_frontend_log(log_path)
            with open(log_path, "a", encoding="utf-8") as f:
                for line in lines:
                    f.write(str(line) + "\n")
    except Exception as e:
        logger.error("Failed to write frontend log: %s", e)
        return {"ok": False, "error": str(e)}

    return {"ok": True, "written": len(lines)}


@router.get("/api/logs/frontend")
async def frontend_log(
    tail_bytes: int = Query(default=60000, ge=0, le=400000, description="读取尾部字节数"),
):
    """读取前端日志文件尾部内容。"""
    return _read_log_tail(_frontend_log_path(), tail_bytes)


@router.get("/api/logs/combined")
async def combined_log(
    tail_bytes: int = Query(default=60000, ge=0, le=200000, description="每部分读取的尾部字节数"),
):
    """
    合并返回后端服务日志 + 前端日志的尾部内容，供前端 exportLogs() 一次性获取。
    """
    return {
        "backend": _read_log_tail(_log_file_path(), tail_bytes),
        "frontend": _read_log_tail(_frontend_log_path(), tail_bytes),
    }
