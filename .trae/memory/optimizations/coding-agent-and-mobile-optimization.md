# 编码类垂类智能体 + 手机端优化任务记忆

## 任务概述

参考 Claw Code 和 OpenKiwi 两个项目，添加编码类垂类智能体并优化手机端模块。

## 完成路径

### 1. 编码类垂类智能体（参考 Claw Code）

**参考项目**: `claw-code-main/`

**核心移植内容**:
- `rust/crates/runtime/src/prompt.rs` - 系统提示词构建器
- `rust/crates/runtime/src/conversation.rs` - 对话运行时架构

**实现文件**: `src/agents/coding.py`

**核心组件**:
1. `SystemPromptBuilder` - 系统提示词构建器
   - 移植自 Claw Code 的 prompt.rs
   - 支持项目上下文发现
   - 支持 CLAW.md 指令文件加载
   - 支持 Git 状态快照

2. `ProjectContext` - 项目上下文发现
   - 自动发现 CLAW.md 指令文件
   - 获取 Git 状态和差异
   - 支持多级目录搜索

3. `CodingAgent` - 编码智能体
   - 继承 `BaseVerticalAgent`
   - 支持文件读写、编辑
   - 支持命令执行
   - 支持 Git 操作
   - 支持代码分析

### 2. 手机端优化（参考 OpenKiwi）

**参考项目**: `OpenKiwi-master/`

**核心移植内容**:
- `app/src/main/java/com/orizon/openkiwi/core/gui/GuiActionExecutor.kt` - 手势执行器
- `app/src/main/java/com/orizon/openkiwi/core/notification/NotificationProcessor.kt` - 通知处理
- `app/src/main/java/com/orizon/openkiwi/core/notification/AutoReplyManager.kt` - 自动回复
- `app/src/main/java/com/orizon/openkiwi/core/code/CodeSandbox.kt` - 代码沙箱

**实现文件**:
1. `src/mobile/verification_code.py` - 验证码提取器
   - 支持多种验证码格式识别
   - 支持有效期提取
   - 支持来源识别

2. `src/mobile/notification_classifier.py` - 通知分类器
   - 支持通知重要性评估
   - 支持子类别检测
   - 支持关键词和实体提取

3. `src/mobile/auto_reply.py` - 自动回复管理器
   - 支持白名单管理
   - 支持速率限制（8次/小时）
   - 支持回复模板

4. `src/mobile/code_sandbox.py` - 代码执行沙箱
   - 支持危险命令检测
   - 支持超时控制
   - 支持输出截断

5. `src/mobile/gesture_executor.py` - 手势执行器
   - 支持低延迟手势执行（50-300ms）
   - 支持节点缓存（TTL 500ms）
   - 支持多种手势（点击、滑动、长按、缩放等）

## 可优化点

### 1. 编码智能体优化
- 可以添加更多代码分析工具（如 pylint、mypy 集成）
- 可以添加代码格式化功能（如 black、prettier）
- 可以添加更多 Git 操作（如 merge、rebase、cherry-pick）

### 2. 手机端优化
- 可以添加 LLM 驱动的智能回复
- 可以添加通知摘要功能
- 可以添加屏幕内容理解（OCR + LLM）
- 可以添加自动化工作流触发器

### 3. 架构优化
- 可以将验证码提取和通知分类整合为流水线
- 可以添加配置文件支持（如 `config/mobile.yaml`）
- 可以添加单元测试覆盖

## 注意事项

1. **代码风格**: 新代码有一些 ruff 警告（中文全角字符、可变类属性），不影响功能
2. **导入检查**: 所有模块都可以正常导入
3. **版本更新**: CHANGELOG.md 已更新为 v0.9.9

## 冲突解决

### 手势执行器与屏幕工具冲突

**问题**: `gesture_executor.py` 和 `screen_tools.py` 都实现了手势操作，存在功能重复。

**解决方案**: 重构 `gesture_executor.py`，让它复用 `ScreenTools` 的核心功能：
- `GestureExecutor` 内部使用 `ScreenTools` 执行实际操作
- 添加节点缓存（TTL 500ms）提升性能
- 添加手势结果回调机制
- 整合截图功能

**优势**:
- 避免代码重复
- 保持 API 兼容性
- 增强功能（节点缓存、回调）

## 文档更新

### README.md
- 添加编码智能体说明（第 21 节）
- 添加手机端增强说明（第 22 节）

### docs/modules/agent-system.md
- 更新版本号为 v0.9.9
- 添加垂类智能体架构图
- 添加编码智能体详细说明
- 添加手机端增强模块说明
- 添加使用示例代码

## 文件变更清单

### 新增文件
- `src/agents/coding.py`
- `src/mobile/verification_code.py`
- `src/mobile/notification_classifier.py`
- `src/mobile/auto_reply.py`
- `src/mobile/code_sandbox.py`
- `src/mobile/gesture_executor.py`
- `.trae/specs/coding-agent/spec.md`
- `.trae/specs/coding-agent/tasks.md`
- `.trae/specs/coding-agent/checklist.md`

### 修改文件
- `src/agents/__init__.py`
- `src/mobile/__init__.py`
- `CHANGELOG.md`
- `README.md`
- `docs/modules/agent-system.md`
