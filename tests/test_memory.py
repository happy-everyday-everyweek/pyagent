"""
PyAgent 记忆系统测试
"""

import pytest

from src.memory import (
    ChatMemoryStorage,
    MemoryLevel,
    MemoryPriority,
    WorkMemoryStorage,
)


class TestChatMemoryStorage:
    """聊天记忆存储测试"""

    def test_create_storage(self, tmp_path):
        """测试创建存储"""
        storage = ChatMemoryStorage(data_dir=str(tmp_path / "chat"))
        assert storage is not None

    @pytest.mark.asyncio
    async def test_store_memory(self, tmp_path):
        """测试存储记忆"""
        storage = ChatMemoryStorage(data_dir=str(tmp_path / "chat"))
        
        entry = await storage.store(
            content="测试记忆内容",
            level=MemoryLevel.DAILY,
            source="test",
        )
        
        assert entry is not None
        assert entry.content == "测试记忆内容"
        assert entry.level == MemoryLevel.DAILY

    @pytest.mark.asyncio
    async def test_recall_all(self, tmp_path):
        """测试召回所有记忆"""
        storage = ChatMemoryStorage(data_dir=str(tmp_path / "chat"))
        
        await storage.store(content="记忆1", level=MemoryLevel.DAILY)
        await storage.store(content="记忆2", level=MemoryLevel.WEEKLY)
        
        memories = await storage.recall_all()
        assert len(memories) == 2


class TestWorkMemoryStorage:
    """工作记忆存储测试"""

    def test_create_storage(self, tmp_path):
        """测试创建存储"""
        storage = WorkMemoryStorage(data_dir=str(tmp_path / "work"))
        assert storage is not None

    @pytest.mark.asyncio
    async def test_create_project_domain(self, tmp_path):
        """测试创建项目记忆域"""
        storage = WorkMemoryStorage(data_dir=str(tmp_path / "work"))
        
        domain = await storage.create_project_domain(
            name="测试项目",
            description="测试项目描述",
            keywords=["测试", "项目"],
        )
        
        assert domain is not None
        assert domain.name == "测试项目"

    @pytest.mark.asyncio
    async def test_add_preference(self, tmp_path):
        """测试添加偏好"""
        storage = WorkMemoryStorage(data_dir=str(tmp_path / "work"))
        
        pref = await storage.add_preference(
            content="用户偏好测试",
            category="general",
        )
        
        assert pref is not None
        assert pref.content == "用户偏好测试"
