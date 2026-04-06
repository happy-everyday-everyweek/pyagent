# PyAgent v0.9.7 发布

## 任务概述
构建并发布PyAgent v0.9.7版本，包括Windows EXE和Android APK。

## 完成路径

### 1. 版本号统一
- 更新README.md徽章和版本号
- 更新AGENTS.md版本历史
- 修复pyproject.toml配置问题

### 2. 构建过程
使用 `build.ps1` 自动构建脚本：
- **Wheel包**: `dist/pyagent-0.9.7-py3-none-any.whl`
- **Windows EXE**: `dist/exe/PyAgent/PyAgent.exe` (13.27 MB)
- **Android APK**: `android/app/build/outputs/apk/debug/app-debug.apk` (7.15 MB)

### 3. GitHub Release
- 创建tag: `v0.9.7`
- 创建Release: https://github.com/happy-everyday-everyweek/pyagent/releases/tag/v0.9.7
- 上传资产:
  - `PyAgent-v0.9.7-windows.exe`
  - `PyAgent-v0.9.7-android.apk`

### 4. 发布内容
v0.9.7新增功能：
- 知识库系统（文档索引、倒排搜索）
- 工作流引擎（触发器、动作、版本管理）
- 本地模型支持（llama.cpp、MNN后端）
- 角色卡系统（PNG元数据、QR分享）
- 研究规划器（任务分解、验证、聚合）
- 调试系统（工具调用跟踪、会话管理）
- 成本追踪（多租户统计、预算告警）
- 虚拟密钥管理（速率限制、配额管理）
- 视图系统（看板、表格、过滤器）
- 自我进化机制（性能监控、自动优化）

## 最终状态
- GitHub仓库: https://github.com/happy-everyday-everyweek/pyagent
- Release页面: https://github.com/happy-everyday-everyweek/pyagent/releases/tag/v0.9.7
- 下载链接:
  - Windows: https://github.com/happy-everyday-everyweek/pyagent/releases/download/v0.9.7/PyAgent-v0.9.7-windows.exe
  - Android: https://github.com/happy-everyday-everyweek/pyagent/releases/download/v0.9.7/PyAgent-v0.9.7-android.apk

## 注意事项
- 构建前需确保pyproject.toml配置正确
- GitHub Token需要有repo权限才能推送和上传Release资产
- APK需要签名才能发布到应用商店

## 可优化项
- 配置release签名用于APK发布
- 添加CI/CD自动构建和发布流程
- 添加更多平台的构建支持（macOS、Linux）
