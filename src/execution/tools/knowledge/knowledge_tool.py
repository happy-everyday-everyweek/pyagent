"""
PyAgent 执行模块工具系统 - 百科知识检索工具

提供本地百科知识检索功能。
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..base import BaseTool, RiskLevel, ToolCategory, ToolParameter, ToolResult
from .zim_parser import ZimParser


@dataclass
class KnowledgeLibrary:
    """知识库信息"""
    id: str
    name: str
    path: Path
    size_mb: float
    article_count: int = 0
    version: str = ""
    language: str = "en"
    description: str = ""


class KnowledgeTool(BaseTool):
    """百科知识检索工具"""

    name = "knowledge_search"
    description = "从本地百科知识库中搜索和获取知识内容，支持离线使用"
    category = ToolCategory.KNOWLEDGE
    risk_level = RiskLevel.SAFE

    DATA_DIR = Path("data/knowledge")
    ZIM_DIR = DATA_DIR / "zim"
    COLLECTIONS_DIR = DATA_DIR

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._libraries: dict[str, KnowledgeLibrary] = {}
        self._parsers: dict[str, ZimParser] = {}
        self._wikipedia_options: list[dict] = []
        self._kiwix_categories: list[dict] = []
        self._load_collections()

        self._parameters = [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: search(搜索), get(获取文章), list(列出库), categories(分类)",
                required=True,
                enum=["search", "get", "list", "categories", "wikipedia_options"]
            ),
            ToolParameter(
                name="query",
                type="string",
                description="搜索关键词或文章URL",
                required=False
            ),
            ToolParameter(
                name="library_id",
                type="string",
                description="知识库ID，不指定则搜索所有库",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回结果数量限制",
                required=False,
                default=10
            )
        ]

    def _load_collections(self):
        """加载收藏数据"""
        wikipedia_path = self.COLLECTIONS_DIR / "wikipedia.json"
        if wikipedia_path.exists():
            try:
                with open(wikipedia_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self._wikipedia_options = data.get("options", [])
            except Exception:
                pass

        categories_path = self.COLLECTIONS_DIR / "kiwix-categories.json"
        if categories_path.exists():
            try:
                with open(categories_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self._kiwix_categories = data.get("categories", [])
            except Exception:
                pass

        self._scan_zim_files()

    def _scan_zim_files(self):
        """扫描ZIM文件"""
        if not self.ZIM_DIR.exists():
            return

        for zim_file in self.ZIM_DIR.glob("*.zim"):
            lib_id = zim_file.stem
            size_mb = zim_file.stat().st_size / (1024 * 1024)

            self._libraries[lib_id] = KnowledgeLibrary(
                id=lib_id,
                name=self._parse_library_name(zim_file.name),
                path=zim_file,
                size_mb=round(size_mb, 2)
            )

    def _parse_library_name(self, filename: str) -> str:
        """解析库名称"""
        name_map = {
            "wikipedia_en_top_mini": "Wikipedia Top 100K (Mini)",
            "wikipedia_en_top_nopic": "Wikipedia Popular (No Images)",
            "wikipedia_en_all_mini": "Wikipedia Complete (Compact)",
            "wikipedia_en_all_nopic": "Wikipedia Complete (No Images)",
            "wikipedia_en_all_maxi": "Wikipedia Complete (Full)",
            "wikipedia_en_medicine": "Wikipedia Medicine",
        }

        for key, name in name_map.items():
            if key in filename:
                return name

        return filename.replace(".zim", "").replace("_", " ").title()

    def _get_parser(self, library_id: str) -> ZimParser | None:
        """获取ZIM解析器"""
        if library_id in self._parsers:
            return self._parsers[library_id]

        if library_id not in self._libraries:
            return None

        lib = self._libraries[library_id]
        parser = ZimParser(str(lib.path))
        if parser.open():
            self._parsers[library_id] = parser
            return parser

        return None

    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        action = kwargs.get("action", "list")

        if action == "list":
            return self._list_libraries()
        if action == "categories":
            return self._list_categories()
        if action == "wikipedia_options":
            return self._list_wikipedia_options()
        if action == "search":
            return await self._search(kwargs)
        if action == "get":
            return await self._get_article(kwargs)
        return ToolResult(success=False, error=f"未知操作: {action}")

    def _list_libraries(self) -> ToolResult:
        """列出知识库"""
        libraries = []
        for lib_id, lib in self._libraries.items():
            parser = self._get_parser(lib_id)
            article_count = 0
            if parser:
                info = parser.get_info()
                article_count = info.get("article_count", 0)

            libraries.append({
                "id": lib.id,
                "name": lib.name,
                "size_mb": lib.size_mb,
                "article_count": article_count,
                "path": str(lib.path)
            })

        return ToolResult(
            success=True,
            output=f"找到 {len(libraries)} 个知识库",
            data={"libraries": libraries}
        )

    def _list_categories(self) -> ToolResult:
        """列出Kiwix分类"""
        categories = []
        for cat in self._kiwix_categories:
            categories.append({
                "name": cat.get("name", ""),
                "slug": cat.get("slug", ""),
                "description": cat.get("description", ""),
                "icon": cat.get("icon", ""),
                "tier_count": len(cat.get("tiers", []))
            })

        return ToolResult(
            success=True,
            output=f"找到 {len(categories)} 个知识分类",
            data={"categories": categories}
        )

    def _list_wikipedia_options(self) -> ToolResult:
        """列出Wikipedia选项"""
        options = []
        for opt in self._wikipedia_options:
            options.append({
                "id": opt.get("id", ""),
                "name": opt.get("name", ""),
                "description": opt.get("description", ""),
                "size_mb": opt.get("size_mb", 0),
                "version": opt.get("version", "")
            })

        return ToolResult(
            success=True,
            output=f"找到 {len(options)} 个Wikipedia选项",
            data={"options": options}
        )

    async def _search(self, kwargs: dict) -> ToolResult:
        """搜索知识"""
        query = kwargs.get("query", "")
        library_id = kwargs.get("library_id")
        limit = kwargs.get("limit", 10)

        if not query:
            return ToolResult(success=False, error="请提供搜索关键词")

        results = []

        if library_id:
            libs_to_search = [library_id] if library_id in self._libraries else []
        else:
            libs_to_search = list(self._libraries.keys())

        if not libs_to_search:
            return ToolResult(
                success=False,
                error="没有可用的知识库，请先下载ZIM文件到 data/knowledge/zim/ 目录"
            )

        for lib_id in libs_to_search:
            parser = self._get_parser(lib_id)
            if not parser:
                continue

            articles = parser.search(query, limit)
            for article in articles:
                results.append({
                    "library_id": lib_id,
                    "library_name": self._libraries[lib_id].name,
                    "title": article.title,
                    "url": article.url,
                    "index": article.index
                })

            if len(results) >= limit:
                break

        return ToolResult(
            success=True,
            output=f"找到 {len(results)} 条结果",
            data={"results": results[:limit], "query": query}
        )

    async def _get_article(self, kwargs: dict) -> ToolResult:
        """获取文章内容"""
        library_id = kwargs.get("library_id")
        query = kwargs.get("query", "")

        if not query:
            return ToolResult(success=False, error="请提供文章URL或标题")

        if not library_id:
            if len(self._libraries) > 0:
                library_id = list(self._libraries.keys())[0]
            else:
                return ToolResult(success=False, error="没有可用的知识库")

        parser = self._get_parser(library_id)
        if not parser:
            return ToolResult(success=False, error=f"无法打开知识库: {library_id}")

        article = parser.get_article_by_url(query)
        if not article:
            articles = parser.search(query, 1)
            if articles:
                article = parser.get_article(articles[0].index)

        if not article:
            return ToolResult(success=False, error="未找到文章")

        content = ""
        if article.content:
            try:
                content = article.content.decode("utf-8", errors="ignore")
            except Exception:
                content = str(article.content[:1000])

        return ToolResult(
            success=True,
            output=f"文章: {article.title}",
            data={
                "title": article.title,
                "url": article.url,
                "content_type": article.content_type,
                "content": content[:10000],
                "library_id": library_id
            }
        )
