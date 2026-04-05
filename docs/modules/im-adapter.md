# IM适配器模块文�?v0.8.0

本文档详细描述PyAgent v0.8.0 IM平台适配器模块的设计和实现�?
## 概述

IM适配器模块提供统一的接口，支持多种即时通讯平台的接入�?
## 支持的IM平台

| 平台 | 协议 | 特点 |
|------|------|------|
| QQ | OneBot | WebSocket长连�?|
| 钉钉 | Webhook | HTTP回调方式 |
| 飞书 | OpenAPI | 需要AppID/AppSecret |
| 企业微信 | OpenAPI | 需要CorpID/AgentID |

## 核心组件

### 1. BaseIMAdapter (适配器基�?

**文件**: `src/im/base.py`

```python
class BaseIMAdapter(ABC):
    """IM平台适配器基类�?""
    
    platform: str = "unknown"
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到IM平台�?""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接�?""
        pass
    
    @abstractmethod
    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        """发送消息�?""
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> Optional[IMUser]:
        """获取用户信息�?""
        pass
    
    @abstractmethod
    async def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """获取聊天信息�?""
        pass
```

### 2. 统一消息格式

#### IMMessage (消息)

```python
@dataclass
class IMMessage:
    message_id: str           # 消息唯一ID
    platform: str             # 平台标识
    chat_id: str              # 聊天ID
    chat_type: ChatType       # 私聊/群聊
    sender: IMUser            # 发送者信�?    content: str              # 消息内容
    message_type: MessageType # 消息类型
    timestamp: float          # 时间�?    reply_to: Optional[str]   # 回复消息ID
    at_users: List[str]       # @的用户列�?    is_at_bot: bool           # 是否@机器�?```

#### IMReply (回复)

```python
@dataclass
class IMReply:
    content: str              # 回复内容
    message_type: MessageType # 消息类型
    reply_to: Optional[str]   # 回复消息ID
    at_users: List[str]       # @的用户列�?```

#### IMUser (用户)

```python
@dataclass
class IMUser:
    user_id: str      # 用户ID
    name: str         # 用户�?    nickname: str     # 昵称
    avatar: str       # 头像URL
    is_bot: bool      # 是否机器�?```

### 3. MessageRouter (消息路由�?

**文件**: `src/im/router.py`

```python
class MessageRouter:
    """消息路由器，管理多个IM适配器�?""
    
    def register_adapter(self, adapter: BaseIMAdapter) -> None:
        """注册适配器�?""
        pass
    
    async def connect_all(self) -> Dict[str, bool]:
        """连接所有适配器�?""
        pass
    
    async def disconnect_all(self) -> None:
        """断开所有适配器�?""
        pass
    
    async def route_message(self, message: IMMessage) -> None:
        """路由消息到处理器�?""
        pass
```

## 各平台适配�?
### OneBotAdapter (QQ)

**文件**: `src/im/onebot.py`

```python
adapter = OneBotAdapter(
    ws_url="ws://127.0.0.1:3001",
    access_token="your_token",
    platform_name="qq"
)

# 注册消息处理�?adapter.register_message_handler(handle_message)

# 连接
await adapter.connect()
```

### DingTalkAdapter (钉钉)

**文件**: `src/im/dingtalk.py`

```python
adapter = DingTalkAdapter(
    webhook_url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
    secret="your_secret"
)

# 发送消�?reply = IMReply(content="你好")
await adapter.send_message("chat_id", reply)
```

### FeishuAdapter (飞书)

**文件**: `src/im/feishu.py`

```python
adapter = FeishuAdapter(
    app_id="cli_xxxxxxxx",
    app_secret="xxxxxxxx"
)

# 连接
await adapter.connect()
```

### WeComAdapter (企业微信)

**文件**: `src/im/wecom.py`

```python
adapter = WeComAdapter(
    corp_id="wwxxxxxxxxxxxxxxxx",
    agent_id="1000002",
    secret="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
)

# 连接
await adapter.connect()
```

## 扩展开�?
### 创建自定义适配�?
```python
from src.im.base import BaseIMAdapter, IMMessage, IMReply, IMUser

class MyPlatformAdapter(BaseIMAdapter):
    """自定义平台适配器�?""
    
    platform = "my_platform"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self._client = None
    
    async def connect(self) -> bool:
        """连接到平台�?""
        try:
            self._client = MyPlatformClient(self.api_key)
            await self._client.connect()
            
            # 设置消息回调
            self._client.on_message(self._handle_message)
            
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接�?""
        if self._client:
            await self._client.disconnect()
        self._connected = False
    
    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        """发送消息�?""
        try:
            await self._client.send_text(
                chat_id=chat_id,
                content=reply.content
            )
            return True
        except Exception as e:
            logger.error(f"发送失�? {e}")
            return False
    
    async def get_user_info(self, user_id: str) -> Optional[IMUser]:
        """获取用户信息�?""
        try:
            data = await self._client.get_user(user_id)
            return IMUser(
                user_id=user_id,
                name=data.get("name", ""),
                nickname=data.get("nickname", "")
            )
        except Exception:
            return None
    
    async def _handle_message(self, raw_msg: Dict[str, Any]) -> None:
        """处理收到的消息�?""
        message = IMMessage(
            message_id=raw_msg["id"],
            platform=self.platform,
            chat_id=raw_msg["chat_id"],
            chat_type=ChatType.GROUP if raw_msg["is_group"] else ChatType.PRIVATE,
            sender=IMUser(
                user_id=raw_msg["sender_id"],
                name=raw_msg["sender_name"]
            ),
            content=raw_msg["content"],
            timestamp=raw_msg["timestamp"]
        )
        
        await self._dispatch_message(message)
```

## 配置

### OneBot配置

```yaml
# config/onebot.yaml
enabled: true
ws_url: ws://127.0.0.1:3001
access_token: your_token
platform: qq
heartbeat_interval: 30
reconnect_interval: 5
```

### 钉钉配置

```yaml
# config/dingtalk.yaml
enabled: true
webhook_url: https://oapi.dingtalk.com/robot/send?access_token=xxx
secret: your_secret
at_all: false
```

### 飞书配置

```yaml
# config/feishu.yaml
enabled: true
app_id: cli_xxxxxxxx
app_secret: xxxxxxxx
encrypt_key: optional
verification_token: optional
```

### 企业微信配置

```yaml
# config/wecom.yaml
enabled: true
corp_id: wwxxxxxxxxxxxxxxxx
agent_id: 1000002
secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
token: optional
encoding_aes_key: optional
```

## 使用示例

```python
from src.im.router import MessageRouter
from src.im.onebot import OneBotAdapter
from src.im.dingtalk import DingTalkAdapter

# 创建路由�?router = MessageRouter()

# 注册OneBot适配�?onebot = OneBotAdapter(
    ws_url="ws://127.0.0.1:3001",
    access_token="token"
)
router.register_adapter(onebot)

# 注册钉钉适配�?dingtalk = DingTalkAdapter(
    webhook_url="https://...",
    secret="secret"
)
router.register_adapter(dingtalk)

# 注册消息处理�?async def handle_message(message: IMMessage):
    print(f"收到消息: {message.content}")
    # 处理消息...

for adapter in router.adapters:
    adapter.register_message_handler(handle_message)

# 连接所有适配�?results = await router.connect_all()
print(f"连接结果: {results}")

# 断开连接
await router.disconnect_all()
```
