# Checklist

## Phase 1: 编码类垂类智能体核心（参考 Claw Code）

* [ ] src/agents/coding.py 文件已创建

* [ ] CodingAgent 类正确继承 BaseVerticalAgent

* [ ] 核心能力列表定义完整

* [ ] _setup_handlers 方法正确注册所有处理器

* [ ] CodeResult 数据类定义正确

* [ ] execute_code 统一入口正常工作

* [ ] Python 代码执行正常

* [ ] JavaScript/Node.js 代码执行正常

* [ ] Shell/PowerShell 命令执行正常

* [ ] 进程执行核心正常工作

* [ ] 超时控制正常（默认 30 秒，最大 120 秒）

* [ ] 输出截断正常（最大 100KB）

* [ ] Python 语法检查正常

* [ ] 错误位置定位准确

* [ ] 圈复杂度计算正确

* [ ] ruff 风格检查集成正常

* [ ] 安全漏洞模式定义完整

* [ ] SQL 注入检测正常

* [ ] 命令注入检测正常

* [ ] 敏感信息泄露检测正常

* [ ] git_status 处理器正常工作

* [ ] git_commit 处理器正常工作

* [ ] git_branch 处理器正常工作

## Phase 2: 手机端优化（移植 OpenKiwi）

* [ ] src/mobile/accessibility/ 目录已创建

* [ ] GestureExecutor 手势执行器正常工作

* [ ] ScreenCapture 截图捕获正常

* [ ] NodeCache 节点缓存正常（TTL 500ms）

* [ ] GestureResult 回调机制正常

* [ ] src/mobile/notification/ 目录已创建

* [ ] NotificationListener 通知监听正常

* [ ] VerificationCodeExtractor 验证码提取正常

* [ ] NotificationClassifier 通知分类正常

* [ ] NotificationCache 通知缓存正常（200 条）

* [ ] src/mobile/reply/ 目录已创建

* [ ] AutoReplyManager 自动回复管理正常

* [ ] ReplyWhitelist 白名单管理正常

* [ ] RateLimiter 速率限制正常（8次/小时）

* [ ] src/mobile/sandbox/ 目录已创建

* [ ] CodeSandbox 代码沙箱正常

* [ ] DangerCommandDetector 危险命令检测正常

* [ ] SandboxConfig 沙箱配置正常

## Phase 3: 注册与集成

* [ ] src/agents/__init__.py 导出正确

* [ ] src/agents/registry.py 注册正确

* [ ] 全局实例创建正确

* [ ] src/mobile/__init__.py 更新正确

* [ ] src/mobile/backend.py 集成正确

* [ ] 配置文件更新正确

* [ ] 代码执行测试通过

* [ ] 静态分析测试通过

* [ ] 手机端模块测试通过

* [ ] 集成测试通过

## 功能验收

### 编码智能体验收

* [ ] 可执行 Python 代码并返回结果

* [ ] 可执行 JavaScript 代码并返回结果

* [ ] 可执行 Shell 命令并返回结果

* [ ] 可检测代码语法错误

* [ ] 可分析代码复杂度

* [ ] 可检测安全漏洞

* [ ] 可查询 Git 状态

* [ ] 可创建 Git 提交

* [ ] 可管理 Git 分支

### 手机端验收

* [ ] 手势执行延迟在 50-300ms

* [ ] 截图捕获正常

* [ ] 节点缓存 TTL 正常

* [ ] 通知监听正常

* [ ] 验证码提取正常

* [ ] 通知分类正常

* [ ] 自动回复正常

* [ ] 白名单管理正常

* [ ] 速率限制正常

* [ ] 代码沙箱正常

* [ ] 危险命令检测正常

## 安全验收

* [ ] 代码执行有超时限制

* [ ] 输出大小有限制

* [ ] 危险操作被检测

* [ ] 敏感信息不会泄露

* [ ] 执行日志完整记录
