# Task: 重命名聊天智能体为交互模块

**日期**: 2026-03-28
**任务类型**: 代码重构/模块迁移

## 任务目标

将 `src/chat/` 下的聊天智能体相关模块重命名为交互模块，迁移到 `src/interaction/` 目录。

## 执行路径

### 1. 目录结构变更

**原结构**:
```
src/chat/
├── heart_flow/     → src/interaction/heart_flow/
├── persona/        → src/interaction/persona/
├── planner/        → src/interaction/planner/
├── replyer/        → src/interaction/reply/
└── tools/          → 保留在 src/chat/tools/
```

**新结构**:
```
src/interaction/
├── __init__.py
├── heart_flow/
│   ├── __init__.py
│   ├── behavior_planner.py
│   ├── cycle_detail.py
│   ├── frequency_control.py
│   ├── heartf_chatting.py
│   └── humanized_prompt.py
├── persona/
│   ├── __init__.py
│   └── persona_system.py
├── planner/
│   ├── __init__.py
│   ├── action_manager.py
│   ├── action_modifier.py
│   ├── action_planner.py
│   └── types.py
└── reply/
    ├── __init__.py
    ├── base_generator.py
    ├── group_generator.py
    ├── private_generator.py
    ├── replyer_manager.py
    └── types.py
```

### 2. 迁移的文件列表

| 原路径 | 新路径 |
|--------|--------|
| src/chat/heart_flow/__init__.py | src/interaction/heart_flow/__init__.py |
| src/chat/heart_flow/behavior_planner.py | src/interaction/heart_flow/behavior_planner.py |
| src/chat/heart_flow/cycle_detail.py | src/interaction/heart_flow/cycle_detail.py |
| src/chat/heart_flow/frequency_control.py | src/interaction/heart_flow/frequency_control.py |
| src/chat/heart_flow/heartf_chatting.py | src/interaction/heart_flow/heartf_chatting.py |
| src/chat/heart_flow/humanized_prompt.py | src/interaction/heart_flow/humanized_prompt.py |
| src/chat/persona/persona_system.py | src/interaction/persona/persona_system.py |
| src/chat/planner/__init__.py | src/interaction/planner/__init__.py |
| src/chat/planner/action_manager.py | src/interaction/planner/action_manager.py |
| src/chat/planner/action_modifier.py | src/interaction/planner/action_modifier.py |
| src/chat/planner/action_planner.py | src/interaction/planner/action_planner.py |
| src/chat/planner/types.py | src/interaction/planner/types.py |
| src/chat/replyer/__init__.py | src/interaction/reply/__init__.py |
| src/chat/replyer/base_generator.py | src/interaction/reply/base_generator.py |
| src/chat/replyer/group_generator.py | src/interaction/reply/group_generator.py |
| src/chat/replyer/private_generator.py | src/interaction/reply/private_generator.py |
| src/chat/replyer/replyer_manager.py | src/interaction/reply/replyer_manager.py |
| src/chat/replyer/types.py | src/interaction/reply/types.py |

**总计**: 18个文件迁移

### 3. 更新的导入路径

| 文件 | 变更 |
|------|------|
| src/web/app.py | `src.chat.heart_flow.heartf_chatting` → `src.interaction.heart_flow.heartf_chatting` (2处) |
| tests/test_humanized.py | `src.chat.heart_flow` → `src.interaction.heart_flow` |
| docs/modules/chat-agent.md | 7处路径更新 |
| docs/modules/persona-system.md | 3处路径更新 |

**总计**: 13处导入路径更新

### 4. 新增文件

- `src/interaction/__init__.py` - 交互模块入口
- `src/interaction/persona/__init__.py` - 个性系统入口

## 验证结果

- `src/` 目录下无残留的 `from src.chat` 导入
- `tests/` 目录下无残留的 `from src.chat` 导入
- 所有文件已正确迁移到新位置

## 保留内容

`src/chat/tools/` 目录保留在原位置，包含:
- execute_tool.py
- memory_tool.py
- read_tool.py
- search_tool.py

这些工具类不属于交互模块核心组件，保留在 chat 目录下。

## 反思与优化建议

### 成功之处
1. 迁移过程保持了代码逻辑不变
2. 所有导入路径已正确更新
3. 文档同步更新

### 可优化点
1. 可以考虑将 `src/chat/tools/` 也迁移到 `src/interaction/tools/`，保持模块完整性
2. 可以添加单元测试验证迁移后的导入正确性
3. 建议在 `src/chat/__init__.py` 中添加废弃警告，提示使用新路径

### 后续建议
1. 运行完整测试套件验证功能正常
2. 更新 AGENTS.md 中的模块说明
3. 考虑添加向后兼容的导入别名
