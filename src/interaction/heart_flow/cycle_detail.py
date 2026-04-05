"""
PyAgent 聊天Agent核心 - 循环信息记录

参考MaiBot的CycleDetail设计，记录每次思考循环的详细信息。
"""

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CycleDetail:
    """循环信息记录类"""

    cycle_id: int
    thinking_id: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    timers: dict[str, float] = field(default_factory=dict)
    loop_plan_info: dict[str, Any] = field(default_factory=dict)
    loop_action_info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """将循环信息转换为字典格式"""

        def convert_to_serializable(obj, depth=0, seen=None):
            if seen is None:
                seen = set()

            if depth > 5:
                return str(obj)

            obj_id = id(obj)
            if obj_id in seen:
                return str(obj)
            seen.add(obj_id)

            try:
                if hasattr(obj, "to_dict"):
                    return obj.to_dict()
                elif isinstance(obj, dict):
                    return {
                        k: convert_to_serializable(v, depth + 1, seen)
                        for k, v in obj.items()
                        if isinstance(k, (str, int, float, bool))
                    }
                elif isinstance(obj, (list, tuple)):
                    return [
                        convert_to_serializable(item, depth + 1, seen)
                        for item in obj
                        if not isinstance(item, (dict, list, tuple))
                        or isinstance(item, (str, int, float, bool, type(None)))
                    ]
                elif isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                else:
                    return str(obj)
            finally:
                seen.remove(obj_id)

        return {
            "cycle_id": self.cycle_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "timers": self.timers,
            "thinking_id": self.thinking_id,
            "loop_plan_info": convert_to_serializable(self.loop_plan_info),
            "loop_action_info": convert_to_serializable(self.loop_action_info),
        }

    def set_loop_info(self, loop_info: dict[str, Any]) -> None:
        """设置循环信息"""
        self.loop_plan_info = loop_info.get("loop_plan_info", {})
        self.loop_action_info = loop_info.get("loop_action_info", {})


class Timer:
    """计时器上下文管理器"""

    def __init__(self, name: str, timers: dict[str, float]):
        self.name = name
        self.timers = timers
        self.start_time: float = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.timers[self.name] = time.time() - self.start_time
