# 视频编辑器全面优化规范

## Why

PyAgent 现有的视频编辑器模块 (`src/video/`) 功能较为基础，缺少完整的命令系统、实时预览、转场效果等核心功能。需要全面优化，继承 Cutia 项目的架构优势，同时针对移动端、Web UI 端和桌面端三个平台进行差异化适配，实现一个功能完善、跨平台的视频编辑解决方案。

## What Changes

### 核心架构优化

* **命令系统**: 引入完整的命令模式，支持撤销/重做操作
* **实时预览**: 实现基于 Canvas/WebGL 的实时预览渲染
* **转场系统**: 实现 12 种转场效果（淡入淡出、滑动、缩放等）
* **贴纸系统**: 新增贴纸轨道和贴纸元素支持
* **场景管理**: 支持多场景/片段管理

### 平台差异化适配

* **移动端**: 触摸手势、小屏幕 UI、性能优化、离线编辑
* **Web UI 端**: 浏览器兼容性、WebCodecs API、IndexedDB 存储
* **桌面端**: 本地文件系统、FFmpeg 渲染、硬件加速

### 功能增强

* **音频分离**: 从视频中分离音频轨道
* **速度控制**: 变速播放、倒放功能
* **字幕系统**: 完整的字幕编辑和样式管理
* **AI 集成**: 智能剪辑、字幕生成、特效推荐

## Impact

* **受影响的模块**: `src/video/`, `src/web/routes/`, `frontend/`, `src/mobile/`
* **新增依赖**: `moderngl`, `pyglet` (桌面端渲染), `ffmpeg-python`
* **前端变更**: Vue.js 视频编辑器组件重构
* **API 变更**: 新增 REST API 端点

---

## ADDED Requirements

### Requirement: 命令系统

系统应提供完整的命令模式实现，支持所有编辑操作的撤销和重做。

#### Scenario: 执行编辑操作

* **WHEN** 用户执行任何编辑操作（添加/删除/移动元素等）
* **THEN** 系统创建对应的命令对象并执行
* **AND** 命令被压入历史栈

#### Scenario: 撤销操作

* **WHEN** 用户请求撤销
* **THEN** 系统从历史栈弹出最近命令并执行 undo
* **AND** 命令被压入重做栈

#### Scenario: 重做操作

* **WHEN** 用户请求重做
* **THEN** 系统从重做栈弹出命令并执行 redo
* **AND** 命令被压入历史栈

#### Scenario: 批量命令

* **WHEN** 用户执行批量操作（如删除多个元素）
* **THEN** 系统将多个命令组合为 BatchCommand
* **AND** 撤销时一次性还原所有操作

### Requirement: 实时预览系统

系统应提供基于 Canvas/WebGL 的实时预览功能。

#### Scenario: 桌面端预览

* **WHEN** 用户在桌面端编辑视频
* **THEN** 系统使用 moderngl 进行 GPU 加速渲染
* **AND** 支持实时预览当前时间轴内容

#### Scenario: Web 端预览

* **WHEN** 用户在浏览器中编辑视频
* **THEN** 系统使用 Canvas 2D 或 WebGL 进行渲染
* **AND** 支持实时预览当前时间轴内容

#### Scenario: 移动端预览

* **WHEN** 用户在移动设备上编辑视频
* **THEN** 系统使用优化后的渲染管线
* **AND** 根据设备性能自动调整预览质量

### Requirement: 转场效果系统

系统应支持多种转场效果。

#### Scenario: 添加转场

* **WHEN** 用户在两个相邻视频片段之间添加转场
* **THEN** 系统创建 TrackTransition 对象
* **AND** 在预览中实时显示转场效果

#### Scenario: 支持的转场类型

系统应支持以下转场类型：
* fade - 淡入淡出
* dissolve - 溶解
* wipe-left/right/up/down - 擦除
* slide-left/right/up/down - 滑动
* zoom-in/out - 缩放

#### Scenario: 转场参数调整

* **WHEN** 用户调整转场持续时间或类型
* **THEN** 系统实时更新转场效果
* **AND** 支持撤销操作

### Requirement: 贴纸系统

系统应支持贴纸元素。

#### Scenario: 添加贴纸

* **WHEN** 用户从贴纸库选择贴纸添加到时间轴
* **THEN** 系统创建 StickerElement 并添加到贴纸轨道
* **AND** 支持调整贴纸位置、大小、旋转

#### Scenario: 贴纸属性编辑

* **WHEN** 用户选中贴纸进行编辑
* **THEN** 系统显示贴纸属性面板
* **AND** 支持修改颜色、透明度、动画效果

### Requirement: 音频分离功能

系统应支持从视频中分离音频。

#### Scenario: 分离音频

* **WHEN** 用户选择视频元素并请求分离音频
* **THEN** 系统创建对应的音频元素
* **AND** 音频元素放置在独立的音频轨道
* **AND** 原视频元素静音

### Requirement: 速度控制

系统应支持视频速度控制。

#### Scenario: 变速播放

* **WHEN** 用户设置视频元素的播放速度
* **THEN** 系统调整元素的 playbackRate 属性
* **AND** 预览中按设定速度播放

#### Scenario: 倒放

* **WHEN** 用户启用倒放功能
* **THEN** 系统设置 reversed 属性为 true
* **AND** 预览中反向播放视频

### Requirement: 移动端适配

系统应针对移动端进行专门优化。

#### Scenario: 触摸手势

* **WHEN** 用户在移动端使用触摸操作
* **THEN** 系统支持捏合缩放、滑动拖动、双指旋转等手势
* **AND** 手势操作流畅无卡顿

#### Scenario: 小屏幕 UI

* **WHEN** 用户在小屏幕设备上使用编辑器
* **THEN** 系统显示适配的移动端 UI 布局
* **AND** 时间轴可横向滚动，面板可折叠

#### Scenario: 性能优化

* **WHEN** 移动设备性能有限
* **THEN** 系统自动降低预览分辨率
* **AND** 减少不必要的渲染帧数

#### Scenario: 离线编辑

* **WHEN** 用户在无网络环境下使用
* **THEN** 系统支持本地存储项目数据
* **AND** 网络恢复后自动同步

### Requirement: Web UI 端适配

系统应针对浏览器环境进行优化。

#### Scenario: 浏览器兼容性

* **WHEN** 用户在不同浏览器中使用
* **THEN** 系统检测浏览器能力并适配
* **AND** 支持 Chrome、Firefox、Safari、Edge 主流版本

#### Scenario: WebCodecs API

* **WHEN** 浏览器支持 WebCodecs API
* **THEN** 系统使用硬件加速的视频解码
* **AND** 提供更流畅的预览体验

#### Scenario: IndexedDB 存储

* **WHEN** 用户在 Web 端保存项目
* **THEN** 系统使用 IndexedDB 存储项目数据
* **AND** 支持大文件存储和快速检索

### Requirement: 桌面端适配

系统应针对桌面环境进行优化。

#### Scenario: 本地文件系统

* **WHEN** 用户在桌面端导入/导出文件
* **THEN** 系统直接访问本地文件系统
* **AND** 支持拖拽导入文件

#### Scenario: FFmpeg 渲染

* **WHEN** 用户导出视频
* **THEN** 系统使用 FFmpeg 进行高质量渲染
* **AND** 支持多种编码器和格式

#### Scenario: 硬件加速

* **WHEN** 桌面设备支持 GPU 加速
* **THEN** 系统启用 NVENC/QuickSync 等硬件编码
* **AND** 显著提升渲染速度

### Requirement: AI 功能集成

系统应深度集成 AI 功能。

#### Scenario: 智能剪辑

* **WHEN** 用户请求 AI 智能剪辑
* **THEN** AI 分析视频内容识别精彩片段
* **AND** 自动生成剪辑建议

#### Scenario: 字幕生成

* **WHEN** 用户请求生成字幕
* **THEN** 系统调用语音识别服务
* **AND** 生成带时间轴的字幕

#### Scenario: 特效推荐

* **WHEN** 用户请求特效推荐
* **THEN** AI 根据视频风格推荐转场和滤镜
* **AND** 一键应用推荐效果

---

## MODIFIED Requirements

### Requirement: 时间线管理器增强

原有 TimelineManager 需要增强以支持新功能。

**新增方法**:
* `addTransition()` - 添加转场效果
* `removeTransition()` - 移除转场效果
* `detachAudio()` - 分离音频
* `updatePlaybackRate()` - 更新播放速度

### Requirement: 类型定义扩展

原有类型定义需要扩展。

**新增类型**:
* `StickerElement` - 贴纸元素
* `TrackTransition` - 轨道转场
* `Transform` - 变换属性（缩放、位置、旋转）
* `Command` - 命令基类

### Requirement: 编辑器核心重构

EditorCore 需要重构以集成命令系统。

**新增组件**:
* `CommandManager` - 命令管理器
* `SelectionManager` - 选择管理器
* `SaveManager` - 自动保存管理器

---

## REMOVED Requirements

无移除的需求。现有功能保持兼容。

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Video Editor Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Platform Layer                        │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │    │
│  │  │  Mobile   │  │   Web     │  │     Desktop       │   │    │
│  │  │  Adapter  │  │  Adapter  │  │     Adapter       │   │    │
│  │  └───────────┘  └───────────┘  └───────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐    │
│  │                    Core Layer                            │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │    │
│  │  │  Command   │ │  Timeline  │ │     Renderer       │  │    │
│  │  │  Manager   │ │  Manager   │ │     Manager        │  │    │
│  │  └────────────┘ └────────────┘ └────────────────────┘  │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │    │
│  │  │  Playback  │ │   Media    │ │      Save          │  │    │
│  │  │  Manager   │ │  Manager   │ │     Manager        │  │    │
│  │  └────────────┘ └────────────┘ └────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐    │
│  │                    AI Layer                              │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │    │
│  │  │   Smart    │ │  Subtitle  │ │     Effect         │  │    │
│  │  │   Edit     │ │  Generator │ │   Recommendation   │  │    │
│  │  └────────────┘ └────────────┘ └────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 命令系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Command System                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Client    │────▶│   Command   │────▶│   Receiver  │       │
│  │             │     │   Manager   │     │  (Editor)   │       │
│  └─────────────┘     └──────┬──────┘     └─────────────┘       │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │  History Stack  │                          │
│                    │  ┌───────────┐  │                          │
│                    │  │  Undo []  │  │                          │
│                    │  │  Redo []  │  │                          │
│                    │  └───────────┘  │                          │
│                    └─────────────────┘                          │
│                                                                  │
│  Commands:                                                       │
│  ├── AddTrackCommand                                             │
│  ├── RemoveTrackCommand                                          │
│  ├── InsertElementCommand                                        │
│  ├── DeleteElementsCommand                                       │
│  ├── MoveElementCommand                                          │
│  ├── SplitElementsCommand                                        │
│  ├── UpdateElementCommand                                        │
│  ├── AddTransitionCommand                                        │
│  ├── DetachAudioCommand                                          │
│  └── BatchCommand                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 平台适配层

```
┌─────────────────────────────────────────────────────────────────┐
│                    Platform Adapters                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Mobile Adapter:                                                 │
│  ├── TouchGestureHandler (捏合、滑动、旋转)                       │
│  ├── MobileUILayout (折叠面板、底部工具栏)                         │
│  ├── PerformanceOptimizer (降分辨率、帧率控制)                     │
│  └── OfflineStorage (本地 SQLite)                                │
│                                                                  │
│  Web Adapter:                                                    │
│  ├── BrowserCapabilityDetector (功能检测)                        │
│  ├── WebCodecsRenderer (硬件加速解码)                             │
│  ├── IndexedDBStorage (浏览器存储)                                │
│  └── ServiceWorker (离线支持)                                    │
│                                                                  │
│  Desktop Adapter:                                                │
│  ├── FileSystemAccess (本地文件系统)                              │
│  ├── FFmpegRenderer (高质量渲染)                                  │
│  ├── HardwareEncoder (NVENC/QuickSync)                          │
│  └── NativeWindow (原生窗口集成)                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 目录结构

```
src/video/
├── __init__.py
├── editor_core.py          # 编辑器核心（重构）
├── manager.py              # 视频管理器
├── project.py              # 项目定义
├── types.py                # 类型定义（扩展）
├── tools.py                # 统一工具接口
├── commands/               # 命令系统（新增）
│   ├── __init__.py
│   ├── base.py             # 命令基类
│   ├── manager.py          # 命令管理器
│   ├── track_commands.py   # 轨道命令
│   ├── element_commands.py # 元素命令
│   └── batch_command.py    # 批量命令
├── managers/               # 管理器（重构）
│   ├── __init__.py
│   ├── timeline.py         # 时间线管理器
│   ├── playback.py         # 播放管理器
│   ├── media.py            # 媒体管理器
│   ├── renderer.py         # 渲染管理器
│   ├── selection.py        # 选择管理器
│   └── save.py             # 保存管理器
├── renderer/               # 渲染系统（新增）
│   ├── __init__.py
│   ├── base.py             # 渲染器基类
│   ├── canvas.py           # Canvas 渲染器
│   ├── opengl.py           # OpenGL 渲染器
│   └── ffmpeg.py           # FFmpeg 渲染器
├── transitions/            # 转场效果（新增）
│   ├── __init__.py
│   ├── base.py             # 转场基类
│   ├── fade.py             # 淡入淡出
│   ├── wipe.py             # 擦除
│   ├── slide.py            # 滑动
│   └── zoom.py             # 缩放
├── platform/               # 平台适配（新增）
│   ├── __init__.py
│   ├── base.py             # 平台适配器基类
│   ├── mobile.py           # 移动端适配
│   ├── web.py              # Web 端适配
│   └── desktop.py          # 桌面端适配
└── ai/                     # AI 功能（新增）
    ├── __init__.py
    ├── smart_edit.py       # 智能剪辑
    ├── subtitle.py         # 字幕生成
    └── effects.py          # 特效推荐
```

---

## 配置文件

### config/video.yaml

```yaml
video:
  editor:
    default_fps: 30
    default_resolution: "1920x1080"
    auto_save_interval: 30  # 秒
    max_undo_history: 100
  
  renderer:
    desktop:
      engine: "ffmpeg"
      hardware_accel: true
      encoder: "nvenc"  # nvenc | qsv | software
    web:
      engine: "canvas"
      webcodecs: true
    mobile:
      engine: "canvas"
      low_quality_mode: true
      max_preview_fps: 15
  
  transitions:
    default_duration: 0.5  # 秒
    types:
      - fade
      - dissolve
      - wipe-left
      - wipe-right
      - wipe-up
      - wipe-down
      - slide-left
      - slide-right
      - slide-up
      - slide-down
      - zoom-in
      - zoom-out
  
  ai:
    smart_edit:
      enabled: true
      model: "video-analysis-v1"
    subtitle:
      enabled: true
      language: "auto"
      provider: "whisper"
    effects:
      enabled: true
      max_suggestions: 5
```

---

## API 端点

### 时间线操作

```
POST /api/video/timeline/undo          # 撤销
POST /api/video/timeline/redo          # 重做
POST /api/video/timeline/transition    # 添加转场
DELETE /api/video/timeline/transition  # 删除转场
POST /api/video/timeline/detach-audio  # 分离音频
```

### 渲染操作

```
POST /api/video/render/preview         # 生成预览帧
POST /api/video/render/export          # 导出视频
GET  /api/video/render/status/:id      # 查询渲染状态
```

### AI 操作

```
POST /api/video/ai/smart-edit          # 智能剪辑
POST /api/video/ai/subtitle            # 生成字幕
POST /api/video/ai/effects             # 特效推荐
```
