"""
PyAgent 用户信息系统 - 用户管理器

参考MaiBot的PersonManager设计，管理所有用户。
"""

import json
from pathlib import Path
from typing import Any

from .person import Person


class PersonManager:
    """用户管理器"""

    def __init__(self, data_dir: str = "data/persons"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._persons: dict[str, Person] = {}
        self._load_all()

    def _get_person_key(self, user_id: str, platform: str) -> str:
        """获取用户键"""
        return f"{platform}:{user_id}"

    def _get_person_file(self, person_key: str) -> Path:
        """获取用户文件路径"""
        return self.data_dir / f"{person_key.replace(':', '_')}.json"

    def _load_all(self) -> None:
        """加载所有用户"""
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    person = Person.from_dict(data)
                    key = self._get_person_key(person.user_id, person.platform)
                    self._persons[key] = person
            except Exception:
                pass

    def _save_person(self, person: Person) -> None:
        """保存用户"""
        key = self._get_person_key(person.user_id, person.platform)
        file_path = self._get_person_file(key)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(person.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def register_person(
        self,
        user_id: str,
        platform: str = "unknown",
        nickname: str = "",
        alias: str = ""
    ) -> Person:
        """注册用户"""
        key = self._get_person_key(user_id, platform)

        if key in self._persons:
            person = self._persons[key]
            if nickname:
                person.nickname = nickname
            if alias:
                person.alias = alias
        else:
            person = Person(
                user_id=user_id,
                platform=platform,
                nickname=nickname,
                alias=alias
            )
            self._persons[key] = person

        self._save_person(person)
        return person

    def get_person(self, user_id: str, platform: str = "unknown") -> Person | None:
        """获取用户"""
        key = self._get_person_key(user_id, platform)
        return self._persons.get(key)

    def get_or_create(
        self,
        user_id: str,
        platform: str = "unknown",
        nickname: str = ""
    ) -> Person:
        """获取或创建用户"""
        person = self.get_person(user_id, platform)
        if not person:
            person = self.register_person(user_id, platform, nickname)
        return person

    def update_person(self, person: Person) -> None:
        """更新用户"""
        key = self._get_person_key(person.user_id, person.platform)
        self._persons[key] = person
        self._save_person(person)

    def add_memory_point(
        self,
        user_id: str,
        content: str,
        platform: str = "unknown",
        source: str = "",
        importance: int = 1
    ) -> None:
        """添加记忆点"""
        person = self.get_or_create(user_id, platform)
        person.add_memory_point(content, source, importance)
        self._save_person(person)

    def set_group_nickname(
        self,
        user_id: str,
        group_id: str,
        nickname: str,
        platform: str = "unknown"
    ) -> None:
        """设置群昵称"""
        person = self.get_or_create(user_id, platform)
        person.set_group_nickname(group_id, nickname)
        self._save_person(person)

    def get_all_persons(self) -> list[Person]:
        """获取所有用户"""
        return list(self._persons.values())

    def search_persons(self, keyword: str) -> list[Person]:
        """搜索用户"""
        results = []
        keyword_lower = keyword.lower()

        for person in self._persons.values():
            if (keyword_lower in person.nickname.lower() or
                keyword_lower in person.alias.lower() or
                keyword_lower in person.user_id.lower()):
                results.append(person)

        return results

    def delete_person(self, user_id: str, platform: str = "unknown") -> bool:
        """删除用户"""
        key = self._get_person_key(user_id, platform)

        if key not in self._persons:
            return False

        del self._persons[key]

        file_path = self._get_person_file(key)
        if file_path.exists():
            file_path.unlink()

        return True

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_persons = len(self._persons)
        total_memory_points = sum(
            len(p.memory_points) for p in self._persons.values()
        )

        platforms = {}
        for person in self._persons.values():
            platforms[person.platform] = platforms.get(person.platform, 0) + 1

        return {
            "total_persons": total_persons,
            "total_memory_points": total_memory_points,
            "platforms": platforms
        }


person_manager = PersonManager()
