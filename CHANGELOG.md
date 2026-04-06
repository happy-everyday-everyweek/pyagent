# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

***

## \[0.9.8] - 2026-04-05

### 新增

**统一后端架构**

- 添加 `src/core/` 统一后端核心模块
- 添加 `src/core/platform/` 平台适配层
- 支持 Web 端和移动端共用同一后端代码
- 支持平台检测和能力识别

**平台适配系统**

- 添加 `PlatformDetector` 平台检测器
- 添加 `PlatformAdapter` 平台适配器
- 支持 Web、Android、iOS、Desktop 四种平台
- 支持工具类别过滤（根据平台能力）

**Android 原生应用重构**

- 添加 `ProotManager.kt` proot 环境管理
- 添加 `PythonRuntime.kt` Python 运行时管理
- 添加 `WebViewManager.kt` WebView 管理
- 添加 `BackendService.kt` 后台服务
- 添加 `BootReceiver.kt` 开机启动接收器
- 添加原生 UI 界面（初始化、聊天、任务、设置）
- 支持 WebView 加载 Web UI（多端统一）
- 支持封装完整 Linux 环境和 Python 运行时

**构建系统增强**

- 更新 `build.ps1` 支持 `-BundlePython` 参数
- 添加 `download-linux.ps1` Linux 环境下载脚本
- 支持打包 Alpine Linux rootfs 到 APK
- 支持多架构构建（arm64-v8a, armeabi-v7a, x86_64）

### 变更

- 重构 `src/web/app.py` 使用统一核心
- 重构 `src/mobile/backend.py` 使用统一核心
- 更新 `android/app/build.gradle.kts` 添加新依赖
- 更新 `AndroidManifest.xml` 添加必要权限

### 移除

- 移除 Web 后端中的重复代码
- 移除移动端后端中的独立实现
