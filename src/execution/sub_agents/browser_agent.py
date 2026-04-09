"""
PyAgent 执行模块子Agent系统 - 浏览器子Agent

专门负责浏览器自动化任务的子Agent，集成新的AI驱动浏览器代理系统。
"""

import logging
from typing import Any

from .base_sub_agent import BaseSubAgent, SubAgentResult

logger = logging.getLogger(__name__)


class BrowserSubAgent(BaseSubAgent):
    """浏览器子Agent - 集成AI驱动的浏览器代理"""

    name = "browser_agent"
    description = "专门负责浏览器自动化任务的子Agent，支持自然语言任务执行"

    def __init__(
        self,
        llm_client: Any | None = None,
        browser_tool: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        super().__init__(llm_client, None, config)
        self.browser_tool = browser_tool
        self._browser_agent = None
        self._browser_session = None
        self._max_steps = config.get("max_steps", 50) if config else 50

    def _init_browser_agent(self) -> bool:
        """初始化浏览器代理"""
        if self._browser_agent is not None:
            return True

        try:
            from browser import (
                BrowserAgent,
                EventBus,
                LoopDetector,
                LoopDetectorConfig,
                StateManager,
            )

            event_bus = EventBus()
            state_manager = StateManager()
            loop_detector = LoopDetector(LoopDetectorConfig())

            self._browser_agent = BrowserAgent(
                task="",
                event_bus=event_bus,
                state_manager=state_manager,
                loop_detector=loop_detector,
                max_steps=self._max_steps,
            )

            if self.llm_client:
                self._browser_agent.set_llm_client(self.llm_client)

            return True
        except ImportError as e:
            logger.warning(f"浏览器代理模块导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"初始化浏览器代理失败: {e}")
            return False

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None
    ) -> SubAgentResult:
        """执行浏览器任务"""
        steps = []

        if self._init_browser_agent() and self._browser_agent:
            try:
                self._browser_agent.task = task
                self._browser_agent.reset()

                if self.llm_client:
                    self._browser_agent.set_llm_client(self.llm_client)

                if context and context.get("browser_session"):
                    self._browser_agent.set_browser_session(context["browser_session"])

                result = await self._browser_agent.run()

                steps.append({
                    "step": "ai_agent_execute",
                    "success": result.success,
                    "is_done": result.is_done,
                })

                return SubAgentResult(
                    success=result.success,
                    result=result.extracted_content or "任务完成",
                    error=result.error,
                    steps=steps
                )
            except Exception as e:
                logger.error(f"AI代理执行失败: {e}")
                steps.append({"step": "ai_agent_error", "error": str(e)})

        action = await self._parse_browser_action(task)
        steps.append({"step": "parse_action", "action": action})

        if self.browser_tool:
            try:
                result = await self.browser_tool.execute(**action)
                steps.append({"step": "execute", "success": result.success})

                return SubAgentResult(
                    success=result.success,
                    result=result.output if result.success else result.error,
                    steps=steps
                )
            except Exception as e:
                return SubAgentResult(
                    success=False,
                    error=str(e),
                    steps=steps
                )

        return SubAgentResult(
            success=True,
            result=f"模拟浏览器操作: {action}",
            steps=steps
        )

    async def _parse_browser_action(self, task: str) -> dict[str, Any]:
        """解析浏览器操作"""
        action = {"type": "navigate", "url": ""}

        task_lower = task.lower()

        if "打开" in task or "访问" in task or "navigate" in task_lower:
            import re
            url_match = re.search(r"https?://[^\s]+", task)
            if url_match:
                action["url"] = url_match.group(0)
                action["type"] = "navigate"

        elif "点击" in task or "click" in task_lower:
            action["type"] = "click"
            action["selector"] = ""

        elif "输入" in task or "type" in task_lower:
            action["type"] = "type"
            action["text"] = ""

        elif "截图" in task or "screenshot" in task_lower:
            action["type"] = "screenshot"

        return action

    async def navigate(self, url: str) -> SubAgentResult:
        """导航到URL"""
        return await self.execute(f"打开网页 {url}")

    async def click(self, selector: str) -> SubAgentResult:
        """点击元素"""
        return await self.execute(f"点击元素 {selector}")

    async def type_text(self, selector: str, text: str) -> SubAgentResult:
        """输入文本"""
        return await self.execute(f"在 {selector} 输入 {text}")

    async def screenshot(self) -> SubAgentResult:
        """截图"""
        return await self.execute("截图")

    async def extract_data(
        self,
        task: str,
        schema: dict[str, Any] | None = None,
    ) -> SubAgentResult:
        """
        提取结构化数据
        
        Args:
            task: 提取任务描述
            schema: 输出 Schema
            
        Returns:
            SubAgentResult: 包含提取数据的结果
        """
        try:
            from browser import StructuredOutputProcessor

            processor = StructuredOutputProcessor()

            if schema:
                from pydantic import create_model
                fields = {}
                for key, value_type in schema.items():
                    fields[key] = (value_type, None)
                output_model = create_model("ExtractedData", **fields)
                processor.set_output_model(output_model)

            result = await self.execute(task)

            if result.success and result.result:
                extraction = processor.extract_single(
                    {"data": result.result},
                    validate=True,
                )

                return SubAgentResult(
                    success=extraction.success,
                    result=extraction.items if extraction.success else None,
                    error=extraction.error,
                    steps=result.steps,
                )

            return result

        except ImportError:
            logger.warning("结构化输出模块不可用")
            return await self.execute(task)
        except Exception as e:
            logger.error(f"数据提取失败: {e}")
            return SubAgentResult(success=False, error=str(e))

    def get_status(self) -> dict[str, Any]:
        """获取代理状态"""
        if self._browser_agent:
            status = self._browser_agent.get_status()
            return {
                "state": status.state.value,
                "current_step": status.current_step,
                "max_steps": status.max_steps,
                "actions_taken": status.actions_taken,
                "errors_count": status.errors_count,
            }
        return {"state": "not_initialized"}

    def reset(self) -> None:
        """重置代理状态"""
        if self._browser_agent:
            self._browser_agent.reset()
