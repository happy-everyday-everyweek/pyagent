# 原生视频编辑器文档 v0.9.0

本文档详细描述 PyAgent v0.9.0 原生视频编辑器的设计和实现。

## 概述

v0.9.0 全面优化视频编辑器，继承 Cutia 项目架构优势，支持移动端、Web UI 端和桌面端三个平台。

### 核心特性

- **命令系统**: 完整的撤销/重做支持
- **转场效果**: 12种转场类型
- **平台适配**: 移动端/Web端/桌面端差异化适配
- **渲染系统**: Canvas和FFmpeg双渲染引擎
- **AI集成**: 智能剪辑、字幕生成、特效推荐

## 架构设计

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

## 目录结构

```
src/video/
├── __init__.py
├── editor_core.py          # 编辑器核心
├── manager.py              # 视频管理器
├── project.py              # 项目定义
├── types.py                # 类型定义
├── tools.py                # 统一工具接口
├── commands/               # 命令系统
│   ├── __init__.py
│   ├── base.py             # 命令基类
│   ├── manager.py          # 命令管理器
│   ├── track_commands.py   # 轨道命令
│   ├── element_commands.py # 元素命令
│   ├── transition_commands.py # 转场命令
│   └── batch_command.py    # 批量命令
├── managers/               # 管理器
│   ├── __init__.py
│   ├── selection.py        # 选择管理器
│   └── save.py             # 保存管理器
├── renderer/               # 渲染系统
│   ├── __init__.py
│   ├── base.py             # 渲染器基类
│   ├── canvas.py           # Canvas 渲染器
│   ├── ffmpeg.py           # FFmpeg 渲染器
│   └── queue.py            # 渲染队列
├── transitions/            # 转场效果
│   ├── __init__.py
│   ├── base.py             # 转场基类
│   ├── fade.py             # 淡入淡出
│   ├── wipe.py             # 擦除
│   ├── slide.py            # 滑动
│   ├── zoom.py             # 缩放
│   └── utils.py            # 工具函数
├── platform/               # 平台适配
│   ├── __init__.py
│   ├── base.py             # 平台适配器基类
│   ├── detector.py         # 平台检测器
│   ├── mobile.py           # 移动端适配
│   ├── web.py              # Web 端适配
│   └── desktop.py          # 桌面端适配
└── ai/                     # AI 功能
    ├── __init__.py
    ├── smart_edit.py       # 智能剪辑
    ├── subtitle.py         # 字幕生成
    └── effects.py          # 特效推荐
```

## 命令系统

### 基本用法

```python
from src.video.commands import CommandManager, AddTrackCommand

manager = CommandManager()

command = AddTrackCommand(
    project_id="project_123",
    track_type="video",
    name="新轨道"
)

manager.execute(command)
manager.undo()
manager.redo()
```

### 支持的命令

| 命令 | 功能 |
|------|------|
| AddTrackCommand | 添加轨道 |
| RemoveTrackCommand | 删除轨道 |
| InsertElementCommand | 插入元素 |
| DeleteElementsCommand | 删除元素 |
| MoveElementCommand | 移动元素 |
| SplitElementsCommand | 分割元素 |
| AddTransitionCommand | 添加转场 |
| DetachAudioCommand | 分离音频 |

## 转场效果

### 支持的转场类型

| 类型 | 说明 |
|------|------|
| fade | 淡入淡出 |
| dissolve | 溶解 |
| wipe-left/right/up/down | 擦除（四方向） |
| slide-left/right/up/down | 滑动（四方向） |
| zoom-in | 放大转场 |
| zoom-out | 缩小转场 |

### 使用示例

```python
from src.video.transitions import get_transition
import numpy as np

frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
frame2 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

transition = get_transition('fade', duration=0.5)
result = transition.apply(frame1, frame2, progress=0.5)
```

## 平台适配

### 平台差异

| 功能 | 移动端 | Web端 | 桌面端 |
|------|--------|-------|--------|
| 渲染引擎 | Canvas | Canvas | FFmpeg |
| 硬件加速 | 有限 | WebCodecs | NVENC/QuickSync |
| 存储 | SQLite | IndexedDB | 文件系统 |
| 触摸手势 | 支持 | 支持 | 不支持 |
| 离线编辑 | 支持 | ServiceWorker | 原生支持 |

### 获取平台适配器

```python
from src.video.platform import get_platform_adapter

adapter = get_platform_adapter()
print(adapter.get_platform_name())
print(adapter.detect_capabilities())
```

## 渲染系统

### Canvas 渲染器（Web/移动端）

```python
from src.video.renderer import CanvasRenderer, RenderConfig

renderer = CanvasRenderer(width=1920, height=1080)
config = RenderConfig(
    output_path="/output/video.mp4",
    format="mp4",
    resolution=(1920, 1080),
    fps=30,
    quality="high"
)
job = renderer.render(project, config)
```

### FFmpeg 渲染器（桌面端）

```python
from src.video.renderer import FFmpegRenderer

renderer = FFmpegRenderer()
if FFmpegRenderer.is_available():
    print(f"FFmpeg version: {FFmpegRenderer.get_version()}")
    job = renderer.render(project, config)
```

## AI 功能

### 智能剪辑

```python
from src.video.ai import SmartEditService

service = SmartEditService()

highlights = service.analyze_highlights("/path/to/video.mp4")
scenes = service.detect_scenes("/path/to/video.mp4")
result = service.auto_edit("/path/to/video.mp4", style="vlog", target_duration=60.0)
```

### 字幕生成

```python
from src.video.ai import SubtitleService

service = SubtitleService(provider="whisper", language="auto")
segments = service.generate_subtitles(
    video_path="/path/to/video.mp4",
    language="zh",
    auto_translate=True,
    target_languages=["en", "ja"]
)
service.export_srt("/path/to/output.srt")
```

### 特效推荐

```python
from src.video.ai import EffectRecommendationService

service = EffectRecommendationService()
recommendations = service.get_all_recommendations("/path/to/video.mp4")
```

## REST API

### 时间线操作

```
POST /api/video/{project_id}/undo          # 撤销
POST /api/video/{project_id}/redo          # 重做
POST /api/video/{project_id}/transition    # 添加转场
DELETE /api/video/{project_id}/transition/{id}  # 删除转场
POST /api/video/{project_id}/detach-audio  # 分离音频
```

### AI 操作

```
POST /api/video/ai/smart-edit          # 智能剪辑
POST /api/video/ai/subtitle            # 生成字幕
POST /api/video/ai/effects             # 特效推荐
```

### 渲染操作

```
POST /api/video/{project_id}/render    # 开始渲染
GET  /api/video/render/{job_id}/status # 查询状态
```

## 配置文件

```yaml
video:
  editor:
    default_fps: 30
    default_resolution: "1920x1080"
    auto_save_interval: 30
    max_undo_history: 100
  
  renderer:
    desktop:
      engine: "ffmpeg"
      hardware_accel: true
      encoder: "nvenc"
    web:
      engine: "canvas"
      webcodecs: true
    mobile:
      engine: "canvas"
      low_quality_mode: true
      max_preview_fps: 15
  
  transitions:
    default_duration: 0.5
    types:
      - fade
      - dissolve
      - wipe-left
      - wipe-right
      - slide-left
      - slide-right
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

## 故障排除

### FFmpeg 未找到

1. 安装 FFmpeg: `apt-get install ffmpeg` (Linux)
2. 配置 ffmpeg.path 指向正确路径
3. 验证: `ffmpeg -version`

### 导出失败

1. 检查磁盘空间
2. 验证输入文件格式
3. 查看错误日志
4. 尝试降低分辨率

### AI 服务超时

1. 检查 AI 服务状态
2. 缩短视频长度
3. 降低分析精度
