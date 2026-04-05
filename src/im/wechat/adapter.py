"""
PyAgent IM平台适配器 - 微信适配器

实现微信通道的适配器，继承BaseIMAdapter基类。
"""

import asyncio
import hashlib
import os
from typing import Any

from ..base import (
    BaseIMAdapter,
    ChatType,
    IMMessage,
    IMReply,
    IMUser,
    MessageType,
)
from .api import WeChatAPI
from .types import (
    CDNMedia,
    SendResult,
    WeChatAccount,
    WeChatMessage,
    WeChatMessageSource,
    WeChatMessageType,
)


class WeChatAdapter(BaseIMAdapter):
    """微信适配器"""

    platform = "wechat"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)

        base_url = self.config.get("base_url", "")
        timeout = self.config.get("timeout", 30)

        self.api = WeChatAPI(base_url, timeout)
        self._accounts: dict[str, WeChatAccount] = {}
        self._poll_task: asyncio.Task | None = None
        self._poll_interval = self.config.get("poll_interval", 30)
        self._typing_tickets: dict[str, str] = {}
        self._context_stores: dict[str, dict[str, Any]] = {}
        self._context_isolation: dict[str, bool] = {}

    async def connect(self) -> bool:
        """连接到微信通道服务"""
        if not self.api.base_url:
            print("WeChat base_url not configured")
            return False

        account_configs = self.config.get("accounts", [])
        if not account_configs:
            print("No WeChat accounts configured")
            return False

        for account_config in account_configs:
            if isinstance(account_config, dict):
                account_id = account_config.get("account_id", "")
                context_isolation = account_config.get("context_isolation", True)
            else:
                account_id = account_config
                context_isolation = True

            if account_id:
                account = await self.api.get_account(account_id)
                if account:
                    self._accounts[account_id] = account
                    self._context_isolation[account_id] = context_isolation

        self._connected = True
        self._poll_task = asyncio.create_task(self._poll_loop())

        print(f"Connected to WeChat service: {self.api.base_url}")
        return True

    async def disconnect(self) -> None:
        """断开连接"""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        await self.api.close()
        self._connected = False
        print("Disconnected from WeChat service")

    async def _poll_loop(self) -> None:
        """轮询消息循环"""
        while self._connected:
            try:
                for account_id in self._accounts:
                    messages = await self.api.get_updates(
                        account_id,
                        timeout=self._poll_interval
                    )

                    for msg in messages:
                        im_msg = self._convert_message(msg, account_id)
                        if im_msg:
                            await self._dispatch_message(im_msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"WeChat poll error: {e}")
                await asyncio.sleep(5)

    def _convert_message(
        self,
        msg: WeChatMessage,
        account_id: str
    ) -> IMMessage | None:
        """转换微信消息为统一消息格式"""
        try:
            msg_type_map = {
                WeChatMessageType.TEXT: MessageType.TEXT,
                WeChatMessageType.IMAGE: MessageType.IMAGE,
                WeChatMessageType.VOICE: MessageType.AUDIO,
                WeChatMessageType.VIDEO: MessageType.VIDEO,
                WeChatMessageType.FILE: MessageType.FILE,
                WeChatMessageType.LINK: MessageType.CARD,
                WeChatMessageType.SYSTEM: MessageType.SYSTEM,
            }

            message_type = msg_type_map.get(msg.msg_type, MessageType.TEXT)

            chat_type = ChatType.PRIVATE
            chat_id = msg.sender_id

            if msg.source == WeChatMessageSource.GROUP and msg.group_id:
                chat_type = ChatType.GROUP
                chat_id = msg.group_id

            return IMMessage(
                message_id=msg.msg_id,
                platform=self.platform,
                chat_id=chat_id,
                chat_type=chat_type,
                sender=IMUser(
                    user_id=msg.sender_id,
                    extra={"account_id": account_id},
                ),
                content=msg.content,
                message_type=message_type,
                timestamp=msg.timestamp,
                at_users=msg.at_users,
                is_at_bot=msg.is_at_bot,
                extra={
                    "media_url": msg.media_url,
                    "receiver_id": msg.receiver_id,
                    "account_id": account_id,
                },
            )

        except Exception as e:
            print(f"Failed to convert WeChat message: {e}")
            return None

    async def send_message(
        self,
        chat_id: str,
        reply: IMReply
    ) -> bool:
        """发送消息"""
        if not self._connected or not self._accounts:
            return False

        account_id = reply.extra.get("account_id")
        if not account_id:
            account_id = list(self._accounts.keys())[0]

        msg_type = self._convert_msg_type(reply.message_type)

        result: SendResult
        if reply.message_type == MessageType.TEXT:
            result = await self.api.send_message(
                account_id=account_id,
                receiver_id=chat_id,
                msg_type=msg_type,
                content=reply.content,
                at_users=reply.at_users if reply.at_users else None,
            )
        else:
            media = reply.extra.get("media")
            result = await self.api.send_message(
                account_id=account_id,
                receiver_id=chat_id,
                msg_type=msg_type,
                content=reply.content,
                media=media,
            )

        return result.success

    def _convert_msg_type(self, msg_type: MessageType) -> WeChatMessageType:
        """转换消息类型"""
        type_map = {
            MessageType.TEXT: WeChatMessageType.TEXT,
            MessageType.IMAGE: WeChatMessageType.IMAGE,
            MessageType.AUDIO: WeChatMessageType.VOICE,
            MessageType.VIDEO: WeChatMessageType.VIDEO,
            MessageType.FILE: WeChatMessageType.FILE,
            MessageType.CARD: WeChatMessageType.LINK,
        }
        return type_map.get(msg_type, WeChatMessageType.TEXT)

    async def get_user_info(self, user_id: str) -> IMUser | None:
        """获取用户信息"""
        if not self._accounts:
            return IMUser(user_id=user_id)

        account_id = list(self._accounts.keys())[0]
        contact = await self.api.get_contact(account_id, user_id)

        if contact:
            return IMUser(
                user_id=user_id,
                name=contact.nickname,
                nickname=contact.nickname,
                avatar=contact.avatar,
                extra={"remark": contact.remark, "alias": contact.alias},
            )

        return IMUser(user_id=user_id)

    async def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """获取聊天信息"""
        if not self._accounts:
            return {"chat_id": chat_id}

        account_id = list(self._accounts.keys())[0]

        if chat_id.endswith("@chatroom"):
            group = await self.api.get_group(account_id, chat_id)
            if group:
                return {
                    "chat_id": chat_id,
                    "name": group.group_name,
                    "member_count": group.member_count,
                    "owner_id": group.owner_id,
                    "members": group.members,
                }

        contact = await self.api.get_contact(account_id, chat_id)
        if contact:
            return {
                "chat_id": chat_id,
                "name": contact.nickname,
                "avatar": contact.avatar,
            }

        return {"chat_id": chat_id}

    async def login(self, account_id: str) -> str:
        """登录账号，返回二维码URL"""
        result = await self.api.login(account_id)

        if result.get("success", False):
            qrcode_url = result.get("qrcode_url", "")

            account = WeChatAccount(
                account_id=account_id,
                qrcode_url=qrcode_url,
            )
            self._accounts[account_id] = account

            return qrcode_url

        return ""

    async def logout(self, account_id: str) -> bool:
        """登出账号"""
        success = await self.api.logout(account_id)

        if success and account_id in self._accounts:
            del self._accounts[account_id]

        return success

    async def send_text(
        self,
        account_id: str,
        receiver_id: str,
        text: str,
        at_users: list[str] | None = None
    ) -> bool:
        """发送文本消息"""
        result = await self.api.send_message(
            account_id=account_id,
            receiver_id=receiver_id,
            msg_type=WeChatMessageType.TEXT,
            content=text,
            at_users=at_users,
        )
        return result.success

    async def send_image(
        self,
        account_id: str,
        receiver_id: str,
        image_path: str
    ) -> bool:
        """发送图片消息"""
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False

        try:
            file_size = os.path.getsize(image_path)
            file_md5 = self._calculate_md5(image_path)

            upload_result = await self.api.get_upload_url(
                account_id=account_id,
                file_md5=file_md5,
                file_size=file_size,
                file_type="image",
            )

            if not upload_result.success:
                print(f"Failed to get upload URL: {upload_result.error}")
                return False

            media = CDNMedia(
                aes_key=upload_result.aes_key or "",
                file_size=file_size,
                file_md5=file_md5,
                file_type="image",
            )

            result = await self.api.send_message(
                account_id=account_id,
                receiver_id=receiver_id,
                msg_type=WeChatMessageType.IMAGE,
                media=media,
            )

            return result.success

        except Exception as e:
            print(f"Failed to send image: {e}")
            return False

    async def send_file(
        self,
        account_id: str,
        receiver_id: str,
        file_path: str
    ) -> bool:
        """发送文件消息"""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        try:
            file_size = os.path.getsize(file_path)
            file_md5 = self._calculate_md5(file_path)
            file_name = os.path.basename(file_path)

            upload_result = await self.api.get_upload_url(
                account_id=account_id,
                file_md5=file_md5,
                file_size=file_size,
                file_type="file",
            )

            if not upload_result.success:
                print(f"Failed to get upload URL: {upload_result.error}")
                return False

            media = CDNMedia(
                aes_key=upload_result.aes_key or "",
                file_size=file_size,
                file_md5=file_md5,
                file_type="file",
                file_name=file_name,
            )

            result = await self.api.send_message(
                account_id=account_id,
                receiver_id=receiver_id,
                msg_type=WeChatMessageType.FILE,
                content=file_name,
                media=media,
            )

            return result.success

        except Exception as e:
            print(f"Failed to send file: {e}")
            return False

    def _calculate_md5(self, file_path: str) -> str:
        """计算文件MD5"""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    async def send_typing(
        self,
        account_id: str,
        receiver_id: str,
        typing: bool = True
    ) -> bool:
        """发送输入状态"""
        return await self.api.send_typing(account_id, receiver_id, typing)

    async def recall_message(self, account_id: str, msg_id: str) -> bool:
        """撤回消息"""
        return await self.api.recall_message(account_id, msg_id)

    def get_accounts(self) -> dict[str, WeChatAccount]:
        """获取所有账号"""
        return self._accounts.copy()

    def get_account(self, account_id: str) -> WeChatAccount | None:
        """获取指定账号"""
        return self._accounts.get(account_id)

    async def add_account(
        self,
        account_id: str,
        context_isolation: bool = True
    ) -> WeChatAccount | None:
        """添加新账号

        Args:
            account_id: 账号ID
            context_isolation: 是否启用上下文隔离

        Returns:
            添加的账号信息，失败返回None
        """
        if account_id in self._accounts:
            print(f"Account {account_id} already exists")
            return self._accounts[account_id]

        account = await self.api.get_account(account_id)
        if account:
            self._accounts[account_id] = account
            self._context_isolation[account_id] = context_isolation
            self._context_stores[account_id] = {}
            print(f"Added WeChat account: {account_id}")
            return account

        account = WeChatAccount(account_id=account_id)
        self._accounts[account_id] = account
        self._context_isolation[account_id] = context_isolation
        self._context_stores[account_id] = {}
        return account

    async def remove_account(self, account_id: str) -> bool:
        """移除账号

        Args:
            account_id: 账号ID

        Returns:
            是否成功移除
        """
        if account_id not in self._accounts:
            print(f"Account {account_id} not found")
            return False

        await self.api.logout(account_id)

        del self._accounts[account_id]
        if account_id in self._context_isolation:
            del self._context_isolation[account_id]
        if account_id in self._context_stores:
            del self._context_stores[account_id]
        if account_id in self._typing_tickets:
            del self._typing_tickets[account_id]

        print(f"Removed WeChat account: {account_id}")
        return True

    def list_accounts(self) -> list[WeChatAccount]:
        """列出所有账号

        Returns:
            账号列表
        """
        return list(self._accounts.values())

    async def send_video(
        self,
        account_id: str,
        receiver_id: str,
        video_path: str
    ) -> bool:
        """发送视频消息

        Args:
            account_id: 账号ID
            receiver_id: 接收者ID
            video_path: 视频文件路径

        Returns:
            是否发送成功
        """
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return False

        try:
            media = await self.api.upload_media(
                account_id=account_id,
                file_path=video_path,
                file_type="video",
            )

            if not media:
                print("Failed to upload video to CDN")
                return False

            result = await self.api.send_message(
                account_id=account_id,
                receiver_id=receiver_id,
                msg_type=WeChatMessageType.VIDEO,
                media=media,
            )

            return result.success

        except Exception as e:
            print(f"Failed to send video: {e}")
            return False

    async def send_image_with_upload(
        self,
        account_id: str,
        receiver_id: str,
        image_path: str
    ) -> bool:
        """发送图片消息（使用CDN上传）

        Args:
            account_id: 账号ID
            receiver_id: 接收者ID
            image_path: 图片文件路径

        Returns:
            是否发送成功
        """
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False

        try:
            media = await self.api.upload_media(
                account_id=account_id,
                file_path=image_path,
                file_type="image",
            )

            if not media:
                print("Failed to upload image to CDN")
                return False

            result = await self.api.send_message(
                account_id=account_id,
                receiver_id=receiver_id,
                msg_type=WeChatMessageType.IMAGE,
                media=media,
            )

            return result.success

        except Exception as e:
            print(f"Failed to send image: {e}")
            return False

    async def send_file_with_upload(
        self,
        account_id: str,
        receiver_id: str,
        file_path: str
    ) -> bool:
        """发送文件消息（使用CDN上传）

        Args:
            account_id: 账号ID
            receiver_id: 接收者ID
            file_path: 文件路径

        Returns:
            是否发送成功
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        try:
            media = await self.api.upload_media(
                account_id=account_id,
                file_path=file_path,
                file_type="file",
            )

            if not media:
                print("Failed to upload file to CDN")
                return False

            result = await self.api.send_message(
                account_id=account_id,
                receiver_id=receiver_id,
                msg_type=WeChatMessageType.FILE,
                content=media.file_name,
                media=media,
            )

            return result.success

        except Exception as e:
            print(f"Failed to send file: {e}")
            return False

    async def check_login_status(self, account_id: str) -> dict[str, Any]:
        """检查登录状态

        Args:
            account_id: 账号ID

        Returns:
            包含登录状态信息的字典
        """
        status = await self.api.check_login_status(account_id)

        if status.get("is_logged_in") and account_id in self._accounts:
            account = self._accounts[account_id]
            account.login_status = True
            account.nickname = status.get("nickname", account.nickname)
            account.wxid = status.get("wxid", account.wxid)
            account.avatar = status.get("avatar", account.avatar)

        return status

    async def get_qrcode(self, account_id: str) -> dict[str, Any]:
        """获取登录二维码

        Args:
            account_id: 账号ID

        Returns:
            包含二维码URL和过期时间的字典
        """
        result = await self.api.get_qrcode(account_id)

        if result.get("qrcode_url") and account_id in self._accounts:
            self._accounts[account_id].qrcode_url = result["qrcode_url"]

        return result

    async def send_typing_with_ticket(
        self,
        account_id: str,
        receiver_id: str,
        typing: bool = True
    ) -> bool:
        """发送输入状态（带票据获取）

        先获取输入状态票据，然后发送输入状态。

        Args:
            account_id: 账号ID
            receiver_id: 接收者ID
            typing: True表示正在输入，False表示停止输入

        Returns:
            是否发送成功
        """
        if account_id not in self._typing_tickets:
            config = await self.api.get_config(account_id)
            typing_ticket = config.get("typing_ticket", "")
            if typing_ticket:
                self._typing_tickets[account_id] = typing_ticket

        return await self.api.send_typing(account_id, receiver_id, typing)

    def get_context_store(self, account_id: str) -> dict[str, Any]:
        """获取账号的上下文存储

        Args:
            account_id: 账号ID

        Returns:
            上下文存储字典
        """
        return self._context_stores.get(account_id, {})

    def set_context_store(
        self,
        account_id: str,
        context: dict[str, Any]
    ) -> None:
        """设置账号的上下文存储

        Args:
            account_id: 账号ID
            context: 上下文字典
        """
        self._context_stores[account_id] = context

    def is_context_isolated(self, account_id: str) -> bool:
        """检查账号是否启用上下文隔离

        Args:
            account_id: 账号ID

        Returns:
            是否启用上下文隔离
        """
        return self._context_isolation.get(account_id, True)

    def get_context(self, account_id: str) -> dict[str, Any]:
        """获取账号的隔离上下文"""
        if account_id not in self._context_stores:
            self._context_stores[account_id] = {}
        return self._context_stores[account_id]

    def set_context(self, account_id: str, key: str, value: Any) -> None:
        """设置账号的隔离上下文"""
        context = self.get_context(account_id)
        context[key] = value

    def clear_context(self, account_id: str) -> None:
        """清除账号的隔离上下文"""
        if account_id in self._context_stores:
            self._context_stores[account_id] = {}
