"""
PyAgent 浏览器自动化模块 - 循环检测系统

检测执行循环和页面停滞，生成智能提示帮助 Agent 调整策略。
参考 browser-use 项目的循环检测设计实现。
"""

import hashlib
import json
import logging
from collections import deque
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LoopType(str, Enum):
    """循环类型"""
    ACTION_REPEAT = "action_repeat"
    PAGE_STAGNANT = "page_stagnant"
    URL_CYCLE = "url_cycle"
    STATE_SIMILAR = "state_similar"


@dataclass
class LoopAlert:
    """循环警告"""
    loop_type: LoopType
    count: int
    message: str
    suggestion: str
    severity: str = "warning"


@dataclass
class ActionRecord:
    """动作记录"""
    action_name: str
    params_hash: str
    url: str
    timestamp: float
    result_summary: str | None = None


@dataclass
class PageFingerprint:
    """页面指纹"""
    url: str
    title: str
    content_hash: str
    element_count: int
    interactive_count: int
    timestamp: float


class LoopDetectorConfig(BaseModel):
    """循环检测器配置"""
    
    max_action_repeat: int = Field(default=3, ge=1, le=10)
    max_page_stagnant: int = Field(default=5, ge=1, le=20)
    max_url_cycle: int = Field(default=3, ge=1, le=10)
    similarity_threshold: float = Field(default=0.85, ge=0.5, le=1.0)
    history_size: int = Field(default=20, ge=5, le=100)


class LoopDetector:
    """循环检测器"""
    
    def __init__(self, config: LoopDetectorConfig | None = None):
        """
        初始化循环检测器
        
        Args:
            config: 检测器配置
        """
        self.config = config or LoopDetectorConfig()
        self._action_history: deque[ActionRecord] = deque(
            maxlen=self.config.history_size
        )
        self._page_history: deque[PageFingerprint] = deque(
            maxlen=self.config.history_size
        )
        self._url_history: deque[str] = deque(
            maxlen=self.config.history_size
        )
        self._alerts: list[LoopAlert] = []
    
    def _hash_params(self, params: dict[str, Any] | None) -> str:
        """计算参数哈希"""
        if params is None:
            return ""
        
        try:
            json_str = json.dumps(params, sort_keys=True, default=str)
            return hashlib.md5(json_str.encode()).hexdigest()[:8]
        except Exception:
            return ""
    
    def _hash_content(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def record_action(
        self,
        action_name: str,
        params: dict[str, Any] | None,
        url: str,
        result_summary: str | None = None,
    ) -> None:
        """
        记录动作执行
        
        Args:
            action_name: 动作名称
            params: 动作参数
            url: 当前 URL
            result_summary: 结果摘要
        """
        import time
        
        record = ActionRecord(
            action_name=action_name,
            params_hash=self._hash_params(params),
            url=url,
            timestamp=time.time(),
            result_summary=result_summary,
        )
        
        self._action_history.append(record)
        logger.debug(f"Recorded action: {action_name}")
    
    def record_page(
        self,
        url: str,
        title: str,
        content: str,
        element_count: int,
        interactive_count: int,
    ) -> None:
        """
        记录页面状态
        
        Args:
            url: 页面 URL
            title: 页面标题
            content: 页面内容
            element_count: 元素总数
            interactive_count: 可交互元素数
        """
        import time
        
        fingerprint = PageFingerprint(
            url=url,
            title=title,
            content_hash=self._hash_content(content),
            element_count=element_count,
            interactive_count=interactive_count,
            timestamp=time.time(),
        )
        
        self._page_history.append(fingerprint)
        self._url_history.append(url)
        logger.debug(f"Recorded page: {url}")
    
    def check_action_loop(self) -> LoopAlert | None:
        """
        检测动作循环
        
        Returns:
            LoopAlert 或 None
        """
        if len(self._action_history) < self.config.max_action_repeat:
            return None
        
        recent_actions = list(self._action_history)[-self.config.max_action_repeat:]
        
        first_action = recent_actions[0]
        for action in recent_actions[1:]:
            if (action.action_name != first_action.action_name or
                action.params_hash != first_action.params_hash):
                return None
        
        count = self.config.max_action_repeat
        
        return LoopAlert(
            loop_type=LoopType.ACTION_REPEAT,
            count=count,
            message=f"Same action '{first_action.action_name}' repeated {count} times",
            suggestion=(
                f"The action '{first_action.action_name}' has been repeated {count} times "
                "without success. Consider:\n"
                "1. Trying a different approach\n"
                "2. Checking if the element is visible and interactive\n"
                "3. Scrolling to make the element visible\n"
                "4. Using a different selector or element"
            ),
            severity="warning",
        )
    
    def check_page_stagnant(self) -> LoopAlert | None:
        """
        检测页面停滞
        
        Returns:
            LoopAlert 或 None
        """
        if len(self._page_history) < self.config.max_page_stagnant:
            return None
        
        recent_pages = list(self._page_history)[-self.config.max_page_stagnant:]
        
        first_page = recent_pages[0]
        for page in recent_pages[1:]:
            if page.content_hash != first_page.content_hash:
                return None
        
        count = self.config.max_page_stagnant
        
        return LoopAlert(
            loop_type=LoopType.PAGE_STAGNANT,
            count=count,
            message=f"Page content unchanged for {count} steps",
            suggestion=(
                f"The page content has not changed for {count} consecutive steps. "
                "Consider:\n"
                "1. Scrolling down to see more content\n"
                "2. Clicking on a different element\n"
                "3. Navigating to a different page\n"
                "4. Checking if there's a popup or modal blocking interaction"
            ),
            severity="info",
        )
    
    def check_url_cycle(self) -> LoopAlert | None:
        """
        检测 URL 循环
        
        Returns:
            LoopAlert 或 None
        """
        if len(self._url_history) < 4:
            return None
        
        recent_urls = list(self._url_history)
        
        for cycle_len in range(2, min(6, len(recent_urls) // 2 + 1)):
            pattern = recent_urls[-cycle_len:]
            prev_pattern = recent_urls[-2*cycle_len:-cycle_len]
            
            if pattern == prev_pattern:
                return LoopAlert(
                    loop_type=LoopType.URL_CYCLE,
                    count=cycle_len,
                    message=f"URL cycle detected: {' -> '.join(pattern[-3:])}",
                    suggestion=(
                        f"Detected a URL cycle of length {cycle_len}. "
                        "The browser is alternating between the same pages. "
                        "Consider:\n"
                        "1. Taking a different action on one of the pages\n"
                        "2. Skipping the current step\n"
                        "3. Navigating to a completely different URL"
                    ),
                    severity="warning",
                )
        
        return None
    
    def check_state_similarity(self) -> LoopAlert | None:
        """
        检测状态相似性
        
        Returns:
            LoopAlert 或 None
        """
        if len(self._page_history) < 3:
            return None
        
        recent_pages = list(self._page_history)[-5:]
        
        for i, page in enumerate(recent_pages[:-1]):
            for other in recent_pages[i+1:]:
                if page.url != other.url:
                    continue
                
                similarity = SequenceMatcher(
                    None,
                    page.content_hash,
                    other.content_hash,
                ).ratio()
                
                if similarity > self.config.similarity_threshold:
                    return LoopAlert(
                        loop_type=LoopType.STATE_SIMILAR,
                        count=2,
                        message=f"Similar page states detected at {page.url}",
                        suggestion=(
                            "The page state is very similar to a previous state. "
                            "This might indicate:\n"
                            "1. The action did not have the expected effect\n"
                            "2. The page needs to be refreshed\n"
                            "3. A different interaction approach is needed"
                        ),
                        severity="info",
                    )
        
        return None
    
    def detect(self) -> list[LoopAlert]:
        """
        执行所有循环检测
        
        Returns:
            检测到的警告列表
        """
        alerts = []
        
        action_alert = self.check_action_loop()
        if action_alert:
            alerts.append(action_alert)
        
        page_alert = self.check_page_stagnant()
        if page_alert:
            alerts.append(page_alert)
        
        url_alert = self.check_url_cycle()
        if url_alert:
            alerts.append(url_alert)
        
        similarity_alert = self.check_state_similarity()
        if similarity_alert:
            alerts.append(similarity_alert)
        
        self._alerts.extend(alerts)
        
        return alerts
    
    def has_loop(self) -> bool:
        """检查是否存在循环"""
        alerts = self.detect()
        return any(alert.severity == "warning" for alert in alerts)
    
    def get_suggestions(self) -> list[str]:
        """获取所有建议"""
        alerts = self.detect()
        return [alert.suggestion for alert in alerts]
    
    def get_alerts(self) -> list[LoopAlert]:
        """获取所有警告"""
        return self._alerts.copy()
    
    def clear_alerts(self) -> None:
        """清除警告历史"""
        self._alerts.clear()
    
    def reset(self) -> None:
        """重置检测器状态"""
        self._action_history.clear()
        self._page_history.clear()
        self._url_history.clear()
        self._alerts.clear()
        logger.info("Loop detector reset")
    
    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_actions": len(self._action_history),
            "total_pages": len(self._page_history),
            "unique_urls": len(set(self._url_history)),
            "total_alerts": len(self._alerts),
            "alerts_by_type": {
                loop_type.value: sum(
                    1 for a in self._alerts if a.loop_type == loop_type
                )
                for loop_type in LoopType
            },
        }
