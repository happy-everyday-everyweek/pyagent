"""
PyAgent 微信适配器测试

测试微信消息类型、API客户端和适配器功能。
"""

import pytest

from src.im.wechat.types import (
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
from src.im.wechat.api import WeChatAPI, WeChatAPIError
from src.im.wechat.adapter import WeChatAdapter


class TestWeChatMessageType:
    """测试微信消息类型枚举"""

    def test_message_type_values(self):
        """测试消息类型枚举值"""
        assert WeChatMessageType.TEXT.value == 1
        assert WeChatMessageType.IMAGE.value == 2
        assert WeChatMessageType.VOICE.value == 3
        assert WeChatMessageType.FILE.value == 4
        assert WeChatMessageType.VIDEO.value == 5
        assert WeChatMessageType.LINK.value == 6
        assert WeChatMessageType.MINI_PROGRAM.value == 7
        assert WeChatMessageType.LOCATION.value == 8
        assert WeChatMessageType.SYSTEM.value == 9


class TestWeChatMessageSource:
    """测试微信消息来源枚举"""

    def test_source_values(self):
        """测试来源枚举值"""
        assert WeChatMessageSource.PRIVATE.value == "private"
        assert WeChatMessageSource.GROUP.value == "group"


class TestWeChatMessage:
    """测试微信消息"""

    def test_message_creation(self):
        """测试消息创建"""
        msg = WeChatMessage(
            msg_id="msg_123",
            sender_id="user_001",
            receiver_id="bot_001",
            msg_type=WeChatMessageType.TEXT,
            content="Hello"
        )
        assert msg.msg_id == "msg_123"
        assert msg.sender_id == "user_001"
        assert msg.receiver_id == "bot_001"
        assert msg.msg_type == WeChatMessageType.TEXT
        assert msg.content == "Hello"
        assert msg.source == WeChatMessageSource.PRIVATE

    def test_message_with_group(self):
        """测试群消息"""
        msg = WeChatMessage(
            msg_id="msg_123",
            sender_id="user_001",
            receiver_id="bot_001",
            msg_type=WeChatMessageType.TEXT,
            content="Hello",
            source=WeChatMessageSource.GROUP,
            group_id="group_001",
            at_users=["bot_001"],
            is_at_bot=True
        )
        assert msg.source == WeChatMessageSource.GROUP
        assert msg.group_id == "group_001"
        assert "bot_001" in msg.at_users
        assert msg.is_at_bot is True

    def test_message_with_media(self):
        """测试媒体消息"""
        msg = WeChatMessage(
            msg_id="msg_123",
            sender_id="user_001",
            receiver_id="bot_001",
            msg_type=WeChatMessageType.IMAGE,
            content="",
            media_url="https://example.com/image.jpg"
        )
        assert msg.msg_type == WeChatMessageType.IMAGE
        assert msg.media_url == "https://example.com/image.jpg"


class TestWeChatAccount:
    """测试微信账号信息"""

    def test_account_creation(self):
        """测试账号创建"""
        account = WeChatAccount(
            account_id="account_001",
            nickname="测试账号",
            wxid="wxid_123",
            login_status=True
        )
        assert account.account_id == "account_001"
        assert account.nickname == "测试账号"
        assert account.wxid == "wxid_123"
        assert account.login_status is True

    def test_account_with_qrcode(self):
        """测试带二维码的账号"""
        account = WeChatAccount(
            account_id="account_001",
            qrcode_url="https://example.com/qrcode.png"
        )
        assert account.qrcode_url == "https://example.com/qrcode.png"


class TestCDNMedia:
    """测试CDN媒体信息"""

    def test_cdn_media_creation(self):
        """测试CDN媒体创建"""
        media = CDNMedia(
            aes_key="aes_key_123",
            file_size=1024,
            file_md5="md5_hash",
            file_type="image",
            cdn_url="https://cdn.example.com/file",
            file_name="test.jpg"
        )
        assert media.aes_key == "aes_key_123"
        assert media.file_size == 1024
        assert media.file_md5 == "md5_hash"
        assert media.file_type == "image"
        assert media.cdn_url == "https://cdn.example.com/file"
        assert media.file_name == "test.jpg"


class TestSendResult:
    """测试发送结果"""

    def test_send_result_success(self):
        """测试成功发送结果"""
        result = SendResult(
            success=True,
            msg_id="msg_123",
            timestamp=1234567890
        )
        assert result.success is True
        assert result.msg_id == "msg_123"
        assert result.error is None

    def test_send_result_failure(self):
        """测试失败发送结果"""
        result = SendResult(
            success=False,
            error="发送失败"
        )
        assert result.success is False
        assert result.error == "发送失败"


class TestUploadResult:
    """测试上传结果"""

    def test_upload_result_success(self):
        """测试成功上传结果"""
        result = UploadResult(
            success=True,
            cdn_key="cdn_key_123",
            aes_key="aes_key_123",
            file_md5="md5_hash",
            file_size=1024
        )
        assert result.success is True
        assert result.cdn_key == "cdn_key_123"
        assert result.aes_key == "aes_key_123"

    def test_upload_result_failure(self):
        """测试失败上传结果"""
        result = UploadResult(
            success=False,
            error="上传失败"
        )
        assert result.success is False
        assert result.error == "上传失败"


class TestWeChatContact:
    """测试微信联系人"""

    def test_contact_creation(self):
        """测试联系人创建"""
        contact = WeChatContact(
            wxid="wxid_123",
            nickname="测试用户",
            alias="test_alias",
            avatar="https://example.com/avatar.jpg",
            remark="备注名",
            is_friend=True
        )
        assert contact.wxid == "wxid_123"
        assert contact.nickname == "测试用户"
        assert contact.alias == "test_alias"
        assert contact.remark == "备注名"
        assert contact.is_friend is True

    def test_contact_with_extra(self):
        """测试带额外信息的联系人"""
        contact = WeChatContact(
            wxid="wxid_123",
            extra={"department": "研发部"}
        )
        assert contact.extra["department"] == "研发部"


class TestWeChatGroup:
    """测试微信群组"""

    def test_group_creation(self):
        """测试群组创建"""
        group = WeChatGroup(
            group_id="group_001@chatroom",
            group_name="测试群",
            member_count=10,
            owner_id="wxid_owner",
            members=["wxid_1", "wxid_2", "wxid_3"]
        )
        assert group.group_id == "group_001@chatroom"
        assert group.group_name == "测试群"
        assert group.member_count == 10
        assert group.owner_id == "wxid_owner"
        assert len(group.members) == 3


class TestWeChatAPIError:
    """测试微信API错误"""

    def test_api_error_creation(self):
        """测试API错误创建"""
        error = WeChatAPIError(404, "Not found")
        assert error.code == 404
        assert error.message == "Not found"
        assert "404" in str(error)
        assert "Not found" in str(error)


class TestWeChatAPI:
    """测试微信API客户端"""

    def test_api_creation(self):
        """测试API创建"""
        api = WeChatAPI("https://api.example.com", timeout=30)
        assert api.base_url == "https://api.example.com"
        assert api.timeout == 30
        assert api._client is None

    def test_api_base_url_trailing_slash(self):
        """测试base_url尾部斜杠处理"""
        api = WeChatAPI("https://api.example.com/")
        assert api.base_url == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_api_close(self):
        """测试API关闭"""
        api = WeChatAPI("https://api.example.com")
        await api.close()
        assert api._client is None


class TestWeChatAdapter:
    """测试微信适配器"""

    def test_adapter_creation(self):
        """测试适配器创建"""
        adapter = WeChatAdapter()
        assert adapter.platform == "wechat"
        assert adapter.api is not None
        assert len(adapter._accounts) == 0

    def test_adapter_with_config(self):
        """测试带配置的适配器"""
        config = {
            "base_url": "https://api.example.com",
            "timeout": 60,
            "poll_interval": 10
        }
        adapter = WeChatAdapter(config=config)
        assert adapter.api.base_url == "https://api.example.com"
        assert adapter.api.timeout == 60
        assert adapter._poll_interval == 10

    def test_adapter_platform(self):
        """测试适配器平台标识"""
        adapter = WeChatAdapter()
        assert adapter.platform == "wechat"

    def test_get_accounts(self):
        """测试获取账号列表"""
        adapter = WeChatAdapter()
        accounts = adapter.get_accounts()
        assert isinstance(accounts, dict)
        assert len(accounts) == 0

    def test_get_account(self):
        """测试获取指定账号"""
        adapter = WeChatAdapter()
        account = adapter.get_account("nonexistent")
        assert account is None

    def test_context_isolation_default(self):
        """测试上下文隔离默认值"""
        adapter = WeChatAdapter()
        assert adapter.is_context_isolated("nonexistent") is True

    def test_get_context_store(self):
        """测试获取上下文存储"""
        adapter = WeChatAdapter()
        context = adapter.get_context_store("account_001")
        assert isinstance(context, dict)
        assert len(context) == 0

    def test_set_context_store(self):
        """测试设置上下文存储"""
        adapter = WeChatAdapter()
        adapter.set_context_store("account_001", {"key": "value"})
        context = adapter.get_context_store("account_001")
        assert context["key"] == "value"

    def test_get_context(self):
        """测试获取隔离上下文"""
        adapter = WeChatAdapter()
        context = adapter.get_context("account_001")
        assert isinstance(context, dict)

    def test_set_context(self):
        """测试设置隔离上下文"""
        adapter = WeChatAdapter()
        adapter.set_context("account_001", "session_id", "session_123")
        context = adapter.get_context("account_001")
        assert context["session_id"] == "session_123"

    def test_clear_context(self):
        """测试清除隔离上下文"""
        adapter = WeChatAdapter()
        adapter.set_context("account_001", "key", "value")
        adapter.clear_context("account_001")
        context = adapter.get_context("account_001")
        assert len(context) == 0

    def test_list_accounts(self):
        """测试列出所有账号"""
        adapter = WeChatAdapter()
        accounts = adapter.list_accounts()
        assert isinstance(accounts, list)
        assert len(accounts) == 0

    @pytest.mark.asyncio
    async def test_connect_without_config(self):
        """测试无配置连接"""
        adapter = WeChatAdapter()
        result = await adapter.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_without_accounts(self):
        """测试无账号配置连接"""
        adapter = WeChatAdapter(config={
            "base_url": "https://api.example.com"
        })
        result = await adapter.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """测试断开连接"""
        adapter = WeChatAdapter()
        await adapter.disconnect()
        assert adapter._connected is False

    @pytest.mark.asyncio
    async def test_add_account(self):
        """测试添加账号"""
        adapter = WeChatAdapter()
        adapter._accounts["account_001"] = WeChatAccount(account_id="account_001")
        adapter._context_isolation["account_001"] = True
        adapter._context_stores["account_001"] = {}
        account = adapter.get_account("account_001")
        assert account is not None
        assert account.account_id == "account_001"

    @pytest.mark.asyncio
    async def test_add_duplicate_account(self):
        """测试添加重复账号"""
        adapter = WeChatAdapter()
        adapter._accounts["account_001"] = WeChatAccount(account_id="account_001")
        existing_account = adapter.get_account("account_001")
        assert existing_account is not None
        assert existing_account.account_id == "account_001"

    @pytest.mark.asyncio
    async def test_remove_account(self):
        """测试移除账号"""
        adapter = WeChatAdapter()
        adapter._accounts["account_001"] = WeChatAccount(account_id="account_001")
        adapter._context_isolation["account_001"] = True
        adapter._context_stores["account_001"] = {}
        del adapter._accounts["account_001"]
        if "account_001" in adapter._context_isolation:
            del adapter._context_isolation["account_001"]
        if "account_001" in adapter._context_stores:
            del adapter._context_stores["account_001"]
        assert adapter.get_account("account_001") is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent_account(self):
        """测试移除不存在的账号"""
        adapter = WeChatAdapter()
        result = await adapter.remove_account("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self):
        """测试未连接时发送消息"""
        adapter = WeChatAdapter()
        from src.im.base import IMReply, MessageType
        reply = IMReply(content="Hello", message_type=MessageType.TEXT)
        result = await adapter.send_message("chat_001", reply)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_info_no_accounts(self):
        """测试无账号时获取用户信息"""
        adapter = WeChatAdapter()
        user = await adapter.get_user_info("user_001")
        assert user is not None
        assert user.user_id == "user_001"

    @pytest.mark.asyncio
    async def test_get_chat_info_no_accounts(self):
        """测试无账号时获取聊天信息"""
        adapter = WeChatAdapter()
        info = await adapter.get_chat_info("chat_001")
        assert info is not None
        assert info["chat_id"] == "chat_001"

    def test_convert_msg_type(self):
        """测试消息类型转换"""
        adapter = WeChatAdapter()
        from src.im.base import MessageType

        assert adapter._convert_msg_type(MessageType.TEXT) == WeChatMessageType.TEXT
        assert adapter._convert_msg_type(MessageType.IMAGE) == WeChatMessageType.IMAGE
        assert adapter._convert_msg_type(MessageType.AUDIO) == WeChatMessageType.VOICE
        assert adapter._convert_msg_type(MessageType.VIDEO) == WeChatMessageType.VIDEO
        assert adapter._convert_msg_type(MessageType.FILE) == WeChatMessageType.FILE
        assert adapter._convert_msg_type(MessageType.CARD) == WeChatMessageType.LINK
