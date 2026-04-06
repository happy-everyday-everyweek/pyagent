# 视频编辑器转场工具函数实现

## 任务执行路径

1. 查阅参考文件 `d:\agent\cutia-main\apps\web\src\lib\timeline\transition-utils.ts` 了解 Cutia 的实现
2. 查看项目现有类型定义 `src/video/types.py`，确认 `TrackTransition`、`TransitionType`、`TimelineElement`、`Track` 等类型已定义
3. 查看现有 `src/video/commands/transition_commands.py` 了解项目中转场相关的实现模式
4. 创建 `src/video/transitions/` 目录
5. 创建 `src/video/transitions/__init__.py` 导出所有函数
6. 创建 `src/video/transitions/utils.py` 实现 6 个工具函数：
   - `build_track_transition`: 构建转场对象
   - `add_transition_to_track`: 添加转场到轨道
   - `remove_transition_from_track`: 从轨道移除转场
   - `are_elements_adjacent`: 检测两个元素是否相邻
   - `cleanup_transitions_for_track`: 清理无效转场
   - `get_transition_at_time`: 获取指定时间点的转场
7. 运行导入测试验证代码正确性
8. 运行功能测试验证所有函数正常工作

## 任务执行路径可优化的地方

- 可考虑添加 `find_adjacent_pairs` 函数到公开 API 中，便于外部使用
- 可添加 `get_transition_for_pair` 函数，用于获取特定元素对之间的转场

## 项目结果可优化的地方

- `Track` 类使用 dataclass 定义，在 `add_transition_to_track` 等函数中创建新对象时需要手动复制所有字段，可考虑使用 `dataclasses.replace()` 简化代码
- 可添加单元测试文件 `tests/test_transition_utils.py` 进行更全面的测试
