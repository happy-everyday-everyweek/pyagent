"""
PyAgent 执行模块核心 - ReAct推理引擎

参考OpenAkita的Brain设计，实现Think-Act-Observe三阶段推理循环。
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReasoningStep(Enum):
    """推理步骤"""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"


@dataclass
class ThoughtStep:
    """思考步骤"""
    step_type: ReasoningStep
    content: str = ""
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReActResult:
    """ReAct推理结果"""
    success: bool
    result: str = ""
    steps: list[ThoughtStep] = field(default_factory=list)
    final_thought: str = ""
    iterations: int = 0
    duration: float = 0.0


class ReActEngine:
    """
    ReAct推理引擎

    实现显式三阶段推理循环：
    - Think: 思考下一步行动
    - Act: 执行工具调用
    - Observe: 观察执行结果
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        tool_registry: Any | None = None,
        security_policy: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.security_policy = security_policy
        self.config = config or {}

        self.max_iterations = self.config.get("max_iterations", 10)
        self.max_tool_calls_per_step = self.config.get("max_tool_calls_per_step", 3)
        self.enable_loop_detection = self.config.get("enable_loop_detection", True)
        self.enable_tool_jitter_detection = self.config.get("enable_tool_jitter_detection", True)

        self._tool_call_history: list[str] = []
        self._loop_detection_window = 5
        self._jitter_threshold = 3

    async def run(
        self,
        task: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """运行ReAct推理循环"""
        start_time = time.time()
        steps: list[ThoughtStep] = []
        result = ReActResult(success=False, steps=steps)

        conversation_history = []
        current_thought = ""

        for iteration in range(self.max_iterations):
            result.iterations = iteration + 1

            think_step = await self._think(task, current_thought, conversation_history)
            steps.append(think_step)

            if self._is_final_answer(think_step.content):
                result.success = True
                result.result = self._extract_final_answer(think_step.content)
                result.final_thought = think_step.content
                break

            if self._should_skip_action(think_step.content):
                continue

            if self.enable_loop_detection and self._detect_loop(steps):
                result.result = "检测到循环，终止推理"
                break

            act_step = await self._act(think_step)
            steps.append(act_step)

            if act_step.tool_name:
                self._tool_call_history.append(act_step.tool_name)

                if self.enable_tool_jitter_detection and self._detect_tool_jitter():
                    result.result = "检测到工具抖动，终止推理"
                    break

                observe_step = await self._observe(act_step)
                steps.append(observe_step)

                current_thought = observe_step.observation
                conversation_history.append({
                    "thought": think_step.content,
                    "action": act_step.tool_name,
                    "observation": observe_step.observation
                })

        result.duration = time.time() - start_time

        if not result.success:
            result.result = "达到最大迭代次数，任务未完成"

        return {
            "success": result.success,
            "result": result.result,
            "steps": [{"type": s.step_type.value, "content": s.content} for s in steps],
            "iterations": result.iterations,
            "duration": result.duration
        }

    async def _think(
        self,
        task: str,
        previous_observation: str,
        history: list[dict[str, str]]
    ) -> ThoughtStep:
        """思考阶段"""
        prompt = self._build_think_prompt(task, previous_observation, history)

        if self.llm_client:
            try:
                from src.llm import Message
                messages = [Message(role="user", content=prompt)]
                response = await self.llm_client.generate(messages=messages)
                content = response.content
            except Exception:
                content = "思考失败，请重试"
        else:
            content = "我需要完成这个任务"

        return ThoughtStep(
            step_type=ReasoningStep.THINK,
            content=content
        )

    async def _act(self, think_step: ThoughtStep) -> ThoughtStep:
        """行动阶段"""
        tool_name, tool_args = self._parse_action(think_step.content)

        if tool_name and self.tool_registry:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                return ThoughtStep(
                    step_type=ReasoningStep.ACT,
                    content=think_step.content,
                    tool_name=tool_name,
                    tool_args=tool_args
                )

        return ThoughtStep(
            step_type=ReasoningStep.ACT,
            content=think_step.content,
            tool_name=tool_name or "",
            tool_args=tool_args
        )

    async def _observe(self, act_step: ThoughtStep) -> ThoughtStep:
        """观察阶段"""
        observation = ""

        if act_step.tool_name and self.tool_registry:
            tool = self.tool_registry.get_tool(act_step.tool_name)
            if tool:
                try:
                    result = await tool.execute(**act_step.tool_args)
                    observation = str(result)
                except Exception as e:
                    observation = f"工具执行失败: {str(e)}"

        if not observation:
            observation = "无观察结果"

        return ThoughtStep(
            step_type=ReasoningStep.OBSERVE,
            content=observation,
            observation=observation
        )

    def _build_think_prompt(
        self,
        task: str,
        previous_observation: str,
        history: list[dict[str, str]]
    ) -> str:
        """构建思考提示词"""
        prompt = f"""任务: {task}

请思考如何完成这个任务。

"""

        if previous_observation:
            prompt += f"上一步观察: {previous_observation}\n\n"

        if history:
            prompt += "历史记录:\n"
            for h in history[-3:]:
                prompt += f"- 思考: {h['thought']}\n"
                prompt += f"- 行动: {h['action']}\n"
                prompt += f"- 观察: {h['observation']}\n"
            prompt += "\n"

        prompt += """请输出你的思考，如果需要调用工具，请使用以下格式：
Thought: 你的思考
Action: 工具名称
Action Input: {"参数名": "参数值"}

如果已经得到最终答案，请使用：
Final Answer: 最终答案
"""

        return prompt

    def _parse_action(self, content: str) -> tuple:
        """解析行动"""
        import json
        import re

        tool_name = ""
        tool_args = {}

        action_match = re.search(r"Action:\s*(\w+)", content)
        if action_match:
            tool_name = action_match.group(1)

        args_match = re.search(r"Action Input:\s*(\{.*?\})", content, re.DOTALL)
        if args_match:
            try:
                tool_args = json.loads(args_match.group(1))
            except json.JSONDecodeError:
                pass

        return tool_name, tool_args

    def _is_final_answer(self, content: str) -> bool:
        """判断是否是最终答案"""
        return "Final Answer:" in content

    def _extract_final_answer(self, content: str) -> str:
        """提取最终答案"""
        import re
        match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content

    def _should_skip_action(self, content: str) -> bool:
        """判断是否应该跳过行动"""
        return False

    def _detect_loop(self, steps: list[ThoughtStep]) -> bool:
        """检测循环"""
        if len(steps) < self._loop_detection_window * 2:
            return False

        recent_thoughts = [s.content for s in steps[-self._loop_detection_window:]
                          if s.step_type == ReasoningStep.THINK]

        if len(recent_thoughts) >= 2:
            if recent_thoughts[-1] == recent_thoughts[-2]:
                return True

        return False

    def _detect_tool_jitter(self) -> bool:
        """检测工具抖动"""
        if len(self._tool_call_history) < self._jitter_threshold:
            return False

        recent_calls = self._tool_call_history[-self._jitter_threshold:]
        if len(set(recent_calls)) == 1:
            return True

        return False
