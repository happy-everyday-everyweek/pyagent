"""
PyAgent 文档编辑器模块 - ONLYOFFICE连接器

实现与ONLYOFFICE Docs服务的集成。
提供文档编辑URL生成和回调处理功能。
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import httpx


@dataclass
class OnlyOfficeConfig:
    """ONLYOFFICE配置"""
    server_url: str = "http://localhost:8080"
    secret_key: str = ""
    callback_url: str = ""
    jwt_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_url": self.server_url,
            "secret_key": self.secret_key,
            "callback_url": self.callback_url,
            "jwt_enabled": self.jwt_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OnlyOfficeConfig":
        return cls(
            server_url=data.get("server_url", "http://localhost:8080"),
            secret_key=data.get("secret_key", ""),
            callback_url=data.get("callback_url", ""),
            jwt_enabled=data.get("jwt_enabled", False),
        )


@dataclass
class EditorConfig:
    """编辑器配置"""
    mode: str = "edit"
    lang: str = "zh-CN"
    callback_url: str = ""
    user_id: str = ""
    user_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "lang": self.lang,
            "callbackUrl": self.callback_url,
            "user": {
                "id": self.user_id,
                "name": self.user_name,
            },
            "created": self.created_at,
        }


@dataclass
class CallbackData:
    """回调数据"""
    key: str
    status: int
    url: str = ""
    changesurl: str = ""
    history: dict[str, Any] = field(default_factory=dict)
    users: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    lastsave: str = ""
    notmodified: bool = False
    forcesavetype: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CallbackData":
        return cls(
            key=data.get("key", ""),
            status=data.get("status", 0),
            url=data.get("url", ""),
            changesurl=data.get("changesurl", ""),
            history=data.get("history", {}),
            users=data.get("users", []),
            actions=data.get("actions", []),
            lastsave=data.get("lastsave", ""),
            notmodified=data.get("notmodified", False),
            forcesavetype=data.get("forcesavetype", 0),
        )


class OnlyOfficeConnector:
    """ONLYOFFICE连接器

    负责与ONLYOFFICE Docs服务的通信。
    """

    CALLBACK_STATUS_EDITING = 1
    CALLBACK_STATUS_SAVED = 2
    CALLBACK_STATUS_CLOSED = 4
    CALLBACK_STATUS_FORCE_SAVE = 6
    CALLBACK_STATUS_CORRUPTED = 7

    def __init__(self, config: OnlyOfficeConfig | None = None):
        self.config = config or OnlyOfficeConfig()
        self._http_client = httpx.AsyncClient(timeout=30.0)

    def _generate_document_key(self, document_id: str, version: int) -> str:
        combined = f"{document_id}_{version}_{time.time()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _generate_jwt_token(self, payload: dict[str, Any]) -> str:
        if not self.config.jwt_enabled or not self.config.secret_key:
            return ""

        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = self._base64_encode(json.dumps(header))
        payload_b64 = self._base64_encode(json.dumps(payload))

        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.config.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"{message}.{signature}"

    def _base64_encode(self, data: str) -> str:
        import base64

        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    def _get_document_type(self, file_extension: str) -> str:
        type_map = {
            ".docx": "word",
            ".doc": "word",
            ".xlsx": "cell",
            ".xls": "cell",
            ".pptx": "slide",
            ".ppt": "slide",
        }
        return type_map.get(file_extension.lower(), "word")

    async def get_editor_url(
        self,
        document_url: str,
        document_id: str,
        document_name: str,
        document_key: str,
        editor_config: EditorConfig | None = None,
    ) -> str:
        if editor_config is None:
            editor_config = EditorConfig()

        file_extension = document_name.rsplit(".", 1)[-1] if "." in document_name else "docx"
        document_type = self._get_document_type(f".{file_extension}")

        config = {
            "document": {
                "fileType": file_extension,
                "key": document_key,
                "title": document_name,
                "url": document_url,
            },
            "documentType": document_type,
            "editorConfig": editor_config.to_dict(),
        }

        if self.config.jwt_enabled:
            token = self._generate_jwt_token(config)
            config["token"] = token

        editor_page = urljoin(self.config.server_url, "/web-apps/apps/api/documents/editor.html")

        return f"{editor_page}?_config={json.dumps(config)}"

    async def check_health(self) -> bool:
        try:
            health_url = urljoin(self.config.server_url, "/healthcheck")
            response = await self._http_client.get(health_url)
            return response.status_code == 200
        except Exception:
            return False

    async def convert_document(
        self,
        source_url: str,
        source_format: str,
        target_format: str,
        document_key: str,
    ) -> str | None:
        convert_url = urljoin(self.config.server_url, "/ConvertService.ashx")

        payload = {
            "async": False,
            "filetype": source_format,
            "key": document_key,
            "outputtype": target_format,
            "url": source_url,
        }

        if self.config.jwt_enabled:
            token = self._generate_jwt_token(payload)
            payload["token"] = token

        try:
            response = await self._http_client.post(
                convert_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("fileUrl")

            return None
        except Exception:
            return None

    def process_callback(self, callback_data: dict[str, Any]) -> dict[str, Any]:
        data = CallbackData.from_dict(callback_data)

        result: dict[str, Any] = {"error": 0}

        if data.status == self.CALLBACK_STATUS_SAVED:
            result["saved"] = True
            result["url"] = data.url

        elif data.status == self.CALLBACK_STATUS_EDITING:
            result["editing"] = True

        elif data.status == self.CALLBACK_STATUS_CLOSED:
            result["closed"] = True

        elif data.status == self.CALLBACK_STATUS_FORCE_SAVE:
            result["force_saved"] = True
            result["url"] = data.url

        elif data.status == self.CALLBACK_STATUS_CORRUPTED:
            result["error"] = 1
            result["message"] = "Document corrupted"

        return result

    async def close(self) -> None:
        await self._http_client.aclose()
