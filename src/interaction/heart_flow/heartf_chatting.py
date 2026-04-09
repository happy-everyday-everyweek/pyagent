"""
PyAgent 聊天Agent核心 - 主循环

参考MaiBot的HeartFChatting设计，实现持续的消息监控和动作规划循环。
"""

import asyncio
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

from .cycle_detail import CycleDetail, Timer
from .frequency_control import frequency_control_manager


@dataclass
class ChatStream:
    """聊天流"""
    stream_id: str
    platform: str = "unknown"
    group_info: Any | None = None
    user_info: Any | None = None
    context: Any | None = None


@dataclass
class MessageInfo:
    """消息信息"""
    message_id: str
    chat_id: str
    user_id: str
    platform: str
    content: str
    timestamp: float = field(default_factory=time.time)
    is_mentioned: bool = False
    is_at: bool = False


class HeartFChatting:
    """
    管理一个连续的Focus Chat循环
    用于在特定聊天流中生成回复。
    """

    def __init__(self, chat_id: str, config: Any | None = None):
        self.stream_id = chat_id
        self.chat_stream = ChatStream(stream_id=chat_id)
        self.log_prefix = f"[{chat_id}]"

        self.running: bool = False
        self._loop_task: asyncio.Task | None = None

        self.history_loop: list[CycleDetail] = []
        self._cycle_counter = 0
        self._current_cycle_detail: CycleDetail | None = None

        self.last_read_time = time.time()
        self.last_active_time = time.time()

        self.consecutive_no_reply_count = 0
        self.is_mute = False

        self.config = config or {}
        self.planner_smooth = self.config.get("planner_smooth", 0.5)
        self.talk_value = self.config.get("talk_value", 0.5)
        self.max_context_size = self.config.get("max_context_size", 50)

        self._action_handlers: dict[str, Any] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()

    async def start(self) -> None:
        """启动主循环"""
        if self.running:
            return

        try:
            self.running = True
            self._loop_task = asyncio.create_task(self._main_chat_loop())
            self._loop_task.add_done_callback(self._handle_loop_completion)
        except Exception:
            self.running = False
            self._loop_task = None
            raise

    async def stop(self) -> None:
        """停止主循环"""
        self.running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

    def _handle_loop_completion(self, task: asyncio.Task) -> None:
        """循环完成回调"""
        try:
            if exception := task.exception():
                print(f"{self.log_prefix} HeartFChatting异常: {exception}")
        except asyncio.CancelledError:
            pass

    def start_cycle(self) -> tuple[dict[str, float], str]:
        """开始新的循环"""
        self._cycle_counter += 1
        self._current_cycle_detail = CycleDetail(self._cycle_counter)
        self._current_cycle_detail.thinking_id = f"tid{round(time.time(), 2)!s}"
        return {}, self._current_cycle_detail.thinking_id

    def end_cycle(self, loop_info: dict[str, Any], timers: dict[str, float]) -> None:
        """结束当前循环"""
        if self._current_cycle_detail:
            self._current_cycle_detail.set_loop_info(loop_info)
            self._current_cycle_detail.timers = timers
            self._current_cycle_detail.end_time = time.time()
            self.history_loop.append(self._current_cycle_detail)

            if len(self.history_loop) > 100:
                self.history_loop = self.history_loop[-50:]

    def print_cycle_info(self, timers: dict[str, float]) -> None:
        """打印循环信息"""
        if not self._current_cycle_detail:
            return

        timer_strings = []
        for name, elapsed in timers.items():
            if elapsed >= 0.1:
                timer_strings.append(f"{name}: {elapsed:.2f}s")

        duration = self._current_cycle_detail.end_time - self._current_cycle_detail.start_time
        print(f"{self.log_prefix} 第{self._current_cycle_detail.cycle_id}次思考, 耗时: {duration:.1f}秒")

    async def _main_chat_loop(self) -> None:
        """主循环"""
        try:
            while self.running:
                success = await self._loopbody()
                await asyncio.sleep(0.1)
                if not success:
                    break
        except asyncio.CancelledError:
            pass
        except Exception:
            traceback.print_exc()
            await asyncio.sleep(3)
            self._loop_task = asyncio.create_task(self._main_chat_loop())

    async def _loopbody(self) -> bool:
        """循环体"""
        frequency_control = frequency_control_manager.get_or_create_frequency_control(self.stream_id)

        threshold = 1
        if self.consecutive_no_reply_count >= 5:
            threshold = 2
        elif self.consecutive_no_reply_count >= 3:
            import random
            threshold = 2 if random.random() < 0.5 else 1

        messages = await self._get_recent_messages()

        if len(messages) >= threshold:
            self.last_read_time = time.time()

            mentioned_message = None
            for message in messages:
                if message.is_mentioned or message.is_at:
                    mentioned_message = message
                    break

            if mentioned_message:
                await self._observe(messages, force_reply_message=mentioned_message)
            elif frequency_control.should_reply(self.talk_value):
                await self._observe(messages)
            else:
                await asyncio.sleep(10)
                return True
        else:
            await asyncio.sleep(0.2)
            return True

        return True

    async def _get_recent_messages(self) -> list[MessageInfo]:
        """获取最近消息"""
        return []

    async def _observe(
        self,
        recent_messages: list[MessageInfo],
        force_reply_message: MessageInfo | None = None
    ) -> bool:
        """观察并规划动作"""
        cycle_timers, thinking_id = self.start_cycle()

        print(f"{self.log_prefix} 开始第{self._cycle_counter}次思考")

        with Timer("规划器", cycle_timers):
            actions = await self._plan_actions(recent_messages, force_reply_message)

        print(f"{self.log_prefix} 决定执行{len(actions)}个动作")

        action_tasks = [
            asyncio.create_task(self._execute_action(action, thinking_id, cycle_timers))
            for action in actions
        ]

        results = await asyncio.gather(*action_tasks, return_exceptions=True)

        loop_info = self._build_loop_info(results, actions)

        self.end_cycle(loop_info, cycle_timers)
        self.print_cycle_info(cycle_timers)

        end_time = time.time()
        if end_time - self.last_read_time < self.planner_smooth:
            await asyncio.sleep(self.planner_smooth - (end_time - self.last_read_time))

        return True

    async def _plan_actions(
        self,
        messages: list[MessageInfo],
        force_reply_message: MessageInfo | None = None
    ) -> list[dict[str, Any]]:
        """规划动作"""
        actions = []

        if force_reply_message:
            actions.append({
                "action": "reply",
                "target_message_id": force_reply_message.message_id,
                "reasoning": "用户提及了我，必须回复"
            })
        else:
            actions.append({
                "action": "reply",
                "target_message_id": messages[-1].message_id if messages else None,
                "reasoning": "正常回复"
            })

        return actions

    async def _execute_action(
        self,
        action: dict[str, Any],
        thinking_id: str,
        timers: dict[str, float]
    ) -> dict[str, Any]:
        """执行动作"""
        action_type = action.get("action", "no_reply")

        if action_type == "no_reply":
            self.consecutive_no_reply_count += 1
            return {"action_type": "no_reply", "success": True, "result": "选择不回复"}

        if action_type == "reply":
            self.consecutive_no_reply_count = 0
            self.last_active_time = time.time()

            with Timer("回复生成", timers):
                reply_text = await self._generate_reply(action)

            return {"action_type": "reply", "success": True, "result": reply_text}

        handler = self._action_handlers.get(action_type)
        if handler:
            result = await handler(action)
            return {"action_type": action_type, "success": True, "result": result}
        return {"action_type": action_type, "success": False, "result": "未知动作"}

    async def _generate_reply(self, action: dict[str, Any]) -> str:
        """生成回复"""
        return "我收到了你的消息"

    def _build_loop_info(
        self,
        results: list[Any],
        actions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """构建循环信息"""
        return {
            "loop_plan_info": {
                "action_result": actions,
            },
            "loop_action_info": {
                "action_taken": any(r.get("success", False) for r in results if isinstance(r, dict)),
                "taken_time": time.time(),
            }
        }

    def register_action_handler(self, action_type: str, handler: Any) -> None:
        """注册动作处理器"""
        self._action_handlers[action_type] = handler

    async def push_message(self, message: MessageInfo) -> None:
        """推送消息到队列"""
        await self._message_queue.put(message)
