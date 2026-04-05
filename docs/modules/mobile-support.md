# PyAgent 移动端支持

**版本**: v0.8.0  
**模块路径**: `src/mobile/`  
**最后更新**: 2025-04-03

---

## 概述

移动端支持是 PyAgent v0.8.0 引入的全新模块，提供在 Android、iOS、HarmonyOS 等移动设备上运行 PyAgent 的能力。包括移动端后端服务、设备能力检测、屏幕控制、通知管理、短信收发等功能。

### 核心特性

- **多平台支持**: Android、iOS、HarmonyOS
- **设备检测**: 自动检测移动设备环境和能力
- **屏幕控制**: 截图、点击、滑动等操作
- **通知管理**: 读取和处理系统通知
- **短信收发**: 发送和接收短信
- **Linux 环境**: 支持 Linux 部署模式

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                   Mobile Support System                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              MobileBackend                          │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │   LinuxEnv   │  │  Capability  │                │   │
│  │  │   (Linux环境) │  │   Detection  │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │ ScreenTools  │  │ Notification │                │   │
│  │  │  (屏幕工具)   │  │   (通知管理)  │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                     │   │
│  │  ┌──────────────┐                                  │   │
│  │  │   SMSTools   │                                  │   │
│  │  │  (短信工具)   │                                  │   │
│  │  └──────────────┘                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 移动端后端 (MobileBackend)

**位置**: `src/mobile/backend.py`

```python
from src.mobile.backend import MobileBackend, MobileConfig, BackendMode

# 使用默认配置
backend = MobileBackend()

# 或自定义配置
config = MobileConfig(
    mode=BackendMode.STANDALONE,
    api_host="127.0.0.1",
    api_port=8080,
    enable_screen_tools=True,
    enable_notification=True,
    enable_sms=True
)
backend = MobileBackend(config)
```

#### 后端模式

```python
class BackendMode(Enum):
    STANDALONE = "standalone"   # 独立模式
    EMBEDDED = "embedded"       # 嵌入模式
    CLIENT = "client"           # 客户端模式
```

#### 后端状态

```python
class BackendStatus(Enum):
    UNINITIALIZED = "uninitialized"   # 未初始化
    INITIALIZING = "initializing"     # 初始化中
    READY = "ready"                   # 就绪
    RUNNING = "running"               # 运行中
    STOPPED = "stopped"               # 已停止
    ERROR = "error"                   # 错误
```

#### 主要方法

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `detect_mobile()` | 检测是否在移动设备上 | `bool` |
| `detect_capabilities()` | 检测设备能力 | `MobileCapabilities` |
| `initialize()` | 初始化后端 | `bool` |
| `start()` | 启动服务 | `bool` |
| `stop()` | 停止服务 | `bool` |
| `get_routes()` | 获取 API 路由 | `list` |
| `health_check()` | 健康检查 | `bool` |
| `get_status_info()` | 获取状态信息 | `dict` |

---

### 2. 设备能力 (MobileCapabilities)

```python
@dataclass
class MobileCapabilities:
    has_screen: bool = True         # 是否有屏幕
    has_camera: bool = True         # 是否有摄像头
    has_gps: bool = True            # 是否有 GPS
    has_bluetooth: bool = True      # 是否有蓝牙
    has_nfc: bool = False           # 是否有 NFC
    has_telephony: bool = True      # 是否有电话功能
    screen_width: int = 1080        # 屏幕宽度
    screen_height: int = 1920       # 屏幕高度
    screen_dpi: int = 480           # 屏幕 DPI
```

---

## 使用示例

### 初始化和启动

```python
from src.mobile.backend import MobileBackend, MobileConfig, BackendMode

# 创建后端
backend = MobileBackend()

# 初始化
if backend.initialize():
    print("移动端后端初始化成功")
    print(f"是否在移动设备: {backend.is_mobile}")
    
    # 启动服务
    if backend.start():
        print(f"服务已启动: {backend.api_endpoint}")
    else:
        print("服务启动失败")
else:
    print("初始化失败")
```

### 检测设备能力

```python
from src.mobile.backend import MobileBackend

backend = MobileBackend()
backend.initialize()

caps = backend.capabilities
if caps:
    print(f"""
设备能力:
=========
屏幕: {caps.has_screen} ({caps.screen_width}x{caps.screen_height})
摄像头: {caps.has_camera}
GPS: {caps.has_gps}
蓝牙: {caps.has_bluetooth}
NFC: {caps.has_nfc}
电话: {caps.has_telephony}
DPI: {caps.screen_dpi}
""")
```

### 屏幕控制

```python
import asyncio
from src.mobile.screen_tools import ScreenTools, ScreenResult

async def screen_example():
    tools = ScreenTools()
    
    # 截图
    result = await tools.capture_screen()
    if result.success:
        print(f"截图保存: {result.data}")
    
    # 点击屏幕
    result = await tools.tap(500, 800)
    print(f"点击结果: {result.success}")
    
    # 滑动屏幕
    result = await tools.swipe(500, 1000, 500, 500)
    print(f"滑动结果: {result.success}")

asyncio.run(screen_example())
```

### 通知管理

```python
import asyncio
from src.mobile.notification import NotificationReader

async def notification_example():
    reader = NotificationReader()
    
    # 获取通知
    notifications = await reader.get_notifications()
    
    for notif in notifications:
        print(f"应用: {notif.app_name}")
        print(f"标题: {notif.title}")
        print(f"内容: {notif.content}")
        print(f"时间: {notif.timestamp}")
        print("-" * 40)

asyncio.run(notification_example())
```

### 短信收发

```python
import asyncio
from src.mobile.sms import SMSTools

async def sms_example():
    tools = SMSTools()
    
    # 发送短信
    result = await tools.send_message(
        to="+86138xxxxxxxx",
        body="你好，这是来自 PyAgent 的测试短信。"
    )
    print(f"发送结果: {result.success}")
    
    # 获取短信
    messages = await tools.get_messages(limit=10)
    for msg in messages:
        print(f"来自: {msg.sender}")
        print(f"内容: {msg.body}")
        print(f"时间: {msg.timestamp}")
        print("-" * 40)

asyncio.run(sms_example())
```

---

## API 接口

### REST API

#### 获取状态
```http
GET /api/mobile/status
```

#### 获取设备能力
```http
GET /api/mobile/capabilities
```

#### 屏幕截图
```http
POST /api/mobile/screen/capture
```

#### 屏幕点击
```http
POST /api/mobile/screen/tap
Content-Type: application/json

{
  "x": 500,
  "y": 800
}
```

#### 屏幕滑动
```http
POST /api/mobile/screen/swipe
Content-Type: application/json

{
  "x1": 500,
  "y1": 1000,
  "x2": 500,
  "y2": 500
}
```

#### 获取通知
```http
GET /api/mobile/notifications
```

#### 获取短信
```http
GET /api/mobile/sms
```

#### 发送短信
```http
POST /api/mobile/sms/send
Content-Type: application/json

{
  "to": "+86138xxxxxxxx",
  "body": "短信内容"
}
```

---

## 配置选项

```yaml
# config/mobile.yaml
mobile:
  backend:
    mode: "standalone"  # standalone, embedded, client
    api_host: "127.0.0.1"
    api_port: 8080
    auto_start: true
    log_level: "info"
  
  features:
    enable_screen_tools: true
    enable_notification: true
    enable_sms: true
  
  data_dir: "data/mobile"
```

---

## 平台特定说明

### Android

```bash
# 需要权限
<uses-permission android:name="android.permission.READ_SMS"/>
<uses-permission android:name="android.permission.SEND_SMS"/>
<uses-permission android:name="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"/>
```

### iOS

iOS 支持需要通过特定框架实现，目前主要支持后台服务模式。

### HarmonyOS

HarmonyOS 支持使用 ArkTS 开发前端，Python 后端通过 RPC 通信。

---

## Linux 环境部署

```python
from src.mobile.linux_env import LinuxEnv, ServiceConfig

# 配置服务
config = ServiceConfig(
    host="0.0.0.0",
    port=8080,
    workers=4
)

# 创建 Linux 环境
linux_env = LinuxEnv(config)

# 初始化
if linux_env.initialize():
    print("Linux 环境初始化成功")
    
    # 启动服务
    if linux_env.start_service():
        print(f"服务运行在: {linux_env.api_endpoint}")
```

---

## 最佳实践

### 1. 权限检查

```python
from src.mobile.backend import MobileBackend

backend = MobileBackend()
backend.initialize()

if backend.is_mobile:
    caps = backend.capabilities
    
    if not caps.has_telephony:
        print("设备不支持短信功能")
    
    if not caps.has_screen:
        print("设备不支持屏幕操作")
```

### 2. 错误处理

```python
import asyncio
from src.mobile.screen_tools import ScreenTools

async def safe_screen_capture():
    tools = ScreenTools()
    
    try:
        result = await tools.capture_screen()
        if result.success:
            return result.data
        else:
            print(f"截图失败: {result.error}")
    except Exception as e:
        print(f"操作异常: {e}")

asyncio.run(safe_screen_capture())
```

### 3. 资源清理

```python
from src.mobile.backend import MobileBackend

backend = MobileBackend()
backend.initialize()
backend.start()

try:
    # 执行业务逻辑
    pass
finally:
    backend.stop()
    backend.cleanup()
```

---

## 故障排除

### 常见问题

**Q: 无法检测移动设备？**  
A: 检查系统环境和权限设置。

**Q: 屏幕控制无响应？**  
A: 确保有屏幕权限，且设备未锁屏。

**Q: 短信发送失败？**  
A: 检查电话权限和 SIM 卡状态。

---

## 手机操作工具

**版本**: v0.8.8  
**位置**: `src/mobile/tool_registry.py`  
**工具名称**: `phone_operation`

### 概述

手机操作工具是一个统一的自然语言驱动 UI 自动化工具，通过 `screen-operation` 垂类模型解析用户意图，自动规划并执行手机操作。

### 使用方式

```python
import asyncio
from src.mobile.tool_registry import mobile_tool_registry

async def phone_operation_example():
    result = await mobile_tool_registry.execute_tool(
        "phone_operation",
        {
            "intent": "打开微信发送消息给张三",
            "max_steps": 20
        }
    )
    
    print(f"成功: {result.success}")
    print(f"消息: {result.data.get('message')}")
    print(f"执行步骤: {result.data.get('steps_taken')}")
    print(f"最终状态: {result.data.get('final_state')}")

asyncio.run(phone_operation_example())
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `intent` | string | 是 | - | 自然语言操作意图 |
| `target_app` | string | 否 | - | 目标应用包名 |
| `max_steps` | integer | 否 | 20 | 最大执行步骤数 |
| `use_virtual_display` | boolean | 否 | false | 是否使用虚拟屏幕 |

### 返回结果

```python
{
    "success": True,           # 操作是否成功
    "message": "操作完成",      # 结果描述
    "steps_taken": 5,          # 执行的步骤数
    "final_state": "已发送消息", # 最终屏幕状态
    "agent_id": "main"         # 执行的代理ID
}
```

### 使用示例

#### 打开应用并发送消息

```python
result = await mobile_tool_registry.execute_tool(
    "phone_operation",
    {
        "intent": "打开微信发送消息给张三：你好，明天见面",
        "target_app": "com.tencent.mm"
    }
)
```

#### 系统设置操作

```python
result = await mobile_tool_registry.execute_tool(
    "phone_operation",
    {
        "intent": "打开设置并关闭蓝牙"
    }
)
```

#### 虚拟屏幕执行

```python
result = await mobile_tool_registry.execute_tool(
    "phone_operation",
    {
        "intent": "打开支付宝查看余额",
        "use_virtual_display": True
    }
)
```

### 配置选项

```yaml
# config/mobile.yaml
phone_operation:
  enabled: true
  max_steps: 20
  step_timeout: 10
  action_interval_ms: 500
  model: "screen-operation"
  virtual_display:
    enabled: true
    width: 1080
    height: 1920
    dpi: 480
```

---

## AutoGLM 子代理

**版本**: v0.8.8  
**位置**: `src/mobile/advanced_control/subagent.py`

### 概述

AutoGLM 子代理是手机操作工具的核心执行引擎，采用循环执行模式：截图 -> 分析 -> 规划 -> 执行 -> 验证。

### 执行流程

```
┌─────────────────────────────────────────────────────────┐
│                    子代理执行流程                        │
├─────────────────────────────────────────────────────────┤
│  1. 截图 (_capture_screen)                              │
│     └─> 使用 ScreenTools 截取当前屏幕                    │
│                                                         │
│  2. 分析 (_analyze_screen)                              │
│     └─> 使用多模态模型分析截图，提取可操作元素            │
│                                                         │
│  3. 规划 (_plan_next_action)                            │
│     └─> 根据意图和屏幕内容规划下一步操作                  │
│                                                         │
│  4. 判断完成 (_is_task_complete)                        │
│     └─> 检查任务是否已完成                               │
│                                                         │
│  5. 执行 (_execute_action)                              │
│     └─> 执行具体操作（tap/swipe/input/press/launch）     │
│                                                         │
│  6. 等待响应 (_wait_for_response)                       │
│     └─> 等待界面响应（默认 500ms）                       │
│                                                         │
│  7. 验证 (_verify_result)                               │
│     └─> 验证操作结果                                     │
│                                                         │
│  8. 记录历史                                            │
│     └─> 记录每步操作详情                                 │
└─────────────────────────────────────────────────────────┘
```

### 支持的操作类型

| 操作 | 参数 | 说明 |
|------|------|------|
| `tap` | x, y | 点击坐标 |
| `double_tap` | x, y | 双击坐标 |
| `long_press` | x, y, duration | 长按坐标 |
| `swipe` | x1, y1, x2, y2, duration | 滑动 |
| `input_text` | text | 输入文本 |
| `press_key` | keycode | 按键（back/home/recent） |
| `launch` | package_name | 启动应用 |
| `wait` | duration | 等待 |
| `scroll` | direction | 滚动（up/down/left/right） |

### 配置选项

```yaml
# config/mobile.yaml
subagent:
  enabled: true
  default_max_steps: 20
  step_timeout: 10
  screen_analysis:
    enabled: true
    timeout: 30
    extract_elements: true
  verification:
    enabled: true
    timeout: 5
    retry_count: 2
  recovery:
    enabled: true
    max_retries: 3
    retry_interval: 1
  history:
    enabled: true
    max_records: 100
    save_path: data/mobile/subagent_history
```

---

## 更新日志

### v0.8.8 (2025-04-04)

- 新增手机操作工具 (`phone_operation`)
- 优化 AutoGLM 子代理执行流程
- 新增循环执行模式：截图 -> 分析 -> 规划 -> 执行 -> 验证
- 新增操作历史记录功能
- 新增失败恢复机制
- 新增虚拟屏幕支持

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持移动设备检测
- 支持屏幕控制
- 支持通知管理
- 支持短信收发
- 支持 Linux 环境

---

## 相关文档

- [域系统](./domain-system.md) - 多设备管理
- [设备 ID](./device-id.md) - 设备标识
- [API 文档](../api.md) - 完整 API 参考
