"""
PyAgent 文档编辑器模块 - 文档工具

实现统一工具接口，支持文档创建、编辑、分析和AI辅助。
"""

from typing import Any

from src.document.connector import EditorConfig, OnlyOfficeConfig, OnlyOfficeConnector
from src.document.manager import DocumentManager, document_manager
from src.document.types import DocumentStatus, DocumentType
from src.tools.base import ToolContext, ToolResult, ToolState, UnifiedTool


class DocumentTool(UnifiedTool):
    """文档工具

    继承UnifiedTool，实现文档操作的三阶段调用模型。
    """

    name = "document_tool"
    description = "文档编辑器工具，支持创建、编辑、分析和AI辅助文档操作"

    def __init__(self, device_id: str = "", onlyoffice_config: OnlyOfficeConfig | None = None):
        super().__init__(device_id)
        self._manager: DocumentManager | None = None
        self._connector: OnlyOfficeConnector | None = None
        self._onlyoffice_config = onlyoffice_config

    async def activate(self, context: ToolContext) -> bool:
        try:
            self._manager = document_manager

            if self._onlyoffice_config is None:
                self._onlyoffice_config = OnlyOfficeConfig()

            self._connector = OnlyOfficeConnector(self._onlyoffice_config)
            self._state = ToolState.ACTIVE

            return True
        except Exception:
            self._state = ToolState.ERROR
            return False

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        if self._manager is None:
            return ToolResult(success=False, error="工具未激活")

        action = kwargs.get("action", "")

        action_handlers = {
            "create_document": self._handle_create_document,
            "edit_document": self._handle_edit_document,
            "analyze_document": self._handle_analyze_document,
            "ai_assist": self._handle_ai_assist,
            "get_document": self._handle_get_document,
            "list_documents": self._handle_list_documents,
            "delete_document": self._handle_delete_document,
            "export_document": self._handle_export_document,
            "search_documents": self._handle_search_documents,
        }

        handler = action_handlers.get(action)
        if handler is None:
            return ToolResult(
                success=False,
                error=f"未知操作: {action}。支持的操作: {list(action_handlers.keys())}",
            )

        return await handler(kwargs)

    async def dormant(self, context: ToolContext) -> bool:
        try:
            if self._connector:
                await self._connector.close()

            self._connector = None
            self._state = ToolState.DORMANT
            return True
        except Exception:
            self._state = ToolState.ERROR
            return False

    async def _handle_create_document(self, kwargs: dict[str, Any]) -> ToolResult:
        document_type_str = kwargs.get("document_type", "word")
        name = kwargs.get("name", "未命名文档")
        content = kwargs.get("content")
        domain_id = kwargs.get("domain_id")
        author = kwargs.get("author", "")
        tags = kwargs.get("tags", [])

        try:
            document_type = DocumentType(document_type_str)
        except ValueError:
            return ToolResult(
                success=False,
                error=f"无效的文档类型: {document_type_str}。支持: word, excel, ppt",
            )

        content_bytes = content.encode() if isinstance(content, str) else content

        metadata = self._manager.create_document(
            document_type=document_type,
            name=name,
            content=content_bytes,
            domain_id=domain_id,
            author=author,
            tags=tags,
        )

        return ToolResult(
            success=True,
            output=f"文档创建成功: {metadata.name}",
            data=metadata.to_dict(),
        )

    async def _handle_edit_document(self, kwargs: dict[str, Any]) -> ToolResult:
        document_id = kwargs.get("document_id")
        if not document_id:
            return ToolResult(success=False, error="缺少document_id参数")

        metadata = self._manager.get_document(document_id)
        if metadata is None:
            return ToolResult(success=False, error=f"文档不存在: {document_id}")

        if self._connector is None:
            return ToolResult(success=False, error="ONLYOFFICE连接器未初始化")

        document_url = kwargs.get("document_url", "")
        if not document_url and metadata.file_path:
            document_url = f"file://{metadata.file_path}"

        user_id = kwargs.get("user_id", "default_user")
        user_name = kwargs.get("user_name", "User")

        editor_config = EditorConfig(
            mode="edit",
            callback_url=self._onlyoffice_config.callback_url if self._onlyoffice_config else "",
            user_id=user_id,
            user_name=user_name,
        )

        document_key = self._connector._generate_document_key(document_id, metadata.version)

        editor_url = await self._connector.get_editor_url(
            document_url=document_url,
            document_id=document_id,
            document_name=metadata.name,
            document_key=document_key,
            editor_config=editor_config,
        )

        metadata.status = DocumentStatus.EDITING
        metadata.update_timestamp()
        self._manager._save_documents()

        return ToolResult(
            success=True,
            output="编辑器URL已生成",
            data={
                "editor_url": editor_url,
                "document_id": document_id,
                "document_key": document_key,
            },
        )

    async def _handle_analyze_document(self, kwargs: dict[str, Any]) -> ToolResult:
        document_id = kwargs.get("document_id")
        if not document_id:
            return ToolResult(success=False, error="缺少document_id参数")

        metadata = self._manager.get_document(document_id)
        if metadata is None:
            return ToolResult(success=False, error=f"文档不存在: {document_id}")

        content = self._manager.get_document_content(document_id)
        if content is None:
            return ToolResult(success=False, error="无法读取文档内容")

        analysis_type = kwargs.get("analysis_type", "summary")

        analysis_result = {
            "document_id": document_id,
            "document_name": metadata.name,
            "document_type": metadata.document_type.value,
            "size": len(content),
            "version": metadata.version,
            "status": metadata.status.value,
            "analysis_type": analysis_type,
            "word_count": len(content) if content else 0,
            "created_at": metadata.created_at,
            "updated_at": metadata.updated_at,
            "author": metadata.author,
            "tags": metadata.tags,
        }

        return ToolResult(
            success=True,
            output=f"文档分析完成: {metadata.name}",
            data=analysis_result,
        )

    async def _handle_ai_assist(self, kwargs: dict[str, Any]) -> ToolResult:
        document_id = kwargs.get("document_id")
        if not document_id:
            return ToolResult(success=False, error="缺少document_id参数")

        metadata = self._manager.get_document(document_id)
        if metadata is None:
            return ToolResult(success=False, error=f"文档不存在: {document_id}")

        assist_type = kwargs.get("assist_type", "suggest")
        prompt = kwargs.get("prompt", "")

        assist_result = {
            "document_id": document_id,
            "document_name": metadata.name,
            "assist_type": assist_type,
            "prompt": prompt,
            "suggestions": [
                "建议1: 考虑添加更多细节到文档中",
                "建议2: 检查文档格式是否正确",
                "建议3: 添加适当的标题和章节",
            ],
            "ai_ready": True,
        }

        return ToolResult(
            success=True,
            output="AI辅助分析完成",
            data=assist_result,
        )

    async def _handle_get_document(self, kwargs: dict[str, Any]) -> ToolResult:
        document_id = kwargs.get("document_id")
        if not document_id:
            return ToolResult(success=False, error="缺少document_id参数")

        metadata = self._manager.get_document(document_id)
        if metadata is None:
            return ToolResult(success=False, error=f"文档不存在: {document_id}")

        include_content = kwargs.get("include_content", False)
        result_data: dict[str, Any] = {"metadata": metadata.to_dict()}

        if include_content:
            content = self._manager.get_document_content(document_id)
            result_data["content_size"] = len(content) if content else 0
            result_data["has_content"] = content is not None

        return ToolResult(
            success=True,
            output=f"获取文档成功: {metadata.name}",
            data=result_data,
        )

    async def _handle_list_documents(self, kwargs: dict[str, Any]) -> ToolResult:
        document_type_str = kwargs.get("document_type")
        status_str = kwargs.get("status")
        domain_id = kwargs.get("domain_id")
        tags = kwargs.get("tags")

        document_type = None
        if document_type_str:
            try:
                document_type = DocumentType(document_type_str)
            except ValueError:
                pass

        status = None
        if status_str:
            try:
                status = DocumentStatus(status_str)
            except ValueError:
                pass

        documents = self._manager.list_documents(
            document_type=document_type,
            status=status,
            domain_id=domain_id,
            tags=tags,
        )

        return ToolResult(
            success=True,
            output=f"找到 {len(documents)} 个文档",
            data={
                "count": len(documents),
                "documents": [doc.to_dict() for doc in documents],
            },
        )

    async def _handle_delete_document(self, kwargs: dict[str, Any]) -> ToolResult:
        document_id = kwargs.get("document_id")
        if not document_id:
            return ToolResult(success=False, error="缺少document_id参数")

        metadata = self._manager.get_document(document_id)
        if metadata is None:
            return ToolResult(success=False, error=f"文档不存在: {document_id}")

        doc_name = metadata.name

        success = self._manager.delete_document(document_id)

        if success:
            return ToolResult(
                success=True,
                output=f"文档已删除: {doc_name}",
                data={"document_id": document_id},
            )
        return ToolResult(
            success=False,
            error=f"删除文档失败: {document_id}",
        )

    async def _handle_export_document(self, kwargs: dict[str, Any]) -> ToolResult:
        document_id = kwargs.get("document_id")
        if not document_id:
            return ToolResult(success=False, error="缺少document_id参数")

        format = kwargs.get("format", "original")
        output_path = kwargs.get("output_path")

        try:
            exported_path = self._manager.export_document(
                document_id=document_id,
                format=format,
                output_path=output_path,
            )

            return ToolResult(
                success=True,
                output="文档导出成功",
                data={
                    "document_id": document_id,
                    "export_path": exported_path,
                    "format": format,
                },
            )
        except ValueError as e:
            return ToolResult(success=False, error=str(e))

    async def _handle_search_documents(self, kwargs: dict[str, Any]) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, error="缺少query参数")

        documents = self._manager.search_documents(query)

        return ToolResult(
            success=True,
            output=f"搜索到 {len(documents)} 个匹配文档",
            data={
                "query": query,
                "count": len(documents),
                "documents": [doc.to_dict() for doc in documents],
            },
        )

    def get_supported_actions(self) -> list[str]:
        return [
            "create_document",
            "edit_document",
            "analyze_document",
            "ai_assist",
            "get_document",
            "list_documents",
            "delete_document",
            "export_document",
            "search_documents",
        ]

    def get_action_schema(self, action: str) -> dict[str, Any]:
        schemas = {
            "create_document": {
                "action": "create_document",
                "params": {
                    "document_type": {"type": "string", "enum": ["word", "excel", "ppt"]},
                    "name": {"type": "string"},
                    "content": {"type": "string", "optional": True},
                    "domain_id": {"type": "string", "optional": True},
                    "author": {"type": "string", "optional": True},
                    "tags": {"type": "array", "items": "string", "optional": True},
                },
            },
            "edit_document": {
                "action": "edit_document",
                "params": {
                    "document_id": {"type": "string"},
                    "document_url": {"type": "string", "optional": True},
                    "user_id": {"type": "string", "optional": True},
                    "user_name": {"type": "string", "optional": True},
                },
            },
            "analyze_document": {
                "action": "analyze_document",
                "params": {
                    "document_id": {"type": "string"},
                    "analysis_type": {"type": "string", "optional": True},
                },
            },
            "ai_assist": {
                "action": "ai_assist",
                "params": {
                    "document_id": {"type": "string"},
                    "assist_type": {"type": "string", "optional": True},
                    "prompt": {"type": "string", "optional": True},
                },
            },
            "get_document": {
                "action": "get_document",
                "params": {
                    "document_id": {"type": "string"},
                    "include_content": {"type": "boolean", "optional": True},
                },
            },
            "list_documents": {
                "action": "list_documents",
                "params": {
                    "document_type": {"type": "string", "optional": True},
                    "status": {"type": "string", "optional": True},
                    "domain_id": {"type": "string", "optional": True},
                    "tags": {"type": "array", "items": "string", "optional": True},
                },
            },
            "delete_document": {
                "action": "delete_document",
                "params": {
                    "document_id": {"type": "string"},
                },
            },
            "export_document": {
                "action": "export_document",
                "params": {
                    "document_id": {"type": "string"},
                    "format": {"type": "string", "optional": True},
                    "output_path": {"type": "string", "optional": True},
                },
            },
            "search_documents": {
                "action": "search_documents",
                "params": {
                    "query": {"type": "string"},
                },
            },
        }
        return schemas.get(action, {})
