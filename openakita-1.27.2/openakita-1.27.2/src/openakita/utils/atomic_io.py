"""
原子文件写入工具

提供 temp+rename 模式的原子 JSON 写入，防止写入中途崩溃导致文件损坏。
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def atomic_json_write(path: Path, data: Any, *, indent: int = 2) -> None:
    """原子写入 JSON 文件（temp + rename 模式）。

    先写入临时文件，验证 JSON 正确性后再重命名为目标文件。
    在 POSIX 系统上 rename 是原子操作；Windows 上通过 replace 保证覆盖。

    Args:
        path: 目标文件路径
        data: 可 JSON 序列化的数据
        indent: JSON 缩进级别
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

        # Windows 不支持 rename 覆盖已存在文件，使用 replace
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise
