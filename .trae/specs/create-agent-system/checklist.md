# Checklist

## Phase 1: 项目基础架构

* [ ] 项目目录结构完整创建

* [ ] pyproject.toml配置正确

* [ ] requirements.txt依赖完整

* [ ] .env.example环境变量模板完整

* [ ] models.yaml模型配置包含四层模型

* [ ] policies.yaml安全策略配置完整

## Phase 2: LLM模型层

* [ ] 模型配置加载器正常工作

* [ ] 统一LLM客户端可调用不同模型

* [ ] 类型定义完整

* [ ] 模型自动选择逻辑正确

* [ ] 模型故障切换机制正常

## Phase 3: 聊天Agent核心（参考MaiBot HeartFChatting）

* [ ] heartf\_chatting.py主循环正常工作

* [ ] cycle\_detail.py循环信息记录正确

* [ ] frequency\_control.py频率控制正常

* [ ] 消息监控循环\_loopbody正常

* [ ] 动作执行\_execute\_action正常

* [ ] ActionPlanner规划器工作正常

* [ ] ActionManager动作管理器工作正常

* [ ] ActionModifier动作修改器工作正常

* [ ] build\_planner\_prompt提示词构建正确

* [ ] plan动作规划逻辑正确

* [ ] JSON解析\_extract\_json\_from\_markdown正常

* [ ] ReplyerManager回复器管理正常

* [ ] GroupGenerator群聊回复器正常

* [ ] PrivateGenerator私聊回复器正常

* [ ] generate\_reply回复生成正常

* [ ] 搜索工具可调用搜索模块

* [ ] 阅读工具可读取内容

* [ ] 执行工具可调用执行Agent（模块间通信）

* [ ] 记忆工具可操作记忆系统

## Phase 4: 执行Agent（支持内部多智能体协作）

* [ ] 执行Agent核心正常工作

* [ ] ReAct推理引擎工作正常

* [ ] 任务队列管理正常

* [ ] 同步/异步执行模式正常

* [ ] 任务状态追踪正常

* [ ] 工具基类定义完整

* [ ] 工具注册中心工作正常

* [ ] 工具目录生成正确

* [ ] Shell工具可执行命令

* [ ] 文件工具可操作文件

* [ ] 浏览器工具可操作浏览器

* [ ] 网络工具可发送请求

* [ ] 子Agent基类定义完整

* [ ] 搜索子Agent工作正常

* [ ] 浏览器子Agent工作正常

* [ ] 子Agent任务委派机制正常

* [ ] 子Agent结果聚合正常

## Phase 5: 用户信息系统（参考MaiBot Person）

* [ ] Person用户类工作正常

* [ ] PersonManager用户管理器正常

* [ ] register\_person用户注册正常

* [ ] memory\_points记忆点管理正常

* [ ] group\_nick\_name群昵称管理正常

* [ ] build\_relationship用户关系构建正常

## Phase 6: 表达学习系统（参考MaiBot ExpressionLearner）

* [ ] ExpressionLearner表达学习器正常

* [ ] JargonMiner黑话挖掘器正常

* [ ] learn\_and\_store学习存储正常

* [ ] \_filter\_expressions表达方式过滤正常

* [ ] \_process\_jargon\_entries黑话处理正常

## Phase 7: 记忆系统

* [ ] 记忆存储正常工作

* [ ] 短期记忆正常

* [ ] 长期记忆正常

* [ ] 记忆检索正常

* [ ] 记忆管理器工作正常

* [ ] 记忆整理正常

* [ ] 记忆遗忘机制正常

## Phase 8: 安全策略系统（参考OpenAkita）

* [ ] 策略引擎工作正常

* [ ] 四区路径保护正常

* [ ] 命令风险分级正确

* [ ] 工具策略控制正常

* [ ] 高危操作确认机制正常

* [ ] 工具抖动检测正常

* [ ] 死亡开关正常

## Phase 9: MCP协议支持

* [ ] MCP客户端可连接服务器

* [ ] stdio传输协议正常

* [ ] streamable\_http传输协议正常

* [ ] sse传输协议正常

* [ ] 工具发现与注册正常

* [ ] 服务器管理器工作正常

* [ ] 连接状态监控正常

## Phase 10: Skills技能系统

* [ ] 技能加载器可加载技能

* [ ] SKILL.md解析器工作正常

* [ ] 技能注册中心工作正常

* [ ] 技能执行器可执行技能

* [ ] 脚本执行环境正常

* [ ] 技能工具生成正确

## Phase 11: IM平台适配器

* [ ] IM适配器基类定义完整

* [ ] 统一消息格式正确

* [ ] 消息路由正常

* [ ] OneBot适配器可收发消息（微信/QQ）

* [ ] 钉钉适配器可收发消息

* [ ] 飞书适配器可收发消息

* [ ] 企业微信适配器可收发消息

## Phase 12: Web服务

* [ ] FastAPI应用正常启动

* [ ] 聊天API工作正常

* [ ] 任务API工作正常

* [ ] 配置API工作正常

* [ ] MCP管理API工作正常

* [ ] WebSocket实时通信正常

* [ ] 前端项目结构完整

* [ ] 聊天对话组件正常

* [ ] 任务监控组件正常

* [ ] 配置管理组件正常

* [ ] 系统状态仪表盘正常

## Phase 13: 集成与测试

* [ ] 主入口正常启动

* [ ] 服务启动脚本正常

* [ ] Docker部署配置正确

* [ ] 单元测试通过

* [ ] 集成测试通过

* [ ] 使用文档完整

## 功能验收

* [ ] 用户可通过Web界面与Agent聊天

* [ ] 聊天Agent可通过模块间通信调用执行Agent

* [ ] 执行Agent内部可进行多智能体协作

* [ ] 异步任务可查询状态

* [ ] MCP工具可正常调用

* [ ] Skills技能可正常执行

* [ ] 记忆系统可存储和检索记忆

* [ ] 安全策略可阻止高危操作

* [ ] 微信/QQ/钉钉/飞书/企微可收发消息

* [ ] 表达学习系统可学习用户语言风格

* [ ] 用户信息系统可管理用户信息

