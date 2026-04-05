"""
PyAgent 交互模块 - 结果处理器

处理任务执行结果并格式化为用户友好的回复。
"""

from typing import Any

from src.execution import TaskResult

from .intent_types import IntentType


class ResultHandler:
    """结果处理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.max_result_length = self.config.get("max_result_length", 2000)
        self.include_details = self.config.get("include_details", True)
        self.include_steps = self.config.get("include_steps", False)

    async def format_result(
        self,
        result: TaskResult,
        intent_type: str = "TASK"
    ) -> str:
        """
        格式化执行结果为用户友好的回复
        
        Args:
            result: 任务执行结果
            intent_type: 意图类型
            
        Returns:
            str: 格式化的回复
        """
        if result.success:
            return self._format_success_result(result, intent_type)
        else:
            return self._format_error_result(result, intent_type)

    def _format_success_result(
        self,
        result: TaskResult,
        intent_type: str
    ) -> str:
        """格式化成功结果"""
        parts = []

        header = self._get_success_header(intent_type)
        parts.append(header)

        data_text = self._format_data(result.data)
        if data_text:
            parts.append(data_text)

        if self.include_steps and result.steps:
            steps_text = self._format_steps(result.steps)
            if steps_text:
                parts.append(steps_text)

        if self.include_details and result.metadata:
            details_text = self._format_metadata(result.metadata)
            if details_text:
                parts.append(details_text)

        if result.duration > 0:
            parts.append(f"\n执行耗时: {result.duration:.2f}秒")

        return "\n".join(parts)

    def _format_error_result(
        self,
        result: TaskResult,
        intent_type: str
    ) -> str:
        """格式化错误结果"""
        parts = []

        header = self._get_error_header(intent_type)
        parts.append(header)

        if result.error:
            error_msg = self._simplify_error(result.error)
            parts.append(f"\n错误信息: {error_msg}")

        if result.steps:
            last_step = result.steps[-1] if result.steps else None
            if last_step and last_step.get("error"):
                parts.append(f"\n最后操作: {last_step.get('action', '未知')}")
                parts.append(f"错误详情: {last_step.get('error', '未知错误')}")

        parts.append("\n建议: 请检查输入参数或稍后重试")

        return "\n".join(parts)

    def _get_success_header(self, intent_type: str) -> str:
        """获取成功结果头部"""
        headers = {
            "TASK": "任务执行成功",
            "QUERY": "查询结果",
            "COMMAND": "命令执行成功",
            "CHAT": "处理完成"
        }
        return headers.get(intent_type, "操作完成")

    def _get_error_header(self, intent_type: str) -> str:
        """获取错误结果头部"""
        headers = {
            "TASK": "任务执行失败",
            "QUERY": "查询失败",
            "COMMAND": "命令执行失败",
            "CHAT": "处理失败"
        }
        return headers.get(intent_type, "操作失败")

    def _format_data(self, data: Any) -> str:
        """格式化数据"""
        if data is None:
            return ""

        if isinstance(data, str):
            text = data
        elif isinstance(data, dict):
            text = self._format_dict(data)
        elif isinstance(data, list):
            text = self._format_list(data)
        else:
            text = str(data)

        if len(text) > self.max_result_length:
            text = text[:self.max_result_length] + "\n...(结果已截断)"

        return text

    def _format_dict(self, data: dict[str, Any], indent: int = 0) -> str:
        """格式化字典"""
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                lines.append(self._format_list(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {value}")

        return "\n".join(lines)

    def _format_list(self, data: list[Any], indent: int = 0) -> str:
        """格式化列表"""
        lines = []
        prefix = "  " * indent

        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                lines.append(f"{prefix}{i}. {self._format_dict(item, indent + 1)}")
            elif isinstance(item, list):
                lines.append(f"{prefix}{i}. {self._format_list(item, indent + 1)}")
            else:
                lines.append(f"{prefix}{i}. {item}")

        return "\n".join(lines)

    def _format_steps(self, steps: list[dict[str, Any]]) -> str:
        """格式化执行步骤"""
        if not steps:
            return ""

        lines = ["\n执行步骤:"]
        for i, step in enumerate(steps, 1):
            action = step.get("action", "未知操作")
            status = "完成" if step.get("success", True) else "失败"
            lines.append(f"  {i}. {action} - {status}")

        return "\n".join(lines)

    def _format_metadata(self, metadata: dict[str, Any]) -> str:
        """格式化元数据"""
        if not metadata:
            return ""

        important_keys = ["files_created", "files_modified", "commands_run", "output_file"]
        relevant_data = {k: v for k, v in metadata.items() if k in important_keys and v}

        if not relevant_data:
            return ""

        lines = ["\n执行详情:"]
        for key, value in relevant_data.items():
            key_display = key.replace("_", " ").title()
            lines.append(f"  {key_display}: {value}")

        return "\n".join(lines)

    def _simplify_error(self, error: str) -> str:
        """简化错误信息"""
        error_patterns = [
            (r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']+)'",
             "文件不存在: {0}"),
            (r"PermissionError: \[Errno 13\] Permission denied: '([^']+)'",
             "权限不足: {0}"),
            (r"TimeoutError: .*",
             "操作超时"),
            (r"ConnectionError: .*",
             "网络连接失败"),
            (r"ValueError: (.+)",
             "参数错误: {0}"),
            (r"TypeError: (.+)",
             "类型错误: {0}"),
        ]

        for pattern, template in error_patterns:
            import re
            match = re.search(pattern, error)
            if match:
                if match.groups():
                    return template.format(match.group(1))
                return template

        if len(error) > 200:
            return error[:200] + "..."

        return error

    def should_notify(self, result: TaskResult) -> bool:
        """
        判断是否需要通知用户
        
        Args:
            result: 任务执行结果
            
        Returns:
            bool: 是否需要通知
        """
        if not result.success:
            return True

        if result.metadata:
            notify_keys = ["user_action_required", "important_result", "needs_confirmation"]
            for key in notify_keys:
                if result.metadata.get(key):
                    return True

        return False

    def get_notification_level(self, result: TaskResult) -> str:
        """
        获取通知级别
        
        Args:
            result: 任务执行结果
            
        Returns:
            str: 通知级别 (info/warning/error)
        """
        if not result.success:
            if result.error and "critical" in result.error.lower():
                return "error"
            return "warning"

        if result.metadata:
            if result.metadata.get("important_result"):
                return "warning"

        return "info"

    def format_summary(self, result: TaskResult) -> str:
        """
        格式化结果摘要
        
        Args:
            result: 任务执行结果
            
        Returns:
            str: 摘要文本
        """
        status = "成功" if result.success else "失败"
        duration = f"{result.duration:.2f}秒" if result.duration > 0 else "未知"

        summary = f"状态: {status} | 耗时: {duration}"

        if result.steps:
            step_count = len(result.steps)
            success_count = sum(1 for s in result.steps if s.get("success", True))
            summary += f" | 步骤: {success_count}/{step_count}"

        return summary
