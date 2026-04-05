# 视频编辑器轨道命令实现

## 任务概述

在 PyAgent 项目中实现视频编辑器的轨道命令系统，参考 Cutia 项目的实现。

## 完成路径

### 1. 代码分析

- 分析了 Cutia 项目的轨道命令实现：
  - `cutia-main/apps/web/src/lib/commands/timeline/track/add-track.ts`
  - `cutia-main/apps/web/src/lib/commands/timeline/track/remove-track.ts`
  - `cutia-main/apps/web/src/lib/commands/timeline/track/reorder-tracks.ts`
  - `cutia-main/apps/web/src/lib/commands/timeline/track/toggle-track-mute.ts`
  - `cutia-main/apps/web/src/lib/commands/timeline/track/toggle-track-visibility.ts`

- 分析了 PyAgent 现有架构：
  - `src/video/commands/base.py` - 命令基类
  - `src/video/project.py` - 视频项目类
  - `src/video/manager.py` - 视频管理器单例
  - `src/video/types.py` - 类型定义（Track, TrackType 等）

### 2. 实现的命令

创建了 `src/video/commands/track_commands.py`，包含以下命令：

#### AddTrackCommand
- 参数: project_id, track_type, index=None, name=None
- 功能: 添加轨道到项目，支持指定插入位置
- undo: 移除添加的轨道
- get_track_id(): 返回创建的轨道ID

#### RemoveTrackCommand
- 参数: project_id, track_id
- 功能: 移除轨道，保存轨道数据用于恢复
- 限制: 主轨道不可移除
- undo: 恢复轨道到原位置

#### ReorderTracksCommand
- 参数: project_id, track_ids (新的轨道顺序)
- 功能: 按新顺序重排轨道
- undo: 恢复原顺序

#### ToggleTrackMuteCommand
- 参数: project_id, track_id
- 功能: 切换静音状态
- 限制: 仅视频和音频轨道支持静音
- undo: 恢复原状态

#### ToggleTrackVisibilityCommand
- 参数: project_id, track_id
- 功能: 切换可见性
- 限制: 主轨道不可隐藏
- undo: 恢复原状态

### 3. 代码质量检查

- 通过 ruff 代码检查
- 通过 Python 语法检查
- 通过功能测试验证

### 4. 文档更新

- 更新了 `src/video/commands/__init__.py` 导出新命令
- 更新了 `CHANGELOG.md` 添加版本记录

## 设计决策

### 项目ID参数

与 Cutia 使用 EditorCore 单例获取当前项目不同，PyAgent 的命令需要显式传入 project_id 参数。这是因为：
1. PyAgent 支持多项目同时打开
2. 命令需要明确操作哪个项目
3. 通过 video_manager.get_project(project_id) 获取项目实例

### 状态保存策略

所有命令在 execute() 时保存完整的轨道状态列表（通过 to_dict() 序列化），在 undo() 时恢复。这种策略：
1. 实现简单，不易出错
2. 支持任意复杂的状态恢复
3. 与 Cutia 的实现一致

### 主轨道保护

RemoveTrackCommand 和 ToggleTrackVisibilityCommand 都检查 is_main 属性，防止对主轨道进行非法操作。

## 可优化点

1. **性能优化**: 当前每次 undo 都恢复整个轨道列表，可以考虑只恢复变更的部分
2. **批量操作**: 可以添加 BatchCommand 支持批量轨道操作
3. **事件通知**: 可以添加轨道变更事件通知，方便 UI 更新
4. **类型检查**: 可以添加更严格的类型检查和参数验证

## 文件变更

- 新增: `src/video/commands/track_commands.py`
- 修改: `src/video/commands/__init__.py`
- 修改: `CHANGELOG.md`
