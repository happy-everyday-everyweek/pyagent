"""
PyAgent 浏览器自动化模块 - 视觉处理器

提供视觉理解能力，支持截图分析和坐标点击。
参考 browser-use 项目的视觉处理设计实现。
"""

import base64
import io
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class VisionMode(str, Enum):
    """视觉模式"""
    SCREENSHOT = "screenshot"
    ELEMENT = "element"
    REGION = "region"
    FULL_PAGE = "full_page"


@dataclass
class BoundingBox:
    """边界框"""
    x: float
    y: float
    width: float
    height: float
    
    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
    
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def contains(self, x: float, y: float) -> bool:
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )


class ScreenshotResult(BaseModel):
    """截图结果"""
    data: bytes | None = None
    base64: str | None = None
    width: int = 0
    height: int = 0
    format: str = "png"
    page_url: str | None = None
    page_title: str | None = None
    timestamp: float | None = None
    
    def to_data_uri(self) -> str:
        """转换为 Data URI"""
        if self.base64:
            return f"data:image/{self.format};base64,{self.base64}"
        elif self.data:
            b64 = base64.b64encode(self.data).decode("utf-8")
            return f"data:image/{self.format};base64,{b64}"
        return ""
    
    def to_openai_format(self) -> dict[str, Any]:
        """转换为 OpenAI 格式"""
        return {
            "type": "image_url",
            "image_url": {
                "url": self.to_data_uri(),
            },
        }


class VisionAnalysisResult(BaseModel):
    """视觉分析结果"""
    description: str
    elements: list[dict[str, Any]] = Field(default_factory=list)
    text_content: str | None = None
    suggested_actions: list[str] = Field(default_factory=list)
    click_coordinates: tuple[float, float] | None = None
    confidence: float = 0.0


class VisionProcessor:
    """视觉处理器"""
    
    def __init__(
        self,
        llm_client: Any | None = None,
        screenshot_quality: int = 80,
        max_width: int = 1920,
        max_height: int = 1080,
    ):
        """
        初始化视觉处理器
        
        Args:
            llm_client: LLM 客户端（支持多模态）
            screenshot_quality: 截图质量（1-100）
            max_width: 最大宽度
            max_height: 最大高度
        """
        self._llm_client = llm_client
        self._screenshot_quality = screenshot_quality
        self._max_width = max_width
        self._max_height = max_height
    
    def set_llm_client(self, client: Any) -> None:
        """设置 LLM 客户端"""
        self._llm_client = client
    
    async def capture_screenshot(
        self,
        page: Any,
        mode: VisionMode = VisionMode.SCREENSHOT,
        selector: str | None = None,
        region: BoundingBox | None = None,
        full_page: bool = False,
    ) -> ScreenshotResult:
        """
        捕获截图
        
        Args:
            page: Playwright 页面对象
            mode: 截图模式
            selector: 元素选择器（ELEMENT 模式）
            region: 区域边界框（REGION 模式）
            full_page: 是否全页面
            
        Returns:
            ScreenshotResult: 截图结果
        """
        import time
        
        try:
            options = {
                "type": "png",
                "quality": self._screenshot_quality,
                "full_page": full_page,
            }
            
            if mode == VisionMode.ELEMENT and selector:
                element = await page.query_selector(selector)
                if element:
                    screenshot_bytes = await element.screenshot(**options)
                else:
                    screenshot_bytes = await page.screenshot(**options)
            elif mode == VisionMode.REGION and region:
                screenshot_bytes = await page.screenshot(
                    clip={
                        "x": region.x,
                        "y": region.y,
                        "width": region.width,
                        "height": region.height,
                    },
                    **options,
                )
            else:
                screenshot_bytes = await page.screenshot(**options)
            
            viewport = page.viewport_size or {"width": 0, "height": 0}
            
            return ScreenshotResult(
                data=screenshot_bytes,
                base64=base64.b64encode(screenshot_bytes).decode("utf-8"),
                width=viewport.get("width", 0),
                height=viewport.get("height", 0),
                page_url=page.url,
                page_title=await page.title(),
                timestamp=time.time(),
            )
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return ScreenshotResult()
    
    async def analyze_screenshot(
        self,
        screenshot: ScreenshotResult,
        prompt: str | None = None,
        elements_of_interest: list[str] | None = None,
    ) -> VisionAnalysisResult:
        """
        分析截图
        
        Args:
            screenshot: 截图结果
            prompt: 分析提示词
            elements_of_interest: 感兴趣的元素类型
            
        Returns:
            VisionAnalysisResult: 分析结果
        """
        if self._llm_client is None:
            return VisionAnalysisResult(
                description="No LLM client configured",
                confidence=0.0,
            )
        
        if screenshot.base64 is None:
            return VisionAnalysisResult(
                description="No screenshot data available",
                confidence=0.0,
            )
        
        default_prompt = """Analyze this web page screenshot and provide:
1. A brief description of what you see
2. List of interactive elements (buttons, links, inputs) with their approximate positions
3. Any text content visible
4. Suggested actions for a browser automation agent

Format your response as JSON with keys: description, elements, text_content, suggested_actions"""

        analysis_prompt = prompt or default_prompt
        
        if elements_of_interest:
            analysis_prompt += f"\n\nFocus on these element types: {', '.join(elements_of_interest)}"
        
        try:
            response = await self._llm_client.chat.completions.create(
                model=self._llm_client.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": screenshot.to_data_uri(),
                                },
                            },
                        ],
                    },
                ],
                max_tokens=1000,
            )
            
            content = response.choices[0].message.content or ""
            
            import json
            import re
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    result_data = json.loads(json_match.group())
                    return VisionAnalysisResult(
                        description=result_data.get("description", content),
                        elements=result_data.get("elements", []),
                        text_content=result_data.get("text_content"),
                        suggested_actions=result_data.get("suggested_actions", []),
                        confidence=0.8,
                    )
                except json.JSONDecodeError:
                    pass
            
            return VisionAnalysisResult(
                description=content,
                confidence=0.6,
            )
            
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return VisionAnalysisResult(
                description=f"Analysis failed: {str(e)}",
                confidence=0.0,
            )
    
    async def find_element_coordinates(
        self,
        screenshot: ScreenshotResult,
        element_description: str,
    ) -> tuple[float, float] | None:
        """
        通过视觉分析找到元素坐标
        
        Args:
            screenshot: 截图结果
            element_description: 元素描述
            
        Returns:
            (x, y) 坐标元组或 None
        """
        prompt = f"""Find the element described as: "{element_description}"

Return ONLY the center coordinates as a JSON object with 'x' and 'y' keys.
Example: {{"x": 150, "y": 300}}

If the element is not found, return {{"x": null, "y": null}}"""

        result = await self.analyze_screenshot(screenshot, prompt=prompt)
        
        if result.click_coordinates:
            return result.click_coordinates
        
        for element in result.elements:
            if element_description.lower() in element.get("description", "").lower():
                bounds = element.get("bounds", {})
                if bounds:
                    x = bounds.get("x", 0) + bounds.get("width", 0) / 2
                    y = bounds.get("y", 0) + bounds.get("height", 0) / 2
                    return (x, y)
        
        return None
    
    def resize_for_analysis(
        self,
        screenshot: ScreenshotResult,
        target_width: int | None = None,
        target_height: int | None = None,
    ) -> ScreenshotResult:
        """
        调整截图大小以优化分析
        
        Args:
            screenshot: 原始截图
            target_width: 目标宽度
            target_height: 目标高度
            
        Returns:
            调整后的截图结果
        """
        if screenshot.data is None:
            return screenshot
        
        try:
            from PIL import Image
            
            image = Image.open(io.BytesIO(screenshot.data))
            
            width = target_width or self._max_width
            height = target_height or self._max_height
            
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            image.save(output, format="PNG", quality=self._screenshot_quality)
            resized_data = output.getvalue()
            
            return ScreenshotResult(
                data=resized_data,
                base64=base64.b64encode(resized_data).decode("utf-8"),
                width=image.width,
                height=image.height,
                format="png",
                page_url=screenshot.page_url,
                page_title=screenshot.page_title,
                timestamp=screenshot.timestamp,
            )
            
        except ImportError:
            logger.warning("PIL not available, returning original screenshot")
            return screenshot
        except Exception as e:
            logger.error(f"Image resize failed: {e}")
            return screenshot
