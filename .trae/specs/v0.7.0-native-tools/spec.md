# PyAgent v0.7.0 Spec - 原生工具与分布式系统

## Why

PyAgent需要从纯AI对话框架升级为具备原生生产力工具的智能平台。用户期望AI不仅能对话，还能直接操作文档、编辑视频，同时为未来的分布式协作奠定基础。通过集成ONLYOFFICE Docs的文档编辑能力和Cutia的视频剪辑能力，并赋予它们AI原生特性，PyAgent将成为真正的AI生产力平台。

## What Changes

### 核心功能

* **原生文档编辑器**: 集成ONLYOFFICE Docs，支持Word/Excel/PPT在线编辑，AI辅助写作、格式化、数据分析

* **原生视频剪辑器**: 集成Cutia视频编辑器，支持AI智能剪辑、字幕生成、特效添加

* **域系统**: 定义设备域，支持多设备数据同步（类Git分支合并机制）

* **分布式准备**: 设备类型参数、设备发现、数据同步协议

* **Kimi IM通道**: 新增Kimi智能助手作为IM接入通道

### 界面优化

* **斜杠菜单增强**: 顶部显示PPT(橙)、Word(蓝)、Excel(绿)三个彩色图标，点击创建对应文档并进入编辑器

## Impact

* Affected specs: LLM客户端、工具系统、设备系统、IM模块、前端UI

* Affected code:

  * `src/tools/` - 新增文档工具和视频工具

  * `src/device/` - 扩展域系统和同步机制

  * `src/im/` - 新增Kimi适配器

  * `frontend/` - 新增编辑器页面和斜杠菜单优化

***

## ADDED Requirements

### Requirement: 原生文档编辑器

系统应提供基于ONLYOFFICE Docs的原生文档编辑能力，支持AI辅助功能。

#### Scenario: 创建Word文档

* **WHEN** 用户点击斜杠菜单中的Word图标或在聊天中请求创建文档

* **THEN** 系统创建新的.docx文档，打开编辑器页面，AI可辅助写作、校对、格式化

#### Scenario: AI辅助编辑

* **WHEN** 用户在文档编辑器中选中文字并请求AI帮助

* **THEN** AI提供改写、扩写、缩写、翻译、校对等建议，用户可选择采纳

#### Scenario: Excel数据分析

* **WHEN** 用户在Excel编辑器中请求数据分析

* **THEN** AI分析数据趋势，生成图表建议，提供公式推荐

#### Scenario: PPT智能生成

* **WHEN** 用户请求生成演示文稿

* **THEN** AI根据主题自动生成大纲、建议布局、推荐配图

### Requirement: 原生视频剪辑器

系统应提供基于Cutia的原生视频编辑能力，支持AI智能剪辑功能。

#### Scenario: AI智能剪辑

* **WHEN** 用户上传视频素材并请求AI剪辑

* **THEN** AI分析视频内容，自动识别精彩片段，生成剪辑建议

#### Scenario: 字幕自动生成

* **WHEN** 用户请求为视频添加字幕

* **THEN** AI自动转录语音，生成时间轴字幕，支持多语言翻译

#### Scenario: AI特效推荐

* **WHEN** 用户请求为视频添加特效

* **THEN** AI根据视频风格推荐转场、滤镜、背景音乐

#### Scenario: 视频导出

* **WHEN** 用户完成编辑并请求导出

* **THEN** 系统渲染视频并保存到指定位置，支持多种格式和分辨率

### Requirement: 域系统与数据同步

系统应支持设备域的概念，实现类Git的多设备数据同步。

#### Scenario: 创建域

* **WHEN** 用户首次启动系统或主动创建域

* **THEN** 系统生成唯一的域ID，当前设备成为域主设备

#### Scenario: 加入域

* **WHEN** 新设备通过域ID请求加入域

* **THEN** 域主设备验证请求，新设备加入域并获取域内所有设备列表

#### Scenario: 数据同步（实时模式）

* **WHEN** 用户在设备A上进行操作且同步模式为实时

* **THEN** 操作立即同步到域内所有在线设备

#### Scenario: 数据同步（定时模式）

* **WHEN** 用户设置同步间隔为N分钟

* **THEN** 系统每N分钟自动同步一次数据

#### Scenario: 冲突合并

* **WHEN** 多设备同时修改同一数据产生冲突

* **THEN** 系统采用类Git的三方合并策略，自动合并或提示用户解决冲突

#### Scenario: 设备记录

* **WHEN** 设备连接到域

* **THEN** 该设备信息被记录到域内所有设备上，包括设备ID、连接时间、设备类型

### Requirement: 设备类型参数

系统应为每个设备定义类型参数，支持分布式场景。

#### Scenario: 设备类型识别

* **WHEN** 设备首次启动

* **THEN** 系统自动识别或让用户选择设备类型（PC/Mobile/Server/Edge）

#### Scenario: 类型能力声明

* **WHEN** 设备加入域

* **THEN** 设备声明其能力（计算能力、存储能力、网络能力）

### Requirement: 斜杠菜单优化

系统应优化斜杠菜单，提供快速创建文档的入口。

#### Scenario: 显示文档图标

* **WHEN** 用户打开斜杠菜单

* **THEN** 菜单顶部显示三个彩色图标：PPT(橙色)、Word(蓝色)、Excel(绿色)

#### Scenario: 创建Word文档

* **WHEN** 用户点击Word图标

* **THEN** 系统创建新Word文档，跳转到文档编辑器页面

#### Scenario: 创建Excel文档

* **WHEN** 用户点击Excel图标

* **THEN** 系统创建新Excel文档，跳转到表格编辑器页面

#### Scenario: 创建PPT文档

* **WHEN** 用户点击PPT图标

* **THEN** 系统创建新PPT文档，跳转到演示文稿编辑器页面

### Requirement: Kimi IM通道

系统应支持Kimi智能助手作为IM接入通道。

#### Scenario: Kimi配置

* **WHEN** 用户配置Kimi bot-token

* **THEN** 系统验证token并建立与Kimi的连接

#### Scenario: Kimi消息接收

* **WHEN** Kimi平台推送消息到系统

* **THEN** 系统解析消息并转发给对话处理模块

#### Scenario: Kimi消息发送

* **WHEN** 系统需要回复Kimi用户

* **THEN** 系统通过Kimi API发送回复消息

***

## MODIFIED Requirements

### Requirement: 设备ID系统（v0.6.0扩展）

设备ID系统需要扩展以支持域和设备类型。

**新增字段**:

* `domain_id`: 所属域ID

* `device_type`: 设备类型（pc/mobile/server/edge）

* `device_capabilities`: 设备能力声明

### Requirement: 统一工具接口（v0.6.0扩展）

统一工具接口需要支持文档工具和视频工具的集成。

**新增工具类型**:

* `DocumentTool`: 文档操作工具

* `VideoTool`: 视频操作工具

***

## REMOVED Requirements

无移除的需求。

***

## 技术架构

### 文档编辑器架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Editor Module                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Word Editor │  │Excel Editor │  │ PPT Editor  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│  ┌──────▼────────────────▼────────────────▼──────┐         │
│  │              ONLYOFFICE Docs SDK               │         │
│  └────────────────────────┬──────────────────────┘         │
│                           │                                 │
│  ┌────────────────────────▼──────────────────────┐         │
│  │              AI Assistant Layer                │         │
│  │  - 智能写作  - 数据分析  - 演示生成            │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 视频编辑器架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Video Editor Module                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Timeline  │  │   Preview   │  │   Assets    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│  ┌──────▼────────────────▼────────────────▼──────┐         │
│  │               Cutia EditorCore                 │         │
│  │  - PlaybackManager  - TimelineManager         │         │
│  │  - MediaManager     - RendererManager         │         │
│  └────────────────────────┬──────────────────────┘         │
│                           │                                 │
│  ┌────────────────────────▼──────────────────────┐         │
│  │              AI Agent Layer                    │         │
│  │  - 智能剪辑  - 字幕生成  - 特效推荐            │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 域同步架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Domain System                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Device A (PC)     Device B (Mobile)    Device C (Server)  │
│   ┌─────────┐       ┌─────────┐          ┌─────────┐       │
│   │ Branch  │       │ Branch  │          │ Branch  │       │
│   │  main   │       │ mobile  │          │ server  │       │
│   └────┬────┘       └────┬────┘          └────┬────┘       │
│        │                 │                    │             │
│        └────────────┬────┴────────────────────┘             │
│                     │                                        │
│              ┌──────▼──────┐                                 │
│              │ Sync Engine │                                 │
│              │ (Git-like)  │                                 │
│              └──────┬──────┘                                 │
│                     │                                        │
│              ┌──────▼──────┐                                 │
│              │ Conflict    │                                 │
│              │ Resolution  │                                 │
│              └─────────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

### AI工具集成

文档和视频编辑器都通过统一工具接口与AI系统交互：

```python
class DocumentTool(UnifiedTool):
    """文档操作工具"""
    name = "document"
    
    async def activate(self, context: ToolContext) -> bool:
        # 初始化文档编辑器连接
        pass
    
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        # 执行文档操作（创建、编辑、分析等）
        pass
    
    async def dormant(self, context: ToolContext) -> bool:
        # 释放资源
        pass

class VideoTool(UnifiedTool):
    """视频操作工具"""
    name = "video"
    
    async def activate(self, context: ToolContext) -> bool:
        # 初始化视频编辑器连接
        pass
    
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        # 执行视频操作（剪辑、字幕、特效等）
        pass
    
    async def dormant(self, context: ToolContext) -> bool:
        # 释放资源
        pass
```

***

## 配置文件

### config/domain.yaml

```yaml
domain:
  id: ""  # 自动生成
  name: "default"
  sync:
    mode: "realtime"  # realtime | interval
    interval: 5  # 分钟，仅interval模式有效
  devices:
    max_devices: 10
    auto_discover: true
```

### config/kimi.yaml

```yaml
kimi:
  enabled: false
  bot_token: ""
  api_base: "https://api.kimi.com"
  timeout: 30
```

***

## 数据存储

### data/domain/

```
data/domain/
├── domain_info.json      # 域信息
├── devices/              # 设备记录
│   ├── device_001.json
│   └── device_002.json
├── sync/                 # 同步数据
│   ├── commits/          # 提交历史
│   └── conflicts/        # 冲突记录
└── documents/            # 文档存储
```

