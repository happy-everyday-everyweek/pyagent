"""
PyAgent 用户信息系统测试
"""

import pytest
from datetime import datetime

from person.person import MemoryPoint, Person
from person.person_manager import PersonManager


class TestMemoryPoint:
    """测试记忆点"""

    def test_memory_point_creation(self):
        point = MemoryPoint(
            content="User likes Python",
            source="chat",
            importance=5
        )
        assert point.content == "User likes Python"
        assert point.source == "chat"
        assert point.importance == 5

    def test_memory_point_defaults(self):
        point = MemoryPoint(content="Simple memory")
        assert point.source == ""
        assert point.importance == 1
        assert point.created_at is not None

    def test_memory_point_to_dict(self):
        point = MemoryPoint(
            content="Test memory",
            source="test",
            importance=3
        )
        data = point.to_dict()
        assert data["content"] == "Test memory"
        assert data["source"] == "test"
        assert data["importance"] == 3

    def test_memory_point_from_dict(self):
        data = {
            "content": "Test memory",
            "source": "test",
            "importance": 3,
            "created_at": "2024-01-01T00:00:00"
        }
        point = MemoryPoint.from_dict(data)
        assert point.content == "Test memory"
        assert point.importance == 3


class TestPerson:
    """测试用户"""

    def test_person_creation(self):
        person = Person(
            user_id="user_001",
            platform="qq",
            nickname="TestUser",
            alias="Test Alias"
        )
        assert person.user_id == "user_001"
        assert person.platform == "qq"
        assert person.nickname == "TestUser"
        assert person.alias == "Test Alias"

    def test_person_defaults(self):
        person = Person(user_id="user_001", platform="qq")
        assert person.nickname == ""
        assert person.alias == ""
        assert person.memory_points == []
        assert person.group_nicknames == {}

    def test_add_memory_point(self):
        person = Person(user_id="user_001", platform="qq")
        person.add_memory_point("User likes Python", "chat", 5)

        assert len(person.memory_points) == 1
        assert person.memory_points[0].content == "User likes Python"

    def test_set_group_nickname(self):
        person = Person(user_id="user_001", platform="qq")
        person.set_group_nickname("group_001", "GroupNick")

        assert person.group_nicknames["group_001"] == "GroupNick"

    def test_get_group_nickname(self):
        person = Person(user_id="user_001", platform="qq")
        person.set_group_nickname("group_001", "GroupNick")

        nickname = person.get_group_nickname("group_001")
        assert nickname == "GroupNick"

    def test_get_group_nickname_not_set(self):
        person = Person(user_id="user_001", platform="qq")
        nickname = person.get_group_nickname("group_001")
        assert nickname == person.nickname

    def test_to_dict(self):
        person = Person(
            user_id="user_001",
            platform="qq",
            nickname="TestUser",
            alias="Test Alias"
        )
        person.add_memory_point("Test memory")

        data = person.to_dict()
        assert data["user_id"] == "user_001"
        assert data["platform"] == "qq"
        assert data["nickname"] == "TestUser"
        assert len(data["memory_points"]) == 1

    def test_from_dict(self):
        data = {
            "user_id": "user_001",
            "platform": "qq",
            "nickname": "TestUser",
            "alias": "Test Alias",
            "memory_points": [
                {
                    "content": "Test memory",
                    "source": "test",
                    "importance": 3,
                    "created_at": "2024-01-01T00:00:00"
                }
            ],
            "group_nicknames": {"group_001": "GroupNick"},
            "created_at": "2024-01-01T00:00:00"
        }
        person = Person.from_dict(data)
        assert person.user_id == "user_001"
        assert person.nickname == "TestUser"
        assert len(person.memory_points) == 1
        assert person.group_nicknames["group_001"] == "GroupNick"


class TestPersonManager:
    """测试用户管理器"""

    def setup_method(self):
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PersonManager(data_dir=self.temp_dir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_manager_creation(self):
        assert self.manager.data_dir == Path(self.temp_dir)
        assert self.manager._persons == {}

    def test_register_person(self):
        person = self.manager.register_person(
            user_id="user_001",
            platform="qq",
            nickname="TestUser"
        )
        assert person.user_id == "user_001"
        assert person.nickname == "TestUser"

    def test_register_existing_person(self):
        self.manager.register_person(
            user_id="user_001",
            platform="qq",
            nickname="Original"
        )
        person = self.manager.register_person(
            user_id="user_001",
            platform="qq",
            nickname="Updated"
        )
        assert person.nickname == "Updated"

    def test_get_person(self):
        self.manager.register_person(
            user_id="user_001",
            platform="qq",
            nickname="TestUser"
        )
        person = self.manager.get_person("user_001", "qq")
        assert person is not None
        assert person.nickname == "TestUser"

    def test_get_nonexistent_person(self):
        person = self.manager.get_person("nonexistent", "qq")
        assert person is None

    def test_get_or_create(self):
        person = self.manager.get_or_create(
            user_id="user_001",
            platform="qq",
            nickname="TestUser"
        )
        assert person is not None
        assert person.nickname == "TestUser"

        person2 = self.manager.get_or_create(
            user_id="user_001",
            platform="qq"
        )
        assert person2 == person

    def test_update_person(self):
        person = self.manager.register_person(
            user_id="user_001",
            platform="qq"
        )
        person.nickname = "Updated"
        self.manager.update_person(person)

        retrieved = self.manager.get_person("user_001", "qq")
        assert retrieved.nickname == "Updated"

    def test_add_memory_point(self):
        self.manager.register_person(
            user_id="user_001",
            platform="qq"
        )
        self.manager.add_memory_point(
            user_id="user_001",
            platform="qq",
            content="Test memory",
            source="chat",
            importance=5
        )
        person = self.manager.get_person("user_001", "qq")
        assert len(person.memory_points) == 1

    def test_set_group_nickname(self):
        self.manager.register_person(
            user_id="user_001",
            platform="qq"
        )
        self.manager.set_group_nickname(
            user_id="user_001",
            group_id="group_001",
            nickname="GroupNick",
            platform="qq"
        )
        person = self.manager.get_person("user_001", "qq")
        assert person.group_nicknames["group_001"] == "GroupNick"

    def test_get_all_persons(self):
        self.manager.register_person(user_id="user_001", platform="qq")
        self.manager.register_person(user_id="user_002", platform="qq")

        persons = self.manager.get_all_persons()
        assert len(persons) == 2

    def test_search_persons(self):
        self.manager.register_person(
            user_id="user_001",
            platform="qq",
            nickname="Python User"
        )
        self.manager.register_person(
            user_id="user_002",
            platform="qq",
            nickname="Java User"
        )

        results = self.manager.search_persons("Python")
        assert len(results) == 1
        assert results[0].nickname == "Python User"

    def test_delete_person(self):
        self.manager.register_person(
            user_id="user_001",
            platform="qq"
        )
        result = self.manager.delete_person("user_001", "qq")
        assert result is True
        assert self.manager.get_person("user_001", "qq") is None

    def test_delete_nonexistent_person(self):
        result = self.manager.delete_person("nonexistent", "qq")
        assert result is False

    def test_get_statistics(self):
        self.manager.register_person(user_id="user_001", platform="qq")
        self.manager.register_person(user_id="user_002", platform="wechat")
        self.manager.add_memory_point(
            user_id="user_001",
            platform="qq",
            content="Test memory"
        )

        stats = self.manager.get_statistics()
        assert stats["total_persons"] == 2
        assert stats["total_memory_points"] == 1
        assert "qq" in stats["platforms"]
        assert "wechat" in stats["platforms"]
