# 手机操作工具 Spec

## Why

当前移动端模块已有 AutoGLM 子代理基础实现，但未作为统一工具暴露给 AI 调用。本次优化旨在：

1. 将手机操作封装为单一工具，便于 AI 理解和调用
2. 优化子代理实现，提升自然语言驱动的 UI 自动化能力
3. 简化接口，避免过多功能干扰 AI 执行

## What Changes

### 核心变更

- **新增手机操作工具**: 将所有手机操作封装为 `phone_operation` 工具
- **优化 AutoGLM 子代理**: 增强自然语言理解和操作规划能力
- **简化接口**: 一个工具处理所有手机操作场景

### 架构变更

- 增强 `src/mobile/advanced_control/subagent.py` - 优化子代理实现
- 更新 `src/mobile/tool_registry.py` - 注册手机操作工具
- 更新 `config/mobile.yaml` - 添加工具配置

## Impact

- Affected specs: 移动端支持、工具系统
- Affected code:
  - `src/mobile/advanced_control/subagent.py`
  - `src/mobile/tool_registry.py`
  - `config/mobile.yaml`

---

## ADDED Requirements

### Requirement: 手机操作工具

系统 SHALL 提供统一的手机操作工具，支持自然语言驱动的 UI 自动化。

#### Scenario: 自然语言操作手机
- **WHEN** AI 调用 `phone_operation` 工具，传入自然语言意图
- **THEN** 系统使用 screen-operation 垂类模型解析意图
- **AND** 自动规划操作序列
- **AND** 执行操作并返回结果

#### Scenario: 打开应用并发送消息
- **WHEN** 用户意图为 "打开微信发送消息给张三"
- **THEN** 系统解析意图为多步骤操作
- **AND** 执行：打开微信 -> 搜索张三 -> 打开聊天 -> 输入消息 -> 发送
- **AND** 返回操作结果

#### Scenario: 系统设置操作
- **WHEN** 用户意图为 "打开设置并关闭蓝牙"
- **THEN** 系统执行打开设置、导航到蓝牙、关闭蓝牙等操作
- **AND** 返回操作结果

#### Scenario: 虚拟屏幕执行
- **WHEN** 指定 `use_virtual_display: true`
- **THEN** 系统在虚拟屏幕上执行操作
- **AND** 不影响主屏幕

#### Scenario: 最大步骤限制
- **WHEN** 操作需要超过 20 个步骤
- **THEN** 系统在达到最大步骤数后停止
- **AND** 返回已执行的步骤和当前状态

### Requirement: AutoGLM 子代理优化

系统 SHALL 优化 AutoGLM 子代理，提升操作准确性和效率。

#### Scenario: 屏幕内容理解
- **WHEN** 子代理需要理解当前屏幕
- **THEN** 使用多模态模型分析截图
- **AND** 提取可操作元素信息
- **AND** 生成屏幕内容描述

#### Scenario: 操作结果验证
- **WHEN** 执行操作后
- **THEN** 系统截图验证操作结果
- **AND** 判断是否成功
- **AND** 失败时尝试恢复

#### Scenario: 操作历史记录
- **WHEN** 子代理执行操作
- **THEN** 记录每步操作的详细信息
- **AND** 支持查询操作历史

---

## MODIFIED Requirements

### Requirement: 移动端工具注册表

原有工具注册表需要注册手机操作工具。

#### 修改内容

- 注册 `phone_operation` 工具
- 工具描述清晰，便于 AI 理解

---

## REMOVED Requirements

无移除的功能。

---

## 技术实现要点

### 手机操作工具定义

```python
{
    "name": "phone_operation",
    "description": "手机操作工具，通过自然语言控制手机执行各种操作。支持打开应用、点击、滑动、输入文本等操作。",
    "parameters": {
        "intent": {
            "type": "string",
            "description": "自然语言操作意图，如：'打开微信发送消息给张三'、'打开设置关闭蓝牙'",
            "required": true
        },
        "target_app": {
            "type": "string",
            "description": "目标应用包名（可选），如：com.tencent.mm",
            "required": false
        },
        "max_steps": {
            "type": "integer",
            "description": "最大执行步骤数，默认20",
            "required": false,
            "default": 20
        },
        "use_virtual_display": {
            "type": "boolean",
            "description": "是否使用虚拟屏幕执行（不影响主屏幕）",
            "required": false,
            "default": false
        }
    },
    "returns": {
        "success": "操作是否成功",
        "message": "操作结果描述",
        "steps_taken": "执行的步骤数",
        "final_state": "最终屏幕状态描述"
    }
}
```

### 子代理增强

```python
class MobileSubAgent:
    async def run(self, intent: str, max_steps: int = 20) -> SubAgentResult:
        while step_count < max_steps:
            screenshot = await self.capture_screen()
            screen_context = await self.analyze_screen(screenshot)
            
            action = await self.plan_next_action(intent, screen_context)
            result = await self.execute_action(action)
            
            if self.is_task_complete(intent, result):
                return SubAgentResult(success=True, ...)
            
            step_count += 1
```

---

## 配置示例

```yaml
mobile:
  phone_operation:
    enabled: true
    max_steps: 20
    step_timeout: 10
    model: "screen-operation"
    virtual_display:
      enabled: true
      width: 1080
      height: 1920
```

---

## 版本兼容性

- **向后兼容**: 完全兼容现有移动端模块
- **新增能力**: 统一的手机操作工具
- **配置迁移**: 自动添加新配置项
