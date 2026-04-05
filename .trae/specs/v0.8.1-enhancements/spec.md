# PyAgent v0.8.1 规范文档

## Why

v0.8.0 版本虽然引入了大量新功能，但在用户体验、系统智能化和安全性方面仍有提升空间。v0.8.1 版本旨在：
1. 优化分布式架构，使其更加智能灵活
2. 增强斜杠命令功能，支持更多操作
3. 新增意图分析层，智能识别用户意图并直接跳转
4. 优化 IM 通道安全性，引入验证机制
5. 优化拟人系统，使对话更加自然
6. 重构设置页面，提供更好的配置体验
7. 全面优化手机操作功能

## What Changes

### 核心架构变更

- **新增意图分析层**: 在消息发送前进行意图识别，智能路由到对应模块
- **分布式架构优化**: 更智能的数据同步和冲突解决机制
- **IM 通道验证机制**: 仅接收经过验证的私聊消息

### 功能增强

- **斜杠命令增强**: 支持打开应用、打开文档、修改设置等操作
- **拟人系统优化**: 参考 MaiMaiBot 优化情感表达和对话风格
- **设置页面重构**: 分类展示，支持更多配置项的可视化修改
- **手机操作优化**: 新增更智能的手机控制模式

### 新增模块

- `src/intent/`: 意图分析模块
- `src/im/verification/`: IM 通道验证模块
- `src/mobile/advanced_control/`: 高级手机控制模块

### 配置文件更新

- 新增 `config/intent.yaml`: 意图分析配置
- 新增 `config/im_verification.yaml`: IM 验证配置
- 更新 `config/persona.yaml`: 拟人系统配置
- 更新 `config/mobile.yaml`: 手机控制配置

## Impact

- Affected specs: 交互模块、IM 适配器、移动端支持、前端 UI
- Affected code: 
  - `src/interaction/` - 意图分析集成
  - `src/im/` - 验证机制
  - `src/mobile/` - 高级控制
  - `frontend/src/` - 设置页面重构

---

## ADDED Requirements

### Requirement: 意图分析系统

系统 SHALL 在用户发送消息前进行意图分析，识别用户意图并智能路由。

#### Scenario: 打开文件意图
- **WHEN** 用户输入 "打开我的工作文档" 或 "/open 工作文档"
- **THEN** 系统识别为 OPEN_FILE 意图
- **AND** 直接打开文件管理页面并定位到对应文件
- **AND** 不发送到聊天模块

#### Scenario: 打开应用意图
- **WHEN** 用户输入 "打开日历" 或 "/calendar"
- **THEN** 系统识别为 OPEN_APP 意图
- **AND** 直接打开日历应用页面
- **AND** 不发送到聊天模块

#### Scenario: 创建日程意图
- **WHEN** 用户输入 "明天下午3点开会" 或 "创建日程..."
- **THEN** 系统识别为 CREATE_EVENT 意图
- **AND** 直接打开日历创建页面并预填信息
- **AND** 不发送到聊天模块

#### Scenario: 创建待办意图
- **WHEN** 用户输入 "提醒我明天交报告" 或 "创建待办..."
- **THEN** 系统识别为 CREATE_TODO 意图
- **AND** 直接打开待办创建页面并预填信息
- **AND** 不发送到聊天模块

#### Scenario: 修改设置意图
- **WHEN** 用户输入 "把模型改成 GPT-4" 或 "/settings model GPT-4"
- **THEN** 系统识别为 MODIFY_SETTINGS 意图
- **AND** 直接修改对应设置并返回确认
- **AND** 不发送到聊天模块

#### Scenario: 普通对话意图
- **WHEN** 用户输入普通对话内容
- **THEN** 系统识别为 CHAT 意图
- **AND** 正常发送到聊天模块处理

### Requirement: IM 通道验证机制

系统 SHALL 对 IM 通道实施验证机制，仅接收经过验证的私聊消息。验证状态持久化存储，用户只需验证一次。

#### Scenario: 新用户首次私聊
- **WHEN** 未验证用户首次发送私聊消息
- **THEN** 系统返回绑定引导消息
- **AND** 生成6位随机验证码
- **AND** 存储验证码与用户ID的关联
- **AND** 不处理该消息内容

#### Scenario: 用户发送验证码
- **WHEN** 用户发送6位数字验证码
- **THEN** 系统验证验证码是否正确
- **AND** 如果正确，标记用户为已验证
- **AND** **持久化存储验证状态到数据库**
- **AND** 返回验证成功消息
- **AND** 后续消息正常处理

#### Scenario: 已验证用户发送消息
- **WHEN** 已验证用户发送私聊消息
- **THEN** 系统从数据库检查验证状态
- **AND** 验证状态永久有效，无需重复验证
- **AND** 消息路由到聊天模块

#### Scenario: 已验证用户重新连接
- **WHEN** 已验证用户断开连接后重新连接
- **THEN** 系统从数据库加载验证状态
- **AND** 用户无需再次验证
- **AND** 直接正常处理消息

#### Scenario: 未验证用户发送消息
- **WHEN** 未验证用户发送消息（非验证码）
- **THEN** 系统忽略该消息
- **AND** 返回提示需要先验证

#### Scenario: 验证码过期
- **WHEN** 验证码生成超过10分钟
- **THEN** 验证码自动失效
- **AND** 用户需要重新请求绑定

#### Scenario: 管理员取消用户验证
- **WHEN** 管理员取消某用户的验证状态
- **THEN** 系统从数据库删除该用户的验证记录
- **AND** 该用户下次发送消息时需要重新验证

### Requirement: 斜杠命令增强

系统 SHALL 支持通过斜杠命令执行更多操作。

#### Scenario: 打开应用命令
- **WHEN** 用户输入 "/calendar" 或 "/日历"
- **THEN** 系统打开日历应用
- **AND** 显示日历界面

#### Scenario: 打开文档命令
- **WHEN** 用户输入 "/word" 或 "/ppt" 或 "/excel"
- **THEN** 系统打开对应的文档编辑器
- **AND** 创建新文档或显示最近文档

#### Scenario: 打开设置命令
- **WHEN** 用户输入 "/settings" 或 "/设置"
- **THEN** 系统打开设置页面

#### Scenario: 创建日程命令
- **WHEN** 用户输入 "/event 明天下午3点开会"
- **THEN** 系统打开日历创建页面
- **AND** 预填 "明天下午3点开会"

#### Scenario: 创建待办命令
- **WHEN** 用户输入 "/todo 完成报告"
- **THEN** 系统打开待办创建页面
- **AND** 预填 "完成报告"

#### Scenario: 快捷操作命令
- **WHEN** 用户输入 "/open 文件名" 或 "/launch 应用名"
- **THEN** 系统执行对应操作
- **AND** 返回操作结果

### Requirement: 拟人系统优化（参考 MaiBot）

系统 SHALL 参考 MaiBot 优化拟人系统，使对话更加自然。

#### Scenario: 个性状态随机切换
- **WHEN** 系统生成回复
- **THEN** 根据 state_probability 概率随机切换个性状态
- **AND** 个性状态从预设列表中随机选择
- **AND** 状态切换平滑过渡

#### Scenario: 对话目标分析
- **WHEN** 用户发送消息
- **THEN** 系统分析对话目标
- **AND** 生成多个可能的对话目标
- **AND** 每个目标包含 goal 和 reasoning
- **AND** 最多保持 3 个活跃目标

#### Scenario: 情感表达优化
- **WHEN** 用户表达积极情绪
- **THEN** 系统回复带有适当的积极情感
- **AND** 情感表达更加细腻和自然

#### Scenario: 对话风格多样化
- **WHEN** 系统生成回复
- **THEN** 回复风格根据上下文动态调整
- **AND** 避免重复使用相同的表达方式
- **AND** 更加口语化和自然
- **AND** 回复简短，一次只回复一个话题

#### Scenario: 上下文理解增强
- **WHEN** 用户使用指代词（如"它"、"那个"）
- **THEN** 系统能够正确理解指代内容
- **AND** 回复与上下文保持连贯

#### Scenario: 个性状态平滑切换
- **WHEN** 对话主题或情绪发生变化
- **THEN** 个性状态平滑过渡
- **AND** 不出现突兀的风格变化

#### Scenario: 主动行为优化
- **WHEN** 对话出现沉默或停顿
- **THEN** 系统能够主动发起话题
- **AND** 主动行为更加自然和适时

#### Scenario: 用户记忆管理
- **WHEN** 系统与用户交互
- **THEN** 自动记录用户相关信息到 memory_points
- **AND** 记忆点格式：category:content:weight
- **AND** 支持按分类检索记忆
- **AND** 支持相似度去重

### Requirement: 设置页面重构

系统 SHALL 重构设置页面，提供更好的配置体验。设置分为**同步设置**和**本地设置**两类。

#### Scenario: 设置分类展示
- **WHEN** 用户打开设置页面
- **THEN** 设置项按以下分类展示：
  - **通用（本地设置）**：语言、主题、通知、快捷键
  - **AI Agent（同步设置）**：模型配置、协作模式、提示词模板
  - **应用（同步设置）**：日历、邮件、文档、视频
  - **分布式（同步设置）**：域管理、同步设置、设备管理
  - **实验室功能（本地设置）**：实验性功能开关

#### Scenario: 同步设置自动同步
- **WHEN** 用户修改同步设置（如模型配置、协作模式等）
- **THEN** 设置自动同步到域内所有设备
- **AND** 其他设备自动应用新设置
- **AND** 显示同步状态指示器

#### Scenario: 本地设置仅本机生效
- **WHEN** 用户修改本地设置（如主题、语言、快捷键等）
- **THEN** 设置仅在本设备生效
- **AND** 不同步到其他设备
- **AND** 显示"仅本机"标识

#### Scenario: 设置同步冲突处理
- **WHEN** 多设备同时修改同一同步设置
- **THEN** 使用"最后修改优先"策略
- **AND** 显示冲突提示
- **AND** 用户可选择保留哪个版本

#### Scenario: 模型配置可视化修改
- **WHEN** 用户修改模型配置
- **THEN** 提供下拉选择、输入框等可视化组件
- **AND** 配置实时保存
- **AND** 自动同步到其他设备
- **AND** 无需手动编辑配置文件

#### Scenario: 域管理可视化
- **WHEN** 用户管理域
- **THEN** 显示当前域信息、设备列表
- **AND** 支持创建、加入、离开域操作
- **AND** 支持设备能力查看

#### Scenario: 同步设置可视化
- **WHEN** 用户配置同步设置
- **THEN** 提供同步模式选择、同步间隔设置
- **AND** 显示同步状态和历史

#### Scenario: 实验室功能管理
- **WHEN** 用户查看实验室功能
- **THEN** 显示所有实验性功能列表
- **AND** 提供开关控制
- **AND** 显示功能说明和风险提示
- **AND** 显示"仅本机"标识

### Requirement: 分布式架构优化

系统 SHALL 优化分布式架构，使其更加智能灵活。

#### Scenario: 智能同步模式选择
- **WHEN** 系统检测到网络条件变化
- **THEN** 自动选择最佳同步模式
- **AND** 网络好时使用实时同步
- **AND** 网络差时切换到增量同步

#### Scenario: 冲突智能解决
- **WHEN** 多设备同时修改同一文件
- **THEN** 系统智能分析冲突内容
- **AND** 尝试自动合并
- **AND** 无法自动合并时提示用户选择

#### Scenario: 设备能力感知
- **WHEN** 新设备加入域
- **THEN** 系统自动检测设备能力
- **AND** 根据能力分配任务
- **AND** 高性能设备承担更多计算任务

#### Scenario: 离线支持增强
- **WHEN** 设备离线
- **THEN** 本地操作正常进行
- **AND** 操作记录本地缓存
- **AND** 恢复在线后自动同步

### Requirement: 手机操作功能优化（参考 Operit 项目）

系统 SHALL 全面优化手机操作功能，参考 Operit 项目的 AutoGLM 子代理模式实现智能控制。

#### Scenario: AutoGLM 子代理模式
- **WHEN** 用户输入自然语言操作意图（如"打开微信发送消息给张三"）
- **THEN** 系统调用 UI 子代理自动规划操作序列
- **AND** 子代理使用已配置的 `screen-operation` 垂类模型（autoglm-phone-9b）
- **AND** 自动执行：打开应用 -> 定位元素 -> 执行操作 -> 验证结果
- **AND** 返回操作结果和最终 UI 状态

#### Scenario: 虚拟屏幕执行
- **WHEN** 需要不影响主屏幕执行操作
- **THEN** 系统在虚拟屏幕上创建会话
- **AND** 使用 agent_id 标识虚拟屏幕会话
- **AND** 操作在虚拟屏幕独立执行
- **AND** 主屏幕不受影响

#### Scenario: 并行子代理执行
- **WHEN** 需要同时执行多个独立任务
- **THEN** 系统支持并行运行多个子代理
- **AND** 每个子代理使用不同的 agent_id
- **AND** 每个子代理操作不同的应用
- **AND** 同一应用不能同时在两个虚拟屏操作
- **AND** 返回所有子代理的执行结果

#### Scenario: 会话复用
- **WHEN** 需要继续之前的操作
- **THEN** 系统支持复用 agent_id
- **AND** 保持同一虚拟屏幕和应用上下文
- **AND** 继续执行后续操作
- **AND** 无需重新启动应用

#### Scenario: 屏幕内容理解
- **WHEN** 系统获取屏幕截图
- **THEN** 使用多模态模型自动识别屏幕内容
- **AND** 提取文本、按钮、图片等信息
- **AND** 生成 UI 层次结构
- **AND** 支持基于内容的智能操作

---

## MODIFIED Requirements

### Requirement: IM 消息处理流程

原有消息处理流程需要增加意图分析和验证检查。

#### 修改后的流程
```
用户消息 -> IM适配器 -> 验证检查 -> 意图分析 -> 路由分发
                                    ├-> OPEN_FILE -> 文件管理
                                    ├-> OPEN_APP -> 应用页面
                                    ├-> CREATE_EVENT -> 日历创建
                                    ├-> CREATE_TODO -> 待办创建
                                    ├-> MODIFY_SETTINGS -> 设置修改
                                    └-> CHAT -> 聊天模块
```

### Requirement: 斜杠面板组件

原有斜杠面板需要增加更多命令选项。

#### 修改后的命令列表
- 文档类：Word、PPT、Excel
- 应用类：日历、任务、邮件、笔记、浏览器、文件
- 配置类：设置、Mate模式、新话题
- 新增：日程创建、待办创建、快捷操作

### Requirement: 前端设置页面

原有设置页面需要重构为分类展示。

#### 修改后的结构
```
设置页面
├── 通用
│   ├── 语言设置
│   ├── 主题设置（亮色/暗色）
│   ├── 通知设置
│   └── 快捷键设置
├── AI Agent
│   ├── 模型配置
│   ├── 协作模式
│   ├── 提示词模板
│   └── 拟人化设置
├── 应用
│   ├── 日历设置
│   ├── 邮件设置
│   ├── 文档设置
│   └── 视频设置
├── 分布式
│   ├── 域管理
│   ├── 同步设置
│   └── 设备管理
└── 实验室功能
    ├── 功能列表
    └── 风险提示
```

---

## REMOVED Requirements

### Requirement: 无

本版本不移除任何功能，仅进行优化和增强。

---

## 技术实现要点

### 手机控制模块（参考 Operit 项目）

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

class IntentType(Enum):
    CHAT = "chat"
    OPEN_FILE = "open_file"
    OPEN_APP = "open_app"
    CREATE_EVENT = "create_event"
    CREATE_TODO = "create_todo"
    MODIFY_SETTINGS = "modify_settings"
    EXECUTE_COMMAND = "execute_command"

@dataclass
class IntentResult:
    intent_type: IntentType
    confidence: float
    parameters: dict[str, Any]
    raw_message: str

class IntentAnalyzer:
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def analyze(self, message: str, context: dict) -> IntentResult:
        pass
    
    def quick_match(self, message: str) -> Optional[IntentResult]:
        pass
```

### IM 验证模块（持久化存储）

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import random
import json

@dataclass
class VerifiedUser:
    user_id: str
    platform: str
    verified_at: datetime
    nickname: Optional[str] = None

class IMVerificationManager:
    def __init__(self, db_path: str = "data/im_verification.json"):
        self.db_path = db_path
        self.code_length = 6
        self.expire_minutes = 10
        self._sessions: dict[str, 'VerificationSession'] = {}
        self._verified_users: dict[str, VerifiedUser] = {}
        self._load_verified_users()
    
    def _load_verified_users(self):
        """从数据库加载已验证用户"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for user_id, user_data in data.get('verified_users', {}).items():
                    self._verified_users[user_id] = VerifiedUser(
                        user_id=user_id,
                        platform=user_data['platform'],
                        verified_at=datetime.fromisoformat(user_data['verified_at']),
                        nickname=user_data.get('nickname')
                    )
        except FileNotFoundError:
            self._verified_users = {}
    
    def _save_verified_users(self):
        """保存已验证用户到数据库"""
        data = {
            'verified_users': {
                user_id: {
                    'platform': user.platform,
                    'verified_at': user.verified_at.isoformat(),
                    'nickname': user.nickname
                }
                for user_id, user in self._verified_users.items()
            }
        }
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def generate_code(self, user_id: str, platform: str) -> str:
        """生成验证码"""
        code = ''.join([str(random.randint(0, 9)) for _ in range(self.code_length)])
        now = datetime.now()
        self._sessions[user_id] = VerificationSession(
            user_id=user_id,
            platform=platform,
            code=code,
            created_at=now,
            expires_at=now + timedelta(minutes=self.expire_minutes)
        )
        return code
    
    def verify(self, user_id: str, code: str, nickname: str = None) -> bool:
        """验证验证码并持久化验证状态"""
        session = self._sessions.get(user_id)
        if not session:
            return False
        if datetime.now() > session.expires_at:
            del self._sessions[user_id]
            return False
        if session.code == code:
            self._verified_users[user_id] = VerifiedUser(
                user_id=user_id,
                platform=session.platform,
                verified_at=datetime.now(),
                nickname=nickname
            )
            self._save_verified_users()
            del self._sessions[user_id]
            return True
        return False
    
    def is_verified(self, user_id: str) -> bool:
        """检查用户是否已验证（从数据库加载）"""
        return user_id in self._verified_users
    
    def revoke_verification(self, user_id: str) -> bool:
        """撤销用户验证状态"""
        if user_id in self._verified_users:
            del self._verified_users[user_id]
            self._save_verified_users()
            return True
        return False

@dataclass
class VerificationSession:
    user_id: str
    platform: str
    code: str
    created_at: datetime
    expires_at: datetime
```

### 手机控制模块（参考 Operit 项目 AutoGLM 子代理）

```python
from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum

from src.llm import LLMClient, TaskType

@dataclass
class SubAgentResult:
    success: bool
    message: str
    final_state: Optional[str] = None  # 最终屏幕状态描述
    steps_taken: int = 0
    data: Optional[dict] = None

class MobileSubAgent:
    def __init__(self, agent_id: str, llm_client: LLMClient, target_app: Optional[str] = None):
        self.agent_id = agent_id
        self.llm_client = llm_client
        self.target_app = target_app
        self._context: dict[str, Any] = {}
    
    async def run(self, intent: str, max_steps: int = 20) -> SubAgentResult:
        result = await self.llm_client.generate(
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": intent}
            ],
            task_type=TaskType.SCREEN_OPERATION
        )
        return self._parse_result(result)
    
    async def get_screenshot(self) -> bytes:
        pass
    
    async def execute_action(self, action: str, params: dict) -> bool:
        pass
    
    def _build_system_prompt(self) -> str:
        return """你是一个手机操作助手，可以根据用户的自然语言意图执行手机操作。
        
你可以执行以下操作：
- tap(x, y): 点击屏幕坐标
- swipe(start_x, start_y, end_x, end_y): 滑动
- type(text): 输入文本
- press(key): 按键
- launch(package): 启动应用
- wait(ms): 等待

请根据用户意图规划操作序列并执行。"""

class MobileControlManager:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self._virtual_displays: dict[str, MobileSubAgent] = {}
        self._cached_agent_id: Optional[str] = None
    
    async def run_subagent_main(self, intent: str, max_steps: int = 20, 
                                target_app: str = None) -> SubAgentResult:
        agent = MobileSubAgent("main", self.llm_client, target_app)
        return await agent.run(intent, max_steps)
    
    async def run_subagent_virtual(self, intent: str, agent_id: str = None, 
                                   max_steps: int = 20, target_app: str = None) -> SubAgentResult:
        if agent_id and agent_id in self._virtual_displays:
            agent = self._virtual_displays[agent_id]
        else:
            agent = MobileSubAgent(agent_id or self._generate_agent_id(), self.llm_client, target_app)
            self._virtual_displays[agent.agent_id] = agent
        self._cached_agent_id = agent.agent_id
        return await agent.run(intent, max_steps)
    
    async def run_subagent_parallel(self, intents: list[dict]) -> list[SubAgentResult]:
        import asyncio
        tasks = [
            self.run_subagent_virtual(
                intent=i["intent"],
                agent_id=i.get("agent_id"),
                target_app=i.get("target_app")
            )
            for i in intents
        ]
        return await asyncio.gather(*tasks)
    
    async def close_all_virtual_displays(self) -> bool:
        self._virtual_displays.clear()
        self._cached_agent_id = None
        return True
    
    def _generate_agent_id(self) -> str:
        import uuid
        return f"agent_{uuid.uuid4().hex[:8]}"
```

---

## 版本兼容性

- **向后兼容**: v0.8.1 完全兼容 v0.8.0
- **配置迁移**: 自动迁移 v0.8.0 配置到新格式
- **数据兼容**: 所有 v0.8.0 数据可直接使用
