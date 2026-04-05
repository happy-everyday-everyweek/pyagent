# 微信适配器文�?v0.8.0

本文档详细描述PyAgent v0.8.0微信适配器的设计和实现�?
## 概述

**v0.4.0** 版本新增微信通道支持，基于OpenClaw微信插件实现，支持二维码登录、消息收发、文件传输等功能�?
## 核心特�?
- **OpenClaw集成**: 基于OpenClaw微信插件
- **二维码登�?*: 支持扫码登录微信
- **多账号支�?*: 可同时管理多个微信账�?- **消息收发**: 支持文本、图片、文件等多种消息类型
- **CDN上传**: 支持大文件分片上�?
## 架构设计

```
┌─────────────────────────────────────────────────────────────────�?�?                    微信适配器架�?v0.4.0                        �?├─────────────────────────────────────────────────────────────────�?�?                                                                �?�? ┌─────────────────────────────────────────────────────────�?  �?�? �?                 WeChatAdapter                          �?  �?�? �?                 (微信适配�?                            �?  �?�? �?                                                        �?  �?�? �? 职责: 实现与微信的通信                                  �?  �?�? �?                                                        �?  �?�? �? 核心功能:                                               �?  �?�? �? - 二维码登�?                                           �?  �?�? �? - 消息收发                                              �?  �?�? �? - 文件传输                                              �?  �?�? �? - 多账号管�?                                           �?  �?�? �?                                                        �?  �?�? └─────────────────────────────────────────────────────────�?  �?�?                             �?                                 �?�?                             �?                                 �?�? ┌─────────────────────────────────────────────────────────�?  �?�? �?                 OpenClawClient                         �?  �?�? �?                 (OpenClaw客户�?                        �?  �?�? �?                                                        �?  �?�? �? 职责: 与OpenClaw插件通信                                �?  �?�? �?                                                        �?  �?�? �? 通信方式:                                               �?  �?�? �? - HTTP API                                             �?  �?�? �? - WebSocket                                            �?  �?�? �?                                                        �?  �?�? └─────────────────────────────────────────────────────────�?  �?�?                             �?                                 �?�?                             �?                                 �?�? ┌─────────────────────────────────────────────────────────�?  �?�? �?                 OpenClaw插件                           �?  �?�? �?                 (微信PC端插�?                          �?  �?�? �?                                                        �?  �?�? �? 功能:                                                   �?  �?�? �? - 注入微信进程                                          �?  �?�? �? - 拦截微信消息                                          �?  �?�? �? - 模拟微信操作                                          �?  �?�? �?                                                        �?  �?�? └─────────────────────────────────────────────────────────�?  �?�?                             �?                                 �?�?                             �?                                 �?�? ┌─────────────────────────────────────────────────────────�?  �?�? �?                 微信PC客户�?                           �?  �?�? �?                                                        �?  �?�? �? - 微信Windows客户�?                                    �?  �?�? �? - 需要保持运�?                                         �?  �?�? �?                                                        �?  �?�? └─────────────────────────────────────────────────────────�?  �?�?                                                                �?└─────────────────────────────────────────────────────────────────�?```

## 核心组件

### 1. WeChatAdapter

**文件**: `src/im/wechat/adapter.py`

微信适配器，实现与微信的通信�?
#### 适配器结�?
```python
class WeChatAdapter(BaseIMAdapter):
    """微信适配�?""
    
    platform = "wechat"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.openclaw_url = config.get("openclaw_url", "http://localhost:9000")
        self.ws_url = config.get("ws_url", "ws://localhost:9001")
        self._client = None
        self._connected = False
        self._qrcode_callback = None
    
    async def connect(self) -> bool:
        """连接到微�?""
        try:
            self._client = OpenClawClient(
                base_url=self.openclaw_url,
                ws_url=self.ws_url
            )
            
            # 检查是否需要登�?            if not await self._client.is_logged_in():
                # 获取登录二维�?                qrcode = await self._client.get_login_qrcode()
                
                # 触发二维码回�?                if self._qrcode_callback:
                    await self._qrcode_callback(qrcode)
                
                # 等待登录
                await self._client.wait_for_login()
            
            # 连接WebSocket
            await self._client.connect_websocket()
            
            # 设置消息回调
            self._client.on_message(self._handle_message)
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"连接微信失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self._client:
            await self._client.disconnect()
        self._connected = False
    
    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        """发送消�?""
        try:
            if reply.message_type == MessageType.TEXT:
                await self._client.send_text(chat_id, reply.content)
            elif reply.message_type == MessageType.IMAGE:
                await self._client.send_image(chat_id, reply.content)
            elif reply.message_type == MessageType.FILE:
                await self._client.send_file(chat_id, reply.content)
            
            return True
            
        except Exception as e:
            logger.error(f"发送消息失�? {e}")
            return False
    
    async def get_user_info(self, user_id: str) -> Optional[IMUser]:
        """获取用户信息"""
        try:
            user_data = await self._client.get_contact(user_id)
            return IMUser(
                user_id=user_id,
                name=user_data.get("nickname", ""),
                nickname=user_data.get("remark", ""),
                avatar=user_data.get("avatar", "")
            )
        except Exception:
            return None
    
    def register_qrcode_callback(self, callback: Callable[[str], None]):
        """注册二维码回�?""
        self._qrcode_callback = callback
```

### 2. OpenClawClient

**文件**: `src/im/wechat/openclaw_client.py`

OpenClaw客户端，负责与OpenClaw插件通信�?
#### 客户端结�?
```python
class OpenClawClient:
    """OpenClaw客户�?""
    
    def __init__(self, base_url: str, ws_url: str):
        self.base_url = base_url
        self.ws_url = ws_url
        self._http_client = httpx.AsyncClient()
        self._ws_client = None
        self._message_handler = None
        self._logged_in = False
    
    async def is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            response = await self._http_client.get(f"{self.base_url}/api/is_logged_in")
            data = response.json()
            return data.get("is_logged_in", False)
        except Exception:
            return False
    
    async def get_login_qrcode(self) -> str:
        """获取登录二维�?""
        response = await self._http_client.get(f"{self.base_url}/api/get_qrcode")
        data = response.json()
        return data.get("qrcode_url", "")
    
    async def wait_for_login(self, timeout: int = 120) -> bool:
        """等待登录"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self.is_logged_in():
                return True
            await asyncio.sleep(2)
        
        return False
    
    async def connect_websocket(self):
        """连接WebSocket"""
        self._ws_client = await websockets.connect(self.ws_url)
        
        # 启动消息接收循环
        asyncio.create_task(self._receive_messages())
    
    async def _receive_messages(self):
        """接收消息"""
        try:
            async for message in self._ws_client:
                data = json.loads(message)
                
                if self._message_handler:
                    await self._message_handler(data)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket连接已关�?)
    
    async def send_text(self, chat_id: str, content: str):
        """发送文本消�?""
        await self._http_client.post(
            f"{self.base_url}/api/send_text",
            json={"wxid": chat_id, "content": content}
        )
    
    async def send_image(self, chat_id: str, image_path: str):
        """发送图�?""
        await self._http_client.post(
            f"{self.base_url}/api/send_image",
            json={"wxid": chat_id, "image_path": image_path}
        )
    
    async def send_file(self, chat_id: str, file_path: str):
        """发送文�?""
        # 大文件使用CDN上传
        if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
            file_url = await self._upload_to_cdn(file_path)
            await self._http_client.post(
                f"{self.base_url}/api/send_file_url",
                json={"wxid": chat_id, "file_url": file_url}
            )
        else:
            await self._http_client.post(
                f"{self.base_url}/api/send_file",
                json={"wxid": chat_id, "file_path": file_path}
            )
    
    async def _upload_to_cdn(self, file_path: str) -> str:
        """上传文件到CDN"""
        # 分片上传大文�?        chunk_size = 1024 * 1024  # 1MB
        file_size = os.path.getsize(file_path)
        chunks = (file_size + chunk_size - 1) // chunk_size
        
        upload_id = None
        
        with open(file_path, "rb") as f:
            for i in range(chunks):
                chunk = f.read(chunk_size)
                
                response = await self._http_client.post(
                    f"{self.base_url}/api/upload_chunk",
                    files={"chunk": chunk},
                    data={
                        "upload_id": upload_id,
                        "chunk_index": i,
                        "total_chunks": chunks
                    }
                )
                
                data = response.json()
                if i == 0:
                    upload_id = data.get("upload_id")
        
        # 完成上传
        response = await self._http_client.post(
            f"{self.base_url}/api/complete_upload",
            json={"upload_id": upload_id}
        )
        
        return response.json().get("file_url")
    
    async def get_contact(self, user_id: str) -> Dict[str, Any]:
        """获取联系人信�?""
        response = await self._http_client.get(
            f"{self.base_url}/api/get_contact",
            params={"wxid": user_id}
        )
        return response.json()
    
    def on_message(self, handler: Callable[[Dict[str, Any]], None]):
        """设置消息处理�?""
        self._message_handler = handler
    
    async def disconnect(self):
        """断开连接"""
        if self._ws_client:
            await self._ws_client.close()
        await self._http_client.aclose()
```

## 消息格式

### 接收消息

```python
{
    "type": "text",  # text/image/file/voice/video
    "wxid": "wxid_xxx",  # 发送者ID
    "sender": "nickname",  # 发送者昵�?    "content": "消息内容",
    "timestamp": 1704067200,
    "is_group": false,
    "group_id": null,  # 群聊ID
    "at_list": []  # @的用户列�?}
```

### 发送消�?
```python
# 文本消息
{
    "wxid": "wxid_xxx",
    "content": "消息内容"
}

# 图片消息
{
    "wxid": "wxid_xxx",
    "image_path": "/path/to/image.jpg"
}

# 文件消息
{
    "wxid": "wxid_xxx",
    "file_path": "/path/to/file.pdf"
}
```

## 使用示例

### 基础使用

```python
from src.im.wechat.adapter import WeChatAdapter

# 创建适配�?adapter = WeChatAdapter(
    config={
        "openclaw_url": "http://localhost:9000",
        "ws_url": "ws://localhost:9001"
    }
)

# 注册二维码回�?async def on_qrcode(qrcode_url: str):
    print(f"请扫描二维码登录: {qrcode_url}")
    # 可以在这里显示二维码图片

adapter.register_qrcode_callback(on_qrcode)

# 连接
connected = await adapter.connect()
if connected:
    print("微信连接成功")
else:
    print("微信连接失败")

# 发送消�?from src.im.base import IMReply, MessageType

reply = IMReply(
    content="你好�?,
    message_type=MessageType.TEXT
)

success = await adapter.send_message("wxid_xxx", reply)
```

### 消息处理

```python
# 注册消息处理�?async def handle_message(message: IMMessage):
    print(f"收到消息: {message.content}")
    
    # 回复消息
    reply = IMReply(
        content=f"收到: {message.content}",
        message_type=MessageType.TEXT
    )
    
    await adapter.send_message(message.chat_id, reply)

adapter.register_message_handler(handle_message)
```

### 多账号管�?
```python
# 创建多个适配器实�?adapter1 = WeChatAdapter(config={"openclaw_url": "http://localhost:9000"})
adapter2 = WeChatAdapter(config={"openclaw_url": "http://localhost:9002"})

# 分别连接
await adapter1.connect()
await adapter2.connect()

# 同时管理多个账号
adapters = [adapter1, adapter2]
```

## 配置

### 配置文件

```yaml
# config/wechat.yaml
wechat:
  enabled: true
  openclaw_url: "http://localhost:9000"
  ws_url: "ws://localhost:9001"
  
  # 登录配置
  login:
    timeout: 120  # 登录超时时间(�?
    auto_login: true  # 自动登录
  
  # 消息配置
  message:
    max_file_size: 100  # 最大文件大�?MB)
    use_cdn: true  # 大文件使用CDN
    cdn_threshold: 10  # CDN阈�?MB)
  
  # 重连配置
  reconnect:
    enabled: true
    interval: 5
    max_attempts: 10
```

### 环境变量

```env
# 微信配置
WECHAT_ENABLED=true
WECHAT_OPENCLAW_URL=http://localhost:9000
WECHAT_WS_URL=ws://localhost:9001
WECHAT_AUTO_LOGIN=true
```

## OpenClaw安装

### 系统要求

- Windows 10/11
- 微信PC�?3.x
- Python 3.10+

### 安装步骤

1. **安装OpenClaw**

```bash
# 克隆OpenClaw仓库
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# 安装依赖
pip install -r requirements.txt

# 安装OpenClaw
python setup.py install
```

2. **启动OpenClaw**

```bash
# 启动OpenClaw服务
python -m openclaw.server --port 9000
```

3. **启动微信**

启动微信PC客户端，OpenClaw会自动注入�?
4. **配置PyAgent**

在`.env`文件中添加微信配置：

```env
WECHAT_ENABLED=true
WECHAT_OPENCLAW_URL=http://localhost:9000
```

## API接口

### 获取登录状�?
```http
GET /api/wechat/status
```

**响应**:
```json
{
  "connected": true,
  "logged_in": true,
  "user_info": {
    "wxid": "wxid_xxx",
    "nickname": "昵称"
  }
}
```

### 获取登录二维�?
```http
GET /api/wechat/qrcode
```

**响应**:
```json
{
  "qrcode_url": "https://weixin.qq.com/x/xxx",
  "expires_in": 300
}
```

### 发送消�?
```http
POST /api/wechat/send
Content-Type: application/json

{
  "wxid": "wxid_xxx",
  "content": "消息内容",
  "type": "text"
}
```

### 获取联系人列�?
```http
GET /api/wechat/contacts
```

**响应**:
```json
{
  "contacts": [
    {
      "wxid": "wxid_xxx",
      "nickname": "昵称",
      "remark": "备注"
    }
  ]
}
```

## 最佳实�?
### 1. 处理二维码登�?
```python
import qrcode

async def on_qrcode(qrcode_url: str):
    """显示二维�?""
    # 生成二维码图�?    qr = qrcode.QRCode()
    qr.add_data(qrcode_url)
    qr.make()
    
    # 显示或保存二维码
    qr.print_ascii()
    # 或保存为图片
    qr.make_image().save("qrcode.png")
```

### 2. 消息去重

```python
class MessageDeduplicator:
    """消息去重�?""
    
    def __init__(self, max_size: int = 1000):
        self._seen = set()
        self._max_size = max_size
    
    def is_duplicate(self, message_id: str) -> bool:
        if message_id in self._seen:
            return True
        
        self._seen.add(message_id)
        
        # 限制集合大小
        if len(self._seen) > self._max_size:
            self._seen.pop()
        
        return False

# 使用
deduplicator = MessageDeduplicator()

async def handle_message(message: IMMessage):
    if deduplicator.is_duplicate(message.message_id):
        return
    
    # 处理消息
    ...
```

### 3. 错误处理

```python
async def safe_send_message(adapter: WeChatAdapter, chat_id: str, reply: IMReply):
    """安全发送消�?""
    try:
        success = await adapter.send_message(chat_id, reply)
        if not success:
            logger.error(f"发送消息失�? {chat_id}")
            # 重试或通知
    except Exception as e:
        logger.error(f"发送消息异�? {e}")
        # 处理异常
```

### 4. 监控连接状�?
```python
async def monitor_connection(adapter: WeChatAdapter):
    """监控连接状�?""
    while True:
        if not adapter.is_connected():
            logger.warning("微信连接断开，尝试重�?..")
            await adapter.connect()
        
        await asyncio.sleep(30)
```

## 故障排除

### 1. 无法连接OpenClaw

**原因**: OpenClaw服务未启�?
**解决**: 
```bash
# 检查OpenClaw服务
python -m openclaw.server --port 9000
```

### 2. 二维码扫描失�?
**原因**: 二维码过�?
**解决**: 重新获取二维�?
### 3. 消息发送失�?
**原因**: 未登录或连接断开

**解决**: 检查登录状态，重新连接

### 4. 大文件上传失�?
**原因**: 网络问题或文件过�?
**解决**: 
- 检查网络连�?- 使用CDN上传
- 分片上传

## 安全注意事项

1. **保护二维�?*: 二维码包含登录凭证，不要泄露给他�?2. **定期更换**: 建议定期更换微信登录凭证
3. **权限控制**: 限制OpenClaw的访问权�?4. **数据加密**: 敏感数据建议加密存储
