"""
PyAgent IM平台适配器 - 微信API客户端

提供与微信通道服务通信的HTTP API封装。
"""

import hashlib
import os
import time
from typing import Any

import httpx

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    AES = None
    pad = None

from .types import (
    CDNMedia,
    SendResult,
    UploadResult,
    WeChatAccount,
    WeChatContact,
    WeChatGroup,
    WeChatMessage,
    WeChatMessageSource,
    WeChatMessageType,
)


class WeChatAPIError(Exception):
    """微信API错误"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"WeChat API Error [{code}]: {message}")


class WeChatAPI:
    """微信API客户端"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict[str, Any]:
        """发送请求"""
        client = await self._get_client()
        response = await client.request(method, endpoint, **kwargs)
        data = response.json()

        if response.status_code != 200:
            raise WeChatAPIError(
                response.status_code,
                data.get("message", "Unknown error")
            )

        if data.get("code", 0) != 0:
            raise WeChatAPIError(
                data.get("code", -1),
                data.get("message", "API error")
            )

        return data.get("data", {})

    async def get_updates(
        self,
        account_id: str,
        timeout: int = 30
    ) -> list[WeChatMessage]:
        """长轮询获取新消息"""
        try:
            data = await self._request(
                "GET",
                "/message/poll",
                params={"account_id": account_id, "timeout": timeout},
                timeout=timeout + 5,
            )

            messages = []
            for item in data.get("messages", []):
                msg = self._parse_message(item)
                if msg:
                    messages.append(msg)

            return messages

        except httpx.TimeoutException:
            return []
        except WeChatAPIError:
            return []

    def _parse_message(self, data: dict[str, Any]) -> WeChatMessage | None:
        """解析消息数据"""
        try:
            msg_type_map = {
                1: WeChatMessageType.TEXT,
                2: WeChatMessageType.IMAGE,
                3: WeChatMessageType.VOICE,
                4: WeChatMessageType.FILE,
                5: WeChatMessageType.VIDEO,
                6: WeChatMessageType.LINK,
                7: WeChatMessageType.MINI_PROGRAM,
                8: WeChatMessageType.LOCATION,
                9: WeChatMessageType.SYSTEM,
            }

            msg_type_int = data.get("msg_type", 1)
            msg_type = msg_type_map.get(msg_type_int, WeChatMessageType.TEXT)

            source = WeChatMessageSource.PRIVATE
            group_id = None
            if data.get("is_group", False):
                source = WeChatMessageSource.GROUP
                group_id = data.get("group_id")

            return WeChatMessage(
                msg_id=str(data.get("msg_id", "")),
                sender_id=str(data.get("sender_id", "")),
                receiver_id=str(data.get("receiver_id", "")),
                msg_type=msg_type,
                content=data.get("content", ""),
                media_url=data.get("media_url"),
                source=source,
                group_id=group_id,
                timestamp=data.get("timestamp", 0),
                at_users=data.get("at_users", []),
                is_at_bot=data.get("is_at_bot", False),
                extra=data.get("extra", {}),
            )

        except Exception:
            return None

    async def send_message(
        self,
        account_id: str,
        receiver_id: str,
        msg_type: WeChatMessageType,
        content: str = "",
        media: CDNMedia | None = None,
        at_users: list[str] | None = None,
    ) -> SendResult:
        """发送消息"""
        try:
            payload: dict[str, Any] = {
                "account_id": account_id,
                "receiver_id": receiver_id,
                "msg_type": msg_type.value,
                "content": content,
            }

            if media:
                payload["media"] = {
                    "aes_key": media.aes_key,
                    "file_size": media.file_size,
                    "file_md5": media.file_md5,
                    "file_type": media.file_type,
                    "cdn_url": media.cdn_url,
                }

            if at_users:
                payload["at_users"] = at_users

            data = await self._request("POST", "/message/send", json=payload)

            return SendResult(
                success=True,
                msg_id=data.get("msg_id"),
                timestamp=int(time.time()),
            )

        except WeChatAPIError as e:
            return SendResult(
                success=False,
                error=e.message,
                timestamp=int(time.time()),
            )
        except Exception as e:
            return SendResult(
                success=False,
                error=str(e),
                timestamp=int(time.time()),
            )

    async def get_upload_url(
        self,
        account_id: str,
        file_md5: str,
        file_size: int,
        file_type: str,
    ) -> UploadResult:
        """获取CDN上传预签名URL"""
        try:
            data = await self._request(
                "POST",
                "/media/upload_url",
                json={
                    "account_id": account_id,
                    "file_md5": file_md5,
                    "file_size": file_size,
                    "file_type": file_type,
                },
            )

            return UploadResult(
                success=True,
                cdn_key=data.get("cdn_key"),
                aes_key=data.get("aes_key"),
                file_md5=file_md5,
                file_size=file_size,
            )

        except WeChatAPIError as e:
            return UploadResult(
                success=False,
                error=e.message,
            )
        except Exception as e:
            return UploadResult(
                success=False,
                error=str(e),
            )

    async def get_account(self, account_id: str) -> WeChatAccount | None:
        """获取账号信息"""
        try:
            data = await self._request(
                "GET",
                f"/account/{account_id}",
            )

            return WeChatAccount(
                account_id=account_id,
                nickname=data.get("nickname", ""),
                avatar=data.get("avatar", ""),
                login_status=data.get("login_status", False),
                qrcode_url=data.get("qrcode_url"),
                wxid=data.get("wxid", ""),
                alias=data.get("alias", ""),
                device_id=data.get("device_id", ""),
            )

        except WeChatAPIError:
            return None

    async def login(self, account_id: str) -> dict[str, Any]:
        """登录账号，返回二维码URL"""
        try:
            data = await self._request(
                "POST",
                "/account/login",
                json={"account_id": account_id},
            )
            return data
        except WeChatAPIError as e:
            return {"success": False, "error": e.message}

    async def logout(self, account_id: str) -> bool:
        """登出账号"""
        try:
            await self._request(
                "POST",
                "/account/logout",
                json={"account_id": account_id},
            )
            return True
        except WeChatAPIError:
            return False

    async def get_contact(
        self,
        account_id: str,
        wxid: str
    ) -> WeChatContact | None:
        """获取联系人信息"""
        try:
            data = await self._request(
                "GET",
                f"/contact/{wxid}",
                params={"account_id": account_id},
            )

            return WeChatContact(
                wxid=wxid,
                nickname=data.get("nickname", ""),
                alias=data.get("alias", ""),
                avatar=data.get("avatar", ""),
                remark=data.get("remark", ""),
                is_friend=data.get("is_friend", False),
                is_group=data.get("is_group", False),
                extra=data.get("extra", {}),
            )

        except WeChatAPIError:
            return None

    async def get_group(
        self,
        account_id: str,
        group_id: str
    ) -> WeChatGroup | None:
        """获取群组信息"""
        try:
            data = await self._request(
                "GET",
                f"/group/{group_id}",
                params={"account_id": account_id},
            )

            return WeChatGroup(
                group_id=group_id,
                group_name=data.get("group_name", ""),
                member_count=data.get("member_count", 0),
                owner_id=data.get("owner_id", ""),
                members=data.get("members", []),
                extra=data.get("extra", {}),
            )

        except WeChatAPIError:
            return None

    async def send_typing(
        self,
        account_id: str,
        receiver_id: str,
        typing: bool = True
    ) -> bool:
        """发送输入状态"""
        try:
            await self._request(
                "POST",
                "/message/typing",
                json={
                    "account_id": account_id,
                    "receiver_id": receiver_id,
                    "typing": typing,
                },
            )
            return True
        except WeChatAPIError:
            return False

    async def recall_message(
        self,
        account_id: str,
        msg_id: str
    ) -> bool:
        """撤回消息"""
        try:
            await self._request(
                "POST",
                "/message/recall",
                json={
                    "account_id": account_id,
                    "msg_id": msg_id,
                },
            )
            return True
        except WeChatAPIError:
            return False

    def _calculate_md5(self, file_path: str) -> str:
        """计算文件MD5"""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def _aes_encrypt(self, data: bytes, key: str) -> bytes:
        """AES-128-ECB加密"""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("pycryptodome not installed, cannot encrypt media files")
        key_bytes = key.encode("utf-8")[:16].ljust(16, b"\x00")
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        padded_data = pad(data, AES.block_size)
        return cipher.encrypt(padded_data)

    async def upload_media(
        self,
        account_id: str,
        file_path: str,
        file_type: str = "file"
    ) -> CDNMedia | None:
        """上传媒体文件到CDN

        Args:
            account_id: 账号ID
            file_path: 文件路径
            file_type: 文件类型 (image/video/file)

        Returns:
            CDNMedia对象，失败返回None
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        try:
            file_size = os.path.getsize(file_path)
            file_md5 = self._calculate_md5(file_path)
            file_name = os.path.basename(file_path)

            upload_result = await self.get_upload_url(
                account_id=account_id,
                file_md5=file_md5,
                file_size=file_size,
                file_type=file_type,
            )

            if not upload_result.success:
                print(f"Failed to get upload URL: {upload_result.error}")
                return None

            cdn_key = upload_result.cdn_key
            aes_key = upload_result.aes_key

            if not cdn_key or not aes_key:
                print("Missing cdn_key or aes_key in upload result")
                return None

            with open(file_path, "rb") as f:
                file_data = f.read()

            encrypted_data = self._aes_encrypt(file_data, aes_key)

            upload_url = f"{self.base_url}/cdn/upload/{cdn_key}"

            client = await self._get_client()
            response = await client.put(
                upload_url,
                content=encrypted_data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "X-File-MD5": file_md5,
                    "X-File-Size": str(file_size),
                },
            )

            if response.status_code != 200:
                print(f"CDN upload failed: {response.status_code}")
                return None

            return CDNMedia(
                aes_key=aes_key,
                file_size=file_size,
                file_md5=file_md5,
                file_type=file_type,
                cdn_url=cdn_key,
                file_name=file_name,
            )

        except Exception as e:
            print(f"Failed to upload media: {e}")
            return None

    async def check_login_status(self, account_id: str) -> dict[str, Any]:
        """检查登录状态

        Returns:
            dict包含: is_logged_in, nickname, wxid等
        """
        try:
            data = await self._request(
                "GET",
                f"/account/{account_id}/status",
            )
            return {
                "is_logged_in": data.get("is_logged_in", False),
                "nickname": data.get("nickname", ""),
                "wxid": data.get("wxid", ""),
                "avatar": data.get("avatar", ""),
            }
        except WeChatAPIError:
            return {"is_logged_in": False}

    async def get_qrcode(self, account_id: str) -> dict[str, Any]:
        """获取登录二维码

        Returns:
            dict包含: qrcode_url, expire_time
        """
        try:
            data = await self._request(
                "GET",
                f"/account/{account_id}/qrcode",
            )
            return {
                "qrcode_url": data.get("qrcode_url", ""),
                "expire_time": data.get("expire_time", 0),
            }
        except WeChatAPIError as e:
            return {"qrcode_url": "", "error": e.message}

    async def get_config(self, account_id: str) -> dict[str, Any]:
        """获取账号配置信息（包含输入状态票据等）

        Returns:
            dict包含: typing_ticket等配置
        """
        try:
            data = await self._request(
                "GET",
                f"/account/{account_id}/config",
            )
            return data
        except WeChatAPIError:
            return {}
