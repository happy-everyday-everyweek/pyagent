"""
PyAgent 聊天Agent核心 - 频率控制

参考MaiBot的frequency_control设计，控制回复频率。
"""

import time
from dataclasses import dataclass, field


@dataclass
class FrequencyControl:
    """频率控制器"""

    chat_id: str
    base_talk_value: float = 0.5
    min_talk_value: float = 0.1
    max_talk_value: float = 1.0

    last_reply_time: float = field(default_factory=time.time)
    reply_count: int = 0
    message_count: int = 0

    decay_rate: float = 0.95
    recovery_rate: float = 0.1
    recovery_interval: float = 300.0

    last_recovery_time: float = field(default_factory=time.time)

    def update_message(self) -> None:
        """更新消息计数"""
        self.message_count += 1
        self._try_recovery()

    def update_reply(self) -> None:
        """更新回复计数"""
        self.reply_count += 1
        self.last_reply_time = time.time()
        self._apply_decay()

    def get_talk_frequency_adjust(self) -> float:
        """获取回复频率调整系数"""
        self._try_recovery()

        time_since_last_reply = time.time() - self.last_reply_time

        if time_since_last_reply < 10:
            return 0.3
        if time_since_last_reply < 30:
            return 0.5
        if time_since_last_reply < 60:
            return 0.7
        if time_since_last_reply < 120:
            return 0.85
        return 1.0

    def should_reply(self, threshold: float = 0.5) -> bool:
        """判断是否应该回复"""
        import random

        adjusted_value = self.base_talk_value * self.get_talk_frequency_adjust()
        return random.random() < adjusted_value

    def _apply_decay(self) -> None:
        """应用衰减"""
        self.base_talk_value = max(
            self.min_talk_value,
            self.base_talk_value * self.decay_rate
        )

    def _try_recovery(self) -> None:
        """尝试恢复"""
        current_time = time.time()
        time_since_recovery = current_time - self.last_recovery_time

        if time_since_recovery >= self.recovery_interval:
            recovery_cycles = int(time_since_recovery / self.recovery_interval)
            self.base_talk_value = min(
                self.max_talk_value,
                self.base_talk_value + self.recovery_rate * recovery_cycles
            )
            self.last_recovery_time = current_time

    def reset(self) -> None:
        """重置频率控制"""
        self.base_talk_value = 0.5
        self.reply_count = 0
        self.message_count = 0
        self.last_reply_time = time.time()
        self.last_recovery_time = time.time()


class FrequencyControlManager:
    """频率控制器管理器"""

    def __init__(self):
        self._controls: dict[str, FrequencyControl] = {}

    def get_or_create_frequency_control(self, chat_id: str) -> FrequencyControl:
        """获取或创建频率控制器"""
        if chat_id not in self._controls:
            self._controls[chat_id] = FrequencyControl(chat_id=chat_id)
        return self._controls[chat_id]

    def remove_frequency_control(self, chat_id: str) -> None:
        """移除频率控制器"""
        if chat_id in self._controls:
            del self._controls[chat_id]

    def reset_all(self) -> None:
        """重置所有频率控制器"""
        for control in self._controls.values():
            control.reset()


frequency_control_manager = FrequencyControlManager()
