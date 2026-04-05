"""
PyAgent ClawHub Skill安装协议支持

ClawHub是一个便捷的Skill技能发现和安装协议。
支持通过URL快速安装Skill技能。

URL格式：
- clawhub://skill-name
- https://clawhub.io/skills/skill-name

Skill格式遵循SKILL.md规范。
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

CLAWHUB_REGISTRY_URL = "https://registry.clawhub.io"
CLAWHUB_API_URL = "https://api.clawhub.io"


@dataclass
class ClawHubSkillInfo:
    """ClawHub技能信息"""
    name: str
    description: str
    version: str
    author: str
    repository: str | None = None
    homepage: str | None = None
    skill_md_url: str | None = None
    scripts: dict[str, str] | None = None
    references: list[str] | None = None
    tags: list[str] | None = None
    license: str | None = None


@dataclass
class ClawHubInstallResult:
    """ClawHub安装结果"""
    success: bool
    skill_name: str = ""
    error: str | None = None
    skill_path: str | None = None
    skill_info: ClawHubSkillInfo | None = None


class ClawHubInstaller:
    """ClawHub Skill安装器

    支持从ClawHub注册表安装Skill技能。
    """

    def __init__(self, skills_dir: Path | None = None):
        """初始化安装器

        Args:
            skills_dir: 技能目录，默认为 skills/
        """
        self._skills_dir = skills_dir or Path("skills")
        self._http_client = httpx.AsyncClient(timeout=30.0)

    def parse_clawhub_url(self, url: str) -> str | None:
        """解析ClawHub URL

        支持格式：
        - clawhub://skill-name
        - https://clawhub.io/skills/skill-name
        - https://registry.clawhub.io/skills/skill-name

        Args:
            url: ClawHub URL

        Returns:
            技能名称，解析失败返回None
        """
        url = url.strip()

        if url.startswith("clawhub://"):
            return url[10:]

        if url.startswith("https://clawhub.io/skills/"):
            return url[len("https://clawhub.io/skills/"):]

        if url.startswith("https://registry.clawhub.io/skills/"):
            return url[len("https://registry.clawhub.io/skills/"):]

        if re.match(r"^[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)?$", url):
            return url

        return None

    async def fetch_skill_info(self, skill_name: str) -> ClawHubSkillInfo | None:
        """从ClawHub注册表获取技能信息

        Args:
            skill_name: 技能名称

        Returns:
            技能信息，获取失败返回None
        """
        try:
            response = await self._http_client.get(
                f"{CLAWHUB_REGISTRY_URL}/skills/{skill_name}"
            )

            if response.status_code == 404:
                logger.warning(f"ClawHub技能未找到: {skill_name}")
                return None

            response.raise_for_status()
            data = response.json()

            return ClawHubSkillInfo(
                name=data.get("name", skill_name),
                description=data.get("description", ""),
                version=data.get("version", "latest"),
                author=data.get("author", "unknown"),
                repository=data.get("repository"),
                homepage=data.get("homepage"),
                skill_md_url=data.get("skill_md_url") or data.get("skill", {}).get("url"),
                scripts=data.get("scripts"),
                references=data.get("references"),
                tags=data.get("tags"),
                license=data.get("license"),
            )

        except httpx.HTTPError as e:
            logger.error(f"获取ClawHub技能信息失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析ClawHub响应失败: {e}")
            return None

    async def install_from_clawhub(self, url: str) -> ClawHubInstallResult:
        """从ClawHub安装Skill技能

        Args:
            url: ClawHub URL或技能名称

        Returns:
            安装结果
        """
        skill_name = self.parse_clawhub_url(url)
        if not skill_name:
            return ClawHubInstallResult(
                success=False,
                error=f"无效的ClawHub URL: {url}"
            )

        skill_info = await self.fetch_skill_info(skill_name)
        if not skill_info:
            return ClawHubInstallResult(
                success=False,
                skill_name=skill_name,
                error=f"无法获取技能信息: {skill_name}"
            )

        try:
            skill_dir = self._skills_dir / skill_name.replace("/", "-")
            skill_dir.mkdir(parents=True, exist_ok=True)

            skill_md_content = await self._fetch_skill_md(skill_info)
            if not skill_md_content:
                skill_md_content = self._generate_skill_md(skill_info)

            skill_md_path = skill_dir / "SKILL.md"
            skill_md_path.write_text(skill_md_content, encoding="utf-8")

            if skill_info.scripts:
                scripts_dir = skill_dir / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                for script_name, script_content in skill_info.scripts.items():
                    script_path = scripts_dir / script_name
                    script_path.write_text(script_content, encoding="utf-8")

            if skill_info.references:
                refs_dir = skill_dir / "references"
                refs_dir.mkdir(exist_ok=True)
                for ref_url in skill_info.references:
                    try:
                        ref_response = await self._http_client.get(ref_url)
                        ref_response.raise_for_status()
                        ref_name = Path(urlparse(ref_url).path).name
                        ref_path = refs_dir / ref_name
                        ref_path.write_text(ref_response.text, encoding="utf-8")
                    except Exception as e:
                        logger.warning(f"下载参考文件失败 {ref_url}: {e}")

            logger.info(f"已从ClawHub安装技能: {skill_name}")

            return ClawHubInstallResult(
                success=True,
                skill_name=skill_info.name,
                skill_path=str(skill_dir),
                skill_info=skill_info,
            )

        except Exception as e:
            logger.error(f"安装技能失败: {e}")
            return ClawHubInstallResult(
                success=False,
                skill_name=skill_name,
                error=str(e)
            )

    async def _fetch_skill_md(self, skill_info: ClawHubSkillInfo) -> str | None:
        """获取SKILL.md内容"""
        if not skill_info.skill_md_url:
            return None

        try:
            response = await self._http_client.get(skill_info.skill_md_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"获取SKILL.md失败: {e}")
            return None

    def _generate_skill_md(self, skill_info: ClawHubSkillInfo) -> str:
        """生成SKILL.md内容"""
        frontmatter = f"""---
name: {skill_info.name}
description: {skill_info.description}
version: "{skill_info.version}"
author: {skill_info.author}
"""
        if skill_info.license:
            frontmatter += f"license: {skill_info.license}\n"
        if skill_info.tags:
            frontmatter += f"tags: {json.dumps(skill_info.tags)}\n"

        frontmatter += "---\n\n"

        body = f"# {skill_info.name}\n\n{skill_info.description}\n"

        if skill_info.repository:
            body += f"\n**仓库**: {skill_info.repository}\n"
        if skill_info.homepage:
            body += f"**主页**: {skill_info.homepage}\n"

        return frontmatter + body

    async def search_skills(self, query: str, limit: int = 10) -> list[ClawHubSkillInfo]:
        """搜索ClawHub技能

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            技能信息列表
        """
        try:
            response = await self._http_client.get(
                f"{CLAWHUB_API_URL}/search",
                params={"q": query, "limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(ClawHubSkillInfo(
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    version=item.get("version", ""),
                    author=item.get("author", ""),
                    tags=item.get("tags"),
                ))

            return results

        except Exception as e:
            logger.error(f"搜索ClawHub技能失败: {e}")
            return []

    async def list_popular_skills(self, limit: int = 20) -> list[ClawHubSkillInfo]:
        """获取热门技能列表

        Args:
            limit: 返回数量限制

        Returns:
            技能信息列表
        """
        try:
            response = await self._http_client.get(
                f"{CLAWHUB_API_URL}/popular",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("skills", []):
                results.append(ClawHubSkillInfo(
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    version=item.get("version", ""),
                    author=item.get("author", ""),
                    tags=item.get("tags"),
                ))

            return results

        except Exception as e:
            logger.error(f"获取热门技能列表失败: {e}")
            return []

    async def uninstall_skill(self, skill_name: str) -> bool:
        """卸载技能

        Args:
            skill_name: 技能名称

        Returns:
            是否成功
        """
        try:
            skill_dir = self._skills_dir / skill_name.replace("/", "-")
            if not skill_dir.exists():
                return False

            import shutil
            shutil.rmtree(skill_dir)

            logger.info(f"已卸载技能: {skill_name}")
            return True

        except Exception as e:
            logger.error(f"卸载技能失败: {e}")
            return False

    async def close(self) -> None:
        """关闭HTTP客户端"""
        await self._http_client.aclose()


_clawhub_installer: ClawHubInstaller | None = None


def get_clawhub_installer(skills_dir: Path | None = None) -> ClawHubInstaller:
    """获取ClawHub安装器单例

    Args:
        skills_dir: 技能目录

    Returns:
        ClawHubInstaller实例
    """
    global _clawhub_installer

    if _clawhub_installer is None:
        _clawhub_installer = ClawHubInstaller(skills_dir)

    return _clawhub_installer


async def install_from_clawhub(url: str) -> ClawHubInstallResult:
    """快捷方法：从ClawHub安装Skill技能

    Args:
        url: ClawHub URL

    Returns:
        安装结果
    """
    return await get_clawhub_installer().install_from_clawhub(url)
