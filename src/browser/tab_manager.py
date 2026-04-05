"""
PyAgent 浏览器自动化模块 - 标签页管理器

提供多标签页管理功能。
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TabInfo:
    """标签页信息"""
    tab_id: str
    url: str
    title: str = ""
    is_active: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tab_id": self.tab_id,
            "url": self.url,
            "title": self.title,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }


class TabManager:
    """标签页管理器"""

    def __init__(self, controller):
        """
        初始化标签页管理器

        Args:
            controller: BrowserController实例
        """
        self._controller = controller
        self._tabs: dict[str, TabInfo] = {}
        self._active_tab_id: str | None = None

    @property
    def context(self):
        return self._controller.context

    @property
    def page(self):
        return self._controller.page

    async def new_tab(
        self,
        url: str = "about:blank",
        activate: bool = True
    ) -> TabInfo:
        """
        打开新标签页

        Args:
            url: 初始URL
            activate: 是否激活新标签页

        Returns:
            TabInfo: 标签页信息
        """
        if not self.context:
            raise RuntimeError("浏览器上下文未初始化")

        try:
            new_page = await self.context.new_page()

            tab_id = str(uuid.uuid4())[:8]

            await new_page.goto(url)

            title = await new_page.title()

            tab_info = TabInfo(
                tab_id=tab_id,
                url=url,
                title=title,
                is_active=activate
            )

            self._tabs[tab_id] = tab_info

            if activate:
                if self._active_tab_id and self._active_tab_id in self._tabs:
                    self._tabs[self._active_tab_id].is_active = False
                self._active_tab_id = tab_id
                self._controller._page = new_page

            logger.info(f"新标签页已打开: {tab_id} - {url}")

            return tab_info

        except Exception as e:
            logger.error(f"打开新标签页失败: {e}")
            raise

    async def close_tab(self, tab_id: str) -> bool:
        """
        关闭标签页

        Args:
            tab_id: 标签页ID

        Returns:
            bool: 是否成功关闭
        """
        if tab_id not in self._tabs:
            logger.warning(f"标签页不存在: {tab_id}")
            return False

        try:
            pages = self.context.pages

            tab_info = self._tabs[tab_id]

            for page in pages:
                if page.url == tab_info.url:
                    await page.close()
                    break

            del self._tabs[tab_id]

            if self._active_tab_id == tab_id:
                remaining_tabs = list(self._tabs.keys())
                if remaining_tabs:
                    await self.switch_tab(remaining_tabs[0])
                else:
                    self._active_tab_id = None
                    self._controller._page = None

            logger.info(f"标签页已关闭: {tab_id}")

            return True

        except Exception as e:
            logger.error(f"关闭标签页失败: {e}")
            return False

    async def switch_tab(self, tab_id: str) -> bool:
        """
        切换到指定标签页

        Args:
            tab_id: 标签页ID

        Returns:
            bool: 是否成功切换
        """
        if tab_id not in self._tabs:
            logger.warning(f"标签页不存在: {tab_id}")
            return False

        try:
            tab_info = self._tabs[tab_id]

            pages = self.context.pages

            target_page = None
            for page in pages:
                if page.url == tab_info.url:
                    target_page = page
                    break

            if not target_page:
                logger.warning(f"未找到标签页对应的页面: {tab_id}")
                return False

            if self._active_tab_id and self._active_tab_id in self._tabs:
                self._tabs[self._active_tab_id].is_active = False

            self._tabs[tab_id].is_active = True
            self._active_tab_id = tab_id
            self._controller._page = target_page

            await target_page.bring_to_front()

            tab_info.url = target_page.url
            tab_info.title = await target_page.title()

            logger.info(f"已切换到标签页: {tab_id}")

            return True

        except Exception as e:
            logger.error(f"切换标签页失败: {e}")
            return False

    async def get_tabs(self) -> list[TabInfo]:
        """
        获取所有标签页信息

        Returns:
            list[TabInfo]: 标签页列表
        """
        if not self.context:
            return []

        try:
            pages = self.context.pages

            for page in pages:
                url = page.url
                for _, tab_info in self._tabs.items():
                    if tab_info.url == url:
                        tab_info.title = await page.title()
                        tab_info.url = url
                        break

            return list(self._tabs.values())

        except Exception as e:
            logger.error(f"获取标签页列表失败: {e}")
            return []

    async def get_active_tab(self) -> TabInfo | None:
        """
        获取当前活动标签页

        Returns:
            TabInfo | None: 活动标签页信息
        """
        if not self._active_tab_id:
            return None

        return self._tabs.get(self._active_tab_id)

    async def get_tab_by_url(self, url: str) -> TabInfo | None:
        """
        通过URL获取标签页

        Args:
            url: 页面URL

        Returns:
            TabInfo | None: 标签页信息
        """
        for tab_info in self._tabs.values():
            if tab_info.url == url:
                return tab_info
        return None

    async def get_tab_by_title(self, title: str) -> TabInfo | None:
        """
        通过标题获取标签页

        Args:
            title: 页面标题

        Returns:
            TabInfo | None: 标签页信息
        """
        for tab_info in self._tabs.values():
            if title in tab_info.title:
                return tab_info
        return None

    async def close_all_tabs(self) -> int:
        """
        关闭所有标签页

        Returns:
            int: 关闭的标签页数量
        """
        if not self.context:
            return 0

        try:
            pages = self.context.pages
            closed_count = 0

            for page in pages:
                try:
                    await page.close()
                    closed_count += 1
                except Exception:
                    pass

            self._tabs.clear()
            self._active_tab_id = None
            self._controller._page = None

            logger.info(f"已关闭所有标签页: {closed_count}个")

            return closed_count

        except Exception as e:
            logger.error(f"关闭所有标签页失败: {e}")
            return 0

    async def duplicate_tab(self, tab_id: str | None = None) -> TabInfo | None:
        """
        复制标签页

        Args:
            tab_id: 要复制的标签页ID，None则复制当前标签页

        Returns:
            TabInfo | None: 新标签页信息
        """
        if tab_id is None:
            tab_id = self._active_tab_id

        if not tab_id or tab_id not in self._tabs:
            logger.warning(f"标签页不存在: {tab_id}")
            return None

        try:
            source_tab = self._tabs[tab_id]
            return await self.new_tab(url=source_tab.url)

        except Exception as e:
            logger.error(f"复制标签页失败: {e}")
            return None

    async def reload_tab(self, tab_id: str | None = None) -> bool:
        """
        刷新标签页

        Args:
            tab_id: 标签页ID，None则刷新当前标签页

        Returns:
            bool: 是否成功刷新
        """
        if tab_id is None:
            tab_id = self._active_tab_id

        if not tab_id or tab_id not in self._tabs:
            logger.warning(f"标签页不存在: {tab_id}")
            return False

        try:
            was_active = tab_id == self._active_tab_id

            if not was_active:
                await self.switch_tab(tab_id)

            if self.page:
                await self.page.reload()

                self._tabs[tab_id].title = await self.page.title()
                self._tabs[tab_id].url = self.page.url

            logger.info(f"标签页已刷新: {tab_id}")

            return True

        except Exception as e:
            logger.error(f"刷新标签页失败: {e}")
            return False

    async def go_back_in_tab(self, tab_id: str | None = None) -> bool:
        """
        在标签页中后退

        Args:
            tab_id: 标签页ID

        Returns:
            bool: 是否成功后退
        """
        if tab_id is None:
            tab_id = self._active_tab_id

        if not tab_id or tab_id not in self._tabs:
            return False

        try:
            was_active = tab_id == self._active_tab_id

            if not was_active:
                await self.switch_tab(tab_id)

            if self.page:
                result = await self.page.go_back()
                if result:
                    self._tabs[tab_id].url = self.page.url
                    self._tabs[tab_id].title = await self.page.title()
                return result is not None

            return False

        except Exception as e:
            logger.error(f"后退失败: {e}")
            return False

    async def go_forward_in_tab(self, tab_id: str | None = None) -> bool:
        """
        在标签页中前进

        Args:
            tab_id: 标签页ID

        Returns:
            bool: 是否成功前进
        """
        if tab_id is None:
            tab_id = self._active_tab_id

        if not tab_id or tab_id not in self._tabs:
            return False

        try:
            was_active = tab_id == self._active_tab_id

            if not was_active:
                await self.switch_tab(tab_id)

            if self.page:
                result = await self.page.go_forward()
                if result:
                    self._tabs[tab_id].url = self.page.url
                    self._tabs[tab_id].title = await self.page.title()
                return result is not None

            return False

        except Exception as e:
            logger.error(f"前进失败: {e}")
            return False

    async def get_tab_history(
        self,
        tab_id: str | None = None
    ) -> list[dict[str, str]]:
        """
        获取标签页历史记录

        Args:
            tab_id: 标签页ID

        Returns:
            list[dict[str, str]]: 历史记录列表
        """
        if tab_id is None:
            tab_id = self._active_tab_id

        if not tab_id or tab_id not in self._tabs:
            return []

        try:
            was_active = tab_id == self._active_tab_id

            if not was_active:
                await self.switch_tab(tab_id)

            if self.page:
                history = await self.page.evaluate("""
                    () => {
                        const history = [];
                        for (let i = 0; i < window.history.length; i++) {
                            history.push({
                                index: i,
                                url: window.location.href
                            });
                        }
                        return history;
                    }
                """)
                return history

            return []

        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return []

    def register_current_tab(self) -> TabInfo:
        """
        注册当前标签页（用于初始化时）

        Returns:
            TabInfo: 标签页信息
        """
        if not self.page:
            raise RuntimeError("浏览器页面未初始化")

        tab_id = str(uuid.uuid4())[:8]

        tab_info = TabInfo(
            tab_id=tab_id,
            url=self.page.url,
            title="",
            is_active=True
        )

        self._tabs[tab_id] = tab_info
        self._active_tab_id = tab_id

        return tab_info

    def get_tab_count(self) -> int:
        """
        获取标签页数量

        Returns:
            int: 标签页数量
        """
        return len(self._tabs)
