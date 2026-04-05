# v0.8.0 问题修复 Spec

## Why
根据项目全面检查报告，发现了一些需要修复的问题：
1. 3个空壳模块文件（__init__.py为空）
2. 4个Mock/占位符实现需要完善
3. 前端版本号与项目版本不一致

这些问题会影响项目的可用性和完整性，需要及时修复。

## What Changes
- 修复空壳模块：为空的__init__.py文件添加正确的导出
- 完善Mock实现：参考根目录的其他项目（VibeVoice、browser-use等）来完善实现
- 同步版本号：将前端版本号更新为v0.8.0

## Impact
- Affected specs: person模块、core模块、chat模块、agents模块、voice模块、pdf模块、前端
- Affected code: 
  - src/person/__init__.py
  - src/core/__init__.py
  - src/chat/__init__.py
  - src/agents/financial.py
  - src/voice/asr.py
  - src/pdf/parser.py
  - frontend/src/App.vue
  - frontend/src/views/VideoEditor.vue

## ADDED Requirements

### Requirement: 空壳模块修复
系统 SHALL 为所有空的__init__.py文件添加正确的模块导出，确保模块可以正常导入和使用。

#### Scenario: person模块导出
- **WHEN** 用户导入person模块
- **THEN** 系统应正确导出Person和PersonManager类

#### Scenario: core模块导出
- **WHEN** 用户导入core模块
- **THEN** 系统应正确导出核心功能类

#### Scenario: chat模块导出
- **WHEN** 用户导入chat模块
- **THEN** 系统应正确导出聊天相关类

### Requirement: ASR模块完善
系统 SHALL 提供真实的语音识别功能，参考VibeVoice项目的实现。

#### Scenario: 语音识别成功
- **WHEN** 用户提供音频数据
- **THEN** 系统应返回真实的语音转文字结果

### Requirement: PDF解析器完善
系统 SHALL 提供完整的PDF解析功能，包括文本提取和元数据读取。

#### Scenario: PDF解析成功
- **WHEN** 用户提供PDF文件
- **THEN** 系统应正确提取文本内容和元数据

### Requirement: 版本号同步
系统 SHALL 保持前端版本号与项目版本一致。

#### Scenario: 版本号显示
- **WHEN** 用户查看前端界面
- **THEN** 系统应显示正确的版本号v0.8.0

## MODIFIED Requirements

### Requirement: 金融智能体数据获取
金融智能体 SHALL 使用真实API获取股票信息，而非Mock数据。

#### Scenario: 股票信息获取
- **WHEN** 用户查询股票信息
- **THEN** 系统应从真实数据源获取数据

## REMOVED Requirements
无
