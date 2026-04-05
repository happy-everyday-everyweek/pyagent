"""
PyAgent 安全策略系统 - 工具抖动检测

检测工具调用的异常频率，防止无限循环。
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    timestamp: float
    args: dict[str, Any] = field(default_factory=dict)
    result_hash: str = ""


class ToolJitterDetector:
    """
    工具抖动检测器

    检测以下异常模式：
    1. 同一工具短时间内重复调用
    2. 相同参数重复调用
    3. 工具调用频率异常高
    """

    def __init__(
        self,
        window_size: int = 20,
        time_window: float = 60.0,
        same_tool_threshold: int = 5,
        same_args_threshold: int = 3,
        frequency_threshold: float = 10.0
    ):
        self.window_size = window_size
        self.time_window = time_window
        self.same_tool_threshold = same_tool_threshold
        self.same_args_threshold = same_args_threshold
        self.frequency_threshold = frequency_threshold

        self._call_history: deque = deque(maxlen=window_size)
        self._tool_counts: dict[str, int] = {}
        self._args_hashes: dict[str, int] = {}
        self._last_reset = time.time()

    def record_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result_hash: str = ""
    ) -> None:
        """记录工具调用"""
        record = ToolCallRecord(
            tool_name=tool_name,
            timestamp=time.time(),
            args=args,
            result_hash=result_hash
        )

        self._call_history.append(record)

        self._tool_counts[tool_name] = self._tool_counts.get(tool_name, 0) + 1

        args_hash = self._hash_args(args)
        key = f"{tool_name}:{args_hash}"
        self._args_hashes[key] = self._args_hashes.get(key, 0) + 1

    def detect_jitter(self) -> dict[str, Any] | None:
        """检测抖动"""
        self._cleanup_old_records()

        jitter_info = self._detect_same_tool_jitter()
        if jitter_info:
            return jitter_info

        jitter_info = self._detect_same_args_jitter()
        if jitter_info:
            return jitter_info

        jitter_info = self._detect_high_frequency_jitter()
        if jitter_info:
            return jitter_info

        return None

    def _detect_same_tool_jitter(self) -> dict[str, Any] | None:
        """检测同一工具重复调用"""
        for tool_name, count in self._tool_counts.items():
            if count >= self.same_tool_threshold:
                return {
                    "type": "same_tool",
                    "tool_name": tool_name,
                    "count": count,
                    "threshold": self.same_tool_threshold,
                    "message": f"工具 '{tool_name}' 在短时间内被调用 {count} 次"
                }
        return None

    def _detect_same_args_jitter(self) -> dict[str, Any] | None:
        """检测相同参数重复调用"""
        for key, count in self._args_hashes.items():
            if count >= self.same_args_threshold:
                tool_name, args_hash = key.split(":", 1)
                return {
                    "type": "same_args",
                    "tool_name": tool_name,
                    "args_hash": args_hash,
                    "count": count,
                    "threshold": self.same_args_threshold,
                    "message": f"工具 '{tool_name}' 使用相同参数被调用 {count} 次"
                }
        return None

    def _detect_high_frequency_jitter(self) -> dict[str, Any] | None:
        """检测高频率调用"""
        if not self._call_history:
            return None

        recent_calls = [
            r for r in self._call_history
            if time.time() - r.timestamp <= self.time_window
        ]

        if not recent_calls:
            return None

        frequency = len(recent_calls) / self.time_window

        if frequency >= self.frequency_threshold:
            return {
                "type": "high_frequency",
                "frequency": frequency,
                "threshold": self.frequency_threshold,
                "call_count": len(recent_calls),
                "time_window": self.time_window,
                "message": f"工具调用频率过高: {frequency:.1f} 次/秒"
            }

        return None

    def _cleanup_old_records(self) -> None:
        """清理旧记录"""
        current_time = time.time()

        if current_time - self._last_reset > self.time_window:
            self._tool_counts.clear()
            self._args_hashes.clear()
            self._last_reset = current_time

        while self._call_history:
            if current_time - self._call_history[0].timestamp > self.time_window:
                old_record = self._call_history.popleft()
                tool_name = old_record.tool_name
                if tool_name in self._tool_counts:
                    self._tool_counts[tool_name] = max(0, self._tool_counts[tool_name] - 1)
            else:
                break

    def _hash_args(self, args: dict[str, Any]) -> str:
        """生成参数哈希"""
        import json
        try:
            return str(hash(json.dumps(args, sort_keys=True, default=str)))
        except Exception:
            return str(hash(str(args)))

    def reset(self) -> None:
        """重置检测器"""
        self._call_history.clear()
        self._tool_counts.clear()
        self._args_hashes.clear()
        self._last_reset = time.time()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_calls": len(self._call_history),
            "unique_tools": len(self._tool_counts),
            "tool_counts": dict(self._tool_counts),
            "time_window": self.time_window,
            "window_size": self.window_size
        }


tool_jitter_detector = ToolJitterDetector()
