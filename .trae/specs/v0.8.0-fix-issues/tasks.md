# Tasks

- [x] Task 1: 修复空壳模块
  - [x] SubTask 1.1: 修复 src/person/__init__.py - 添加Person和PersonManager的导出
  - [x] SubTask 1.2: 修复 src/core/__init__.py - 添加核心功能类的导出
  - [x] SubTask 1.3: 修复 src/chat/__init__.py - 添加聊天相关类的导出

- [x] Task 2: 完善ASR语音识别模块
  - [x] SubTask 2.1: 参考VibeVoice项目的audio_utils.py实现音频加载功能
  - [x] SubTask 2.2: 实现基于Whisper或其他ASR引擎的真实语音识别
  - [x] SubTask 2.3: 添加音频格式转换和预处理功能

- [x] Task 3: 完善PDF解析器
  - [x] SubTask 3.1: 添加基于PyPDF2或pdfplumber的备用解析方案
  - [x] SubTask 3.2: 修复基础解析返回空文档的问题
  - [x] SubTask 3.3: 完善元数据读取功能

- [x] Task 4: 完善金融智能体
  - [x] SubTask 4.1: 集成真实的金融数据API（如yfinance）
  - [x] SubTask 4.2: 替换Mock数据为真实API调用
  - [x] SubTask 4.3: 添加错误处理和API限流机制

- [x] Task 5: 同步前端版本号
  - [x] SubTask 5.1: 更新 frontend/src/App.vue 中的版本号为v0.8.0

- [x] Task 6: 完善视频编辑器前端
  - [x] SubTask 6.1: 实现splitClip函数

# Task Dependencies
- [Task 2] 依赖 VibeVoice项目的参考实现
- [Task 4] 需要先确认API选择
