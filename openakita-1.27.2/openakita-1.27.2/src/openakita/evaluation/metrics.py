"""
评估指标定义

定义 Agent 性能评估的各项指标和聚合逻辑。
从 Tracing 系统的 Trace 数据中提取量化指标。
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TraceMetrics:
    """
    单次 Trace 提取的指标。

    从一个 Trace (一次完整用户请求) 中提取的量化数据。
    """

    trace_id: str
    session_id: str = ""
    timestamp: float = field(default_factory=time.time)

    # 基本指标
    total_iterations: int = 0
    total_llm_calls: int = 0
    total_tool_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: float = 0.0

    # 质量指标
    task_completed: bool = False  # 任务是否完成 (by state machine)
    tool_errors: int = 0  # 工具调用失败次数
    loop_detected: bool = False  # 是否触发了循环检测
    rollback_count: int = 0  # 回滚次数
    context_compressions: int = 0  # 上下文压缩次数

    # 工具使用
    tools_used: list[str] = field(default_factory=list)
    unique_tools: int = 0

    @classmethod
    def from_trace(cls, trace: Any) -> "TraceMetrics":
        """从 Trace 对象提取指标。"""
        from ..tracing.tracer import SpanStatus, SpanType

        metrics = cls(
            trace_id=trace.trace_id,
            session_id=trace.session_id,
            total_duration_ms=trace.duration_ms or 0.0,
        )

        for span in trace.spans:
            if span.span_type == SpanType.LLM:
                metrics.total_llm_calls += 1
                metrics.total_input_tokens += span.attributes.get("input_tokens", 0)
                metrics.total_output_tokens += span.attributes.get("output_tokens", 0)

            elif span.span_type == SpanType.TOOL:
                metrics.total_tool_calls += 1
                tool_name = span.attributes.get("tool_name", "")
                if tool_name:
                    metrics.tools_used.append(tool_name)
                if span.status == SpanStatus.ERROR:
                    metrics.tool_errors += 1

            elif span.span_type == SpanType.CONTEXT:
                metrics.context_compressions += 1

            elif span.span_type == SpanType.REASONING:
                metrics.total_iterations += 1

        metrics.unique_tools = len(set(metrics.tools_used))

        # 从 trace metadata 提取完成信息
        metadata = trace.metadata or {}
        result = metadata.get("result", "")
        metrics.task_completed = result in ("completed", "completed_end_turn")
        metrics.loop_detected = result == "loop_terminated"
        metrics.rollback_count = metadata.get("rollback_count", 0)

        return metrics


@dataclass
class EvalResult:
    """
    单次评估结果。

    包含量化指标 + LLM Judge 的定性评估。
    """

    trace_id: str
    metrics: TraceMetrics
    judge_score: float = 0.0  # 0-1, 由 Judge 评分
    judge_reasoning: str = ""
    judge_suggestions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)  # 标签: "failed", "slow", "loop", etc.

    def is_good(self) -> bool:
        """是否通过评估"""
        return self.metrics.task_completed and self.judge_score >= 0.7


@dataclass
class EvalMetrics:
    """
    聚合评估指标。

    从多个 EvalResult 聚合得到的整体性能指标。
    """

    # 计数
    total_traces: int = 0
    period_start: float = 0.0
    period_end: float = 0.0

    # 完成率
    task_completion_rate: float = 0.0  # 任务完成率

    # 工具相关
    tool_selection_accuracy: float = 0.0  # 工具无错率 (无错trace / 总trace)
    avg_tool_calls_per_task: float = 0.0
    most_errored_tools: list[tuple[str, int]] = field(default_factory=list)

    # 效率指标
    avg_iterations: float = 0.0
    avg_token_usage: int = 0  # 平均总 token
    avg_latency_ms: float = 0.0

    # 异常检测
    loop_detection_rate: float = 0.0  # 触发循环检测的比例
    error_recovery_rate: float = 0.0  # 有错误但最终完成的比例
    rollback_rate: float = 0.0  # 触发回滚的比例

    # Judge 评分
    avg_judge_score: float = 0.0

    @classmethod
    def aggregate(cls, results: list[EvalResult]) -> "EvalMetrics":
        """从评估结果列表聚合指标。"""
        if not results:
            return cls()

        total = len(results)
        now = time.time()

        # 完成率
        completed = sum(1 for r in results if r.metrics.task_completed)

        # 工具准确率: 无工具错误的 trace 比例
        no_tool_errors = sum(1 for r in results if r.metrics.tool_errors == 0)

        # 循环检测率
        loops = sum(1 for r in results if r.metrics.loop_detected)

        # 错误恢复率
        had_errors = [r for r in results if r.metrics.tool_errors > 0]
        recovered = sum(1 for r in had_errors if r.metrics.task_completed)

        # 回滚率
        rollbacks = sum(1 for r in results if r.metrics.rollback_count > 0)

        metrics = cls(
            total_traces=total,
            period_start=min(r.metrics.timestamp for r in results),
            period_end=now,
            task_completion_rate=completed / total,
            tool_selection_accuracy=no_tool_errors / total,
            avg_tool_calls_per_task=(
                sum(r.metrics.total_tool_calls for r in results) / total
            ),
            avg_iterations=sum(r.metrics.total_iterations for r in results) / total,
            avg_token_usage=int(
                sum(r.metrics.total_input_tokens + r.metrics.total_output_tokens for r in results) / total
            ),
            avg_latency_ms=sum(r.metrics.total_duration_ms for r in results) / total,
            loop_detection_rate=loops / total,
            error_recovery_rate=(recovered / len(had_errors)) if had_errors else 1.0,
            rollback_rate=rollbacks / total,
            avg_judge_score=(
                sum(r.judge_score for r in results) / total
            ),
        )

        return metrics

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "total_traces": self.total_traces,
            "task_completion_rate": round(self.task_completion_rate, 3),
            "tool_selection_accuracy": round(self.tool_selection_accuracy, 3),
            "avg_tool_calls_per_task": round(self.avg_tool_calls_per_task, 1),
            "avg_iterations": round(self.avg_iterations, 1),
            "avg_token_usage": self.avg_token_usage,
            "avg_latency_ms": round(self.avg_latency_ms, 0),
            "loop_detection_rate": round(self.loop_detection_rate, 3),
            "error_recovery_rate": round(self.error_recovery_rate, 3),
            "rollback_rate": round(self.rollback_rate, 3),
            "avg_judge_score": round(self.avg_judge_score, 3),
        }

    def format_report(self) -> str:
        """格式化为可读报告"""
        lines = [
            "=" * 50,
            "OpenAkita Agent 评估报告",
            "=" * 50,
            f"评估 Trace 数: {self.total_traces}",
            "",
            "📊 核心指标:",
            f"  任务完成率:     {self.task_completion_rate:.1%}",
            f"  工具无错率:     {self.tool_selection_accuracy:.1%}",
            f"  Judge 平均分:   {self.avg_judge_score:.2f}/1.0",
            "",
            "⚡ 效率指标:",
            f"  平均迭代次数:   {self.avg_iterations:.1f}",
            f"  平均 Token:     {self.avg_token_usage:,}",
            f"  平均延迟:       {self.avg_latency_ms:.0f}ms",
            f"  平均工具调用数: {self.avg_tool_calls_per_task:.1f}",
            "",
            "🔍 异常指标:",
            f"  循环检测率:     {self.loop_detection_rate:.1%}",
            f"  错误恢复率:     {self.error_recovery_rate:.1%}",
            f"  回滚触发率:     {self.rollback_rate:.1%}",
            "=" * 50,
        ]
        return "\n".join(lines)
