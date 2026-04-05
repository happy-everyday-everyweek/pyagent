# IM 通道模块 — 开源贡献任务清单

> **模块负责人**: TBD
> **最后更新**: 2026-02-28
> **状态**: 开放认领中

## 概述

OpenAkita 通过统一的 `ChannelAdapter` 接口接入各 IM 平台。目前已接入 6 个平台（Telegram、飞书、钉钉、企业微信、QQ 官方机器人、OneBot），但部分平台存在功能不全的问题，同时还有多个国际主流 IM 尚未接入。

IM 通道模块是相对独立的子系统，非常适合社区贡献者参与。每个适配器只需实现 `ChannelAdapter` 基类的抽象方法，不涉及核心 Agent 逻辑的修改。

## 架构速览

```
平台消息 → Adapter (解析) → UnifiedMessage → Gateway (预处理) → Agent
                                                    ↓
Agent 回复 ← Adapter (发送) ← OutgoingMessage ← Gateway (路由)
```

**关键文件**:
- 基类: `src/openakita/channels/base.py` — `ChannelAdapter` 抽象类
- 消息类型: `src/openakita/channels/types.py` — `UnifiedMessage`, `OutgoingMessage`, `MediaFile`
- 消息网关: `src/openakita/channels/gateway.py` — 统一路由和预处理
- 适配器目录: `src/openakita/channels/adapters/` — 各平台实现
- 注册入口: `src/openakita/main.py` — `_create_bot_adapter()` 和 `start_im_channels()`

**必须实现的抽象方法**:
| 方法 | 说明 |
|------|------|
| `start()` | 启动适配器（建立连接、启动 webhook 等） |
| `stop()` | 停止适配器（断开连接、清理资源） |
| `send_message(message)` | 发送消息（统一入口） |
| `download_media(media)` | 下载平台侧的媒体文件到本地 |
| `upload_media(path, mime_type)` | 上传本地文件到平台 |

**可选覆盖的方法**:
| 方法 | 说明 |
|------|------|
| `send_file()` | 发送文件 |
| `send_voice()` | 发送语音 |
| `send_typing()` | 发送"正在输入"状态 |
| `get_chat_info()` | 获取聊天信息 |
| `get_user_info()` | 获取用户信息 |
| `delete_message()` | 删除消息 |
| `edit_message()` | 编辑消息 |

---

## 一、已接入平台 — 功能增强任务

### 1.1 企业微信 (WeWork) — 功能补全

当前企业微信通过"智能机器人"接入，功能受限较大。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| WW-01 | 支持接收语音消息 | ⭐⭐ 中等 | P1 | 🟡 待认领 |
| WW-02 | 支持接收文件/视频消息 | ⭐⭐ 中等 | P1 | 🟡 待认领 |
| WW-03 | 支持群聊中接收图片消息（当前仅单聊支持） | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| WW-04 | 探索通过"企业微信应用"方式接入（功能更全面） | ⭐⭐⭐ 困难 | P2 | 🟡 待认领 |
| WW-05 | 支持发送文件（当前降级为文本描述） | ⭐⭐ 中等 | P2 | 🟡 待认领 |

> **备注**: 企业微信智能机器人本身 API 存在限制，部分功能增强可能需要切换到"自建应用"接入方式。WW-04 是一个较大的探索性任务，建议有企业微信开发经验的贡献者认领。

### 1.2 钉钉 (DingTalk) — 功能增强

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| DD-01 | 文件发送优化：当前降级为链接，探索原生文件发送能力 | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| DD-02 | 语音发送优化：当前降级为文件，探索原生语音消息支持 | ⭐⭐ 中等 | P3 | 🟡 待认领 |
| DD-03 | 支持钉钉卡片消息（ActionCard / FeedCard） | ⭐⭐ 中等 | P3 | 🟡 待认领 |

### 1.3 QQ 官方机器人 — 功能增强

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| QQ-01 | 支持本地文件上传发送（当前需公网 URL） | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| QQ-02 | 支持语音消息发送优化（silk 格式转换自动化） | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| QQ-03 | 支持 Markdown 模板消息 | ⭐ 简单 | P3 | 🟡 待认领 |

### 1.4 通用增强

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| GEN-01 | 适配器健康检查机制（心跳检测、自动重连指标上报） | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| GEN-02 | 统一的消息速率限制框架（各平台 API 限流适配） | ⭐⭐⭐ 困难 | P2 | 🟡 待认领 |
| GEN-03 | 适配器单元测试覆盖率提升（Mock 框架 + 各平台测试） | ⭐⭐ 中等 | P2 | 🟡 待认领 |

---

## 二、新平台接入任务 — 国际 IM

### 2.1 Discord

**平台简介**: 全球最大的游戏和社区即时通讯平台，拥有服务器/频道/线程体系，Bot API 成熟。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| DC-01 | Discord 适配器基础实现（文字消息收发） | ⭐⭐ 中等 | **P0** | 🟡 待认领 |
| DC-02 | 支持图片/文件/语音消息收发 | ⭐⭐ 中等 | P1 | 🟡 待认领 |
| DC-03 | 支持 Slash Commands | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| DC-04 | 支持 Thread（帖子/线程）消息 | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| DC-05 | 支持 Embed 富文本消息 | ⭐ 简单 | P3 | 🟡 待认领 |
| DC-06 | 支持 Reaction（表情回应）事件 | ⭐ 简单 | P3 | 🟡 待认领 |

**技术要点**:
- 推荐依赖: `discord.py` (>=2.0) 或 `nextcord`
- 接入方式: WebSocket Gateway (无需公网 IP)
- Bot Token 通过 [Discord Developer Portal](https://discord.com/developers/applications) 获取
- 需要处理 Gateway Intents（MESSAGE_CONTENT intent 需申请）
- 参考: [Discord API 文档](https://discord.com/developers/docs)

**接入示例配置**:
```bash
DISCORD_ENABLED=true
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_INTENTS=message_content,guilds,guild_messages,dm_messages
```

---

### 2.2 Slack

**平台简介**: 全球企业协作首选平台，拥有丰富的 App/Bot API、Block Kit UI 框架和事件订阅系统。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| SL-01 | Slack 适配器基础实现（文字消息收发） | ⭐⭐ 中等 | **P0** | 🟡 待认领 |
| SL-02 | 支持图片/文件收发 | ⭐⭐ 中等 | P1 | 🟡 待认领 |
| SL-03 | 支持 Thread（消息线程）回复 | ⭐⭐ 中等 | P1 | 🟡 待认领 |
| SL-04 | 支持 Block Kit 富文本消息 | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| SL-05 | 支持 Slash Commands | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| SL-06 | 支持 Socket Mode（无需公网 IP） | ⭐⭐ 中等 | P1 | 🟡 待认领 |

**技术要点**:
- 推荐依赖: `slack-bolt` (Python) + `slack-sdk`
- 接入方式: Socket Mode (WebSocket, 推荐) 或 Events API (HTTP, 需公网)
- App 通过 [Slack API](https://api.slack.com/apps) 创建
- 需要配置 OAuth Scopes: `chat:write`, `channels:history`, `files:read`, `files:write` 等
- 参考: [Slack Bolt for Python](https://slack.dev/bolt-python/)

**接入示例配置**:
```bash
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token    # Socket Mode 需要
SLACK_SIGNING_SECRET=your-signing-secret
```

---

### 2.3 WhatsApp (Business API)

**平台简介**: 全球用户量最大的即时通讯应用（20亿+用户），通过 WhatsApp Business API / Cloud API 接入。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| WA-01 | WhatsApp 适配器基础实现（文字消息收发） | ⭐⭐⭐ 困难 | **P0** | 🟡 待认领 |
| WA-02 | 支持图片/文件/语音/视频消息收发 | ⭐⭐ 中等 | P1 | 🟡 待认领 |
| WA-03 | 支持消息模板 (Message Templates) | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| WA-04 | 支持互动式消息（按钮、列表） | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| WA-05 | Webhook 签名验证和安全机制 | ⭐⭐ 中等 | P1 | 🟡 待认领 |

**技术要点**:
- 接入方式: WhatsApp Cloud API (Meta 提供) — 通过 Webhook 接收消息，REST API 发送消息
- 需要 Meta Business 账户 + WhatsApp Business App
- **需要公网 HTTPS URL** 接收 Webhook（或使用 ngrok 等隧道工具）
- 24 小时消息窗口限制：用户发消息后 24 小时内可自由回复，超时需使用消息模板
- 参考: [WhatsApp Cloud API 文档](https://developers.facebook.com/docs/whatsapp/cloud-api)

**接入示例配置**:
```bash
WHATSAPP_ENABLED=true
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_VERIFY_TOKEN=your-verify-token      # Webhook 验证
WHATSAPP_WEBHOOK_PORT=9881
```

---

### 2.4 Microsoft Teams

**平台简介**: 微软企业协作平台，广泛用于企业内部沟通，通过 Bot Framework 接入。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| MT-01 | Teams 适配器基础实现（文字消息收发） | ⭐⭐⭐ 困难 | P1 | 🟡 待认领 |
| MT-02 | 支持图片/文件收发 | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| MT-03 | 支持 Adaptive Cards 富文本消息 | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| MT-04 | 支持 Teams Channel 和 Group Chat | ⭐⭐ 中等 | P2 | 🟡 待认领 |

**技术要点**:
- 推荐依赖: `botbuilder-core`, `botbuilder-integration-aiohttp`
- 接入方式: Bot Framework (HTTP, 需要公网 URL) 或通过 Azure Bot Service
- 需要 Azure AD App Registration，获取 App ID 和 App Password
- 参考: [Microsoft Bot Framework 文档](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/)

**接入示例配置**:
```bash
TEAMS_ENABLED=true
TEAMS_APP_ID=your-azure-app-id
TEAMS_APP_PASSWORD=your-azure-app-password
TEAMS_WEBHOOK_PORT=9882
```

---

### 2.5 LINE

**平台简介**: 日本、台湾、东南亚主流即时通讯应用（约 2 亿用户），Messaging API 成熟。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| LN-01 | LINE 适配器基础实现（文字消息收发） | ⭐⭐ 中等 | P1 | 🟡 待认领 |
| LN-02 | 支持图片/文件/语音/视频消息收发 | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| LN-03 | 支持 Flex Message（富文本卡片） | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| LN-04 | 支持 Rich Menu（底部菜单） | ⭐ 简单 | P3 | 🟡 待认领 |

**技术要点**:
- 推荐依赖: `line-bot-sdk` (Python)
- 接入方式: Webhook (HTTP, 需要公网 HTTPS URL)
- 通过 [LINE Developers Console](https://developers.line.biz/) 创建 Messaging API Channel
- 需要 Channel Access Token 和 Channel Secret
- 参考: [LINE Messaging API 文档](https://developers.line.biz/en/docs/messaging-api/)

**接入示例配置**:
```bash
LINE_ENABLED=true
LINE_CHANNEL_ACCESS_TOKEN=your-channel-access-token
LINE_CHANNEL_SECRET=your-channel-secret
LINE_WEBHOOK_PORT=9883
```

---

### 2.6 Signal

**平台简介**: 以隐私和安全著称的开源即时通讯应用，通过 Signal CLI 或 signal-cli-rest-api 接入。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| SG-01 | Signal 适配器基础实现（文字消息收发） | ⭐⭐⭐ 困难 | P2 | 🟡 待认领 |
| SG-02 | 支持图片/文件/语音消息收发 | ⭐⭐ 中等 | P3 | 🟡 待认领 |
| SG-03 | 支持群组消息 | ⭐⭐ 中等 | P3 | 🟡 待认领 |

**技术要点**:
- 接入方式: 通过 [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) (Docker 部署) 提供 REST + WebSocket 接口
- Signal 没有官方 Bot API，需要使用真实手机号注册
- 需要先通过 signal-cli 注册/链接设备
- 参考: [signal-cli-rest-api 文档](https://github.com/bbernhard/signal-cli-rest-api)

**接入示例配置**:
```bash
SIGNAL_ENABLED=true
SIGNAL_API_URL=http://127.0.0.1:8080    # signal-cli-rest-api 地址
SIGNAL_PHONE_NUMBER=+1234567890
```

---

### 2.7 Matrix (Element)

**平台简介**: 开源去中心化通讯协议，Element 是其主要客户端。适合注重隐私和自托管的用户群体。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| MX-01 | Matrix 适配器基础实现（文字消息收发） | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| MX-02 | 支持图片/文件/语音消息收发 | ⭐⭐ 中等 | P3 | 🟡 待认领 |
| MX-03 | 支持 E2EE 端到端加密房间 | ⭐⭐⭐ 困难 | P3 | 🟡 待认领 |

**技术要点**:
- 推荐依赖: `matrix-nio` (支持 E2EE)
- 接入方式: Client-Server API (Long Polling / Sync, 无需公网 IP)
- 需要 Matrix 账号和 Homeserver URL
- 参考: [Matrix Client-Server API](https://spec.matrix.org/latest/client-server-api/)

**接入示例配置**:
```bash
MATRIX_ENABLED=true
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER_ID=@bot:matrix.org
MATRIX_ACCESS_TOKEN=your-access-token
```

---

### 2.8 iMessage (Apple Messages)

**平台简介**: Apple 生态内置的即时通讯服务，覆盖全球 iPhone/iPad/Mac 用户（约 10 亿+ 活跃设备）。iMessage 没有官方 Bot API，需要通过第三方桥接方案接入。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| IM-01 | iMessage 适配器基础实现（文字消息收发，基于 BlueBubbles） | ⭐⭐⭐ 困难 | P1 | 🟡 待认领 |
| IM-02 | 支持图片/文件/语音消息收发 | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| IM-03 | 支持群组消息 (Group Chat) | ⭐⭐ 中等 | P2 | 🟡 待认领 |
| IM-04 | 支持 Tapback 表情回应 | ⭐ 简单 | P3 | 🟡 待认领 |
| IM-05 | 支持 AppleScript 直接接入方案（macOS 原生） | ⭐⭐⭐ 困难 | P3 | 🟡 待认领 |

**技术要点**:
- **方案 A (推荐)**: 通过 [BlueBubbles](https://bluebubbles.app/) Server 接入
  - BlueBubbles 在 macOS 上运行，提供 REST API + WebSocket 接口
  - 支持发送/接收文字、图片、文件、语音、Tapback 等
  - 需要一台 macOS 设备（Mac mini / MacBook）持续运行
  - 推荐依赖: `aiohttp` (调用 BlueBubbles REST API) + `websockets` (实时消息)
- **方案 B**: 通过 macOS AppleScript / Messages.app 数据库
  - 直接在 macOS 上通过 AppleScript 发送消息，监听 `chat.db` 接收消息
  - 优点：无需第三方服务；缺点：仅限 macOS，实现复杂，稳定性依赖系统版本
- **共同限制**:
  - **必须有 macOS 设备**，且登录了 Apple ID 并开启 iMessage
  - Apple 没有官方 Bot API，所有方案均为非官方桥接
  - 不适用于大规模部署，适合个人/小团队使用场景
- 参考: [BlueBubbles API 文档](https://documenter.getpostman.com/view/765844/2s8YsqUajo)

**接入示例配置**:
```bash
IMESSAGE_ENABLED=true
IMESSAGE_BACKEND=bluebubbles             # bluebubbles 或 applescript
BLUEBUBBLES_API_URL=http://192.168.1.x:1234
BLUEBUBBLES_PASSWORD=your-server-password
```

---

### 2.9 Messenger (Facebook)

**平台简介**: Facebook/Meta 旗下即时通讯平台，通过 Messenger Platform API 接入。

| 任务 ID | 任务描述 | 难度 | 优先级 | 状态 |
|---------|---------|------|--------|------|
| FB-01 | Messenger 适配器基础实现（文字消息收发） | ⭐⭐⭐ 困难 | P2 | 🟡 待认领 |
| FB-02 | 支持图片/文件/语音消息收发 | ⭐⭐ 中等 | P3 | 🟡 待认领 |
| FB-03 | 支持 Quick Replies 和 Templates | ⭐⭐ 中等 | P3 | 🟡 待认领 |

**技术要点**:
- 接入方式: Webhook (HTTP, 需要公网 HTTPS URL)
- 需要 Facebook Page + Meta App，配置 Messenger Webhook
- 参考: [Messenger Platform 文档](https://developers.facebook.com/docs/messenger-platform)

**接入示例配置**:
```bash
MESSENGER_ENABLED=true
MESSENGER_PAGE_ACCESS_TOKEN=your-page-access-token
MESSENGER_VERIFY_TOKEN=your-verify-token
MESSENGER_WEBHOOK_PORT=9884
```

---

## 三、任务优先级总览

### P0 — 高优先级（建议优先认领）

| 任务 ID | 平台 | 描述 | 难度 |
|---------|------|------|------|
| DC-01 | Discord | 基础适配器实现 | ⭐⭐ |
| SL-01 | Slack | 基础适配器实现 | ⭐⭐ |
| WA-01 | WhatsApp | 基础适配器实现 | ⭐⭐⭐ |

### P1 — 重要

| 任务 ID | 平台 | 描述 | 难度 |
|---------|------|------|------|
| WW-01 | 企业微信 | 支持接收语音消息 | ⭐⭐ |
| WW-02 | 企业微信 | 支持接收文件/视频消息 | ⭐⭐ |
| DC-02 | Discord | 媒体消息支持 | ⭐⭐ |
| SL-02 | Slack | 媒体消息支持 | ⭐⭐ |
| SL-03 | Slack | Thread 回复 | ⭐⭐ |
| SL-06 | Slack | Socket Mode | ⭐⭐ |
| WA-02 | WhatsApp | 媒体消息支持 | ⭐⭐ |
| WA-05 | WhatsApp | Webhook 安全 | ⭐⭐ |
| MT-01 | Teams | 基础适配器实现 | ⭐⭐⭐ |
| LN-01 | LINE | 基础适配器实现 | ⭐⭐ |
| IM-01 | iMessage | 基础适配器实现 (BlueBubbles) | ⭐⭐⭐ |

### P2 — 常规

| 任务 ID | 平台 | 描述 | 难度 |
|---------|------|------|------|
| WW-03 | 企业微信 | 群聊图片接收 | ⭐⭐ |
| WW-04 | 企业微信 | 自建应用接入方式 | ⭐⭐⭐ |
| WW-05 | 企业微信 | 文件发送 | ⭐⭐ |
| DD-01 | 钉钉 | 文件发送优化 | ⭐⭐ |
| QQ-01 | QQ 官方 | 本地文件上传 | ⭐⭐ |
| QQ-02 | QQ 官方 | 语音发送优化 | ⭐⭐ |
| DC-03 | Discord | Slash Commands | ⭐⭐ |
| DC-04 | Discord | Thread 消息 | ⭐⭐ |
| SL-04 | Slack | Block Kit 消息 | ⭐⭐ |
| SL-05 | Slack | Slash Commands | ⭐⭐ |
| WA-03 | WhatsApp | 消息模板 | ⭐⭐ |
| WA-04 | WhatsApp | 互动式消息 | ⭐⭐ |
| MT-02 | Teams | 媒体消息 | ⭐⭐ |
| MT-03 | Teams | Adaptive Cards | ⭐⭐ |
| MT-04 | Teams | Channel/Group Chat | ⭐⭐ |
| LN-02 | LINE | 媒体消息 | ⭐⭐ |
| LN-03 | LINE | Flex Message | ⭐⭐ |
| IM-02 | iMessage | 媒体消息支持 | ⭐⭐ |
| IM-03 | iMessage | 群组消息 | ⭐⭐ |
| SG-01 | Signal | 基础适配器实现 | ⭐⭐⭐ |
| MX-01 | Matrix | 基础适配器实现 | ⭐⭐ |
| GEN-01 | 通用 | 健康检查机制 | ⭐⭐ |
| GEN-02 | 通用 | 速率限制框架 | ⭐⭐⭐ |
| GEN-03 | 通用 | 测试覆盖率提升 | ⭐⭐ |

## 四、新适配器开发指南

### 4.1 开发步骤

1. **创建适配器文件**: 在 `src/openakita/channels/adapters/` 下新建 `<platform>.py`
2. **继承 ChannelAdapter**: 实现所有抽象方法
3. **添加配置项**: 在 `src/openakita/config.py` 中添加平台配置字段
4. **注册适配器**: 在 `src/openakita/main.py` 的 `_create_bot_adapter()` 和 `start_im_channels()` 中添加创建/启动逻辑
5. **添加依赖**: 在 `pyproject.toml` 中添加可选依赖组
6. **导出适配器**: 在 `src/openakita/channels/adapters/__init__.py` 中导出
7. **编写测试**: 在 `tests/` 下添加单元测试和集成测试
8. **编写文档**: 更新 `docs/im-channels.md`，添加平台配置说明

### 4.2 适配器模板

```python
"""
<Platform> 通道适配器
"""

import logging
from pathlib import Path

from ..base import ChannelAdapter
from ..types import MediaFile, OutgoingMessage, UnifiedMessage

logger = logging.getLogger(__name__)


class PlatformAdapter(ChannelAdapter):
    """<Platform> 适配器"""

    channel_name = "platform"

    def __init__(self, *, bot_token: str, **kwargs):
        super().__init__(**kwargs)
        self._bot_token = bot_token
        # 初始化平台 SDK 客户端

    async def start(self) -> None:
        """启动适配器，建立与平台的连接"""
        self._running = True
        # 启动 WebSocket / Webhook / Long Polling
        logger.info(f"{self.channel_name} adapter started")

    async def stop(self) -> None:
        """停止适配器，清理资源"""
        self._running = False
        # 关闭连接、清理资源
        logger.info(f"{self.channel_name} adapter stopped")

    async def send_message(self, message: OutgoingMessage) -> str:
        """发送消息到平台"""
        # 根据 message.content 类型调用平台 API
        # 返回平台侧的消息 ID
        raise NotImplementedError

    async def download_media(self, media: MediaFile) -> Path:
        """从平台下载媒体文件"""
        # 使用平台 API 下载文件到本地
        raise NotImplementedError

    async def upload_media(self, path: Path, mime_type: str) -> MediaFile:
        """上传文件到平台"""
        # 使用平台 API 上传文件
        raise NotImplementedError

    # ---------- 可选方法 ----------

    async def send_typing(self, chat_id: str) -> None:
        """发送正在输入状态"""
        pass

    async def get_user_info(self, user_id: str) -> dict | None:
        """获取用户信息"""
        return None
```

### 4.3 PR 提交规范

- 分支命名: `feat/im-<platform>` (如 `feat/im-discord`)
- Commit 格式: `feat(channels): add <platform> adapter`
- PR 标题: `feat(channels): add <Platform> IM adapter`
- PR 中需包含:
  - 适配器实现代码
  - 配置项说明 (环境变量)
  - 基础单元测试
  - `docs/im-channels.md` 文档更新
  - `pyproject.toml` 依赖更新
  - `.env.example` 配置示例更新

### 4.4 好的参考实现

- **Telegram 适配器** (`telegram.py`): 功能最完整，媒体类型支持最全面，推荐作为新适配器的主要参考
- **飞书适配器** (`feishu.py`): WebSocket 长连接模式的参考
- **OneBot 适配器** (`onebot.py`): 通用协议适配器的参考

---

## 五、如何认领任务

1. 在 [GitHub Issues](https://github.com/openakita/openakita/issues) 中找到对应任务的 Issue（标签: `im-channel`）
2. 留言表示认领意向，说明预计完成时间
3. 维护者确认后会将 Issue assign 给你
4. Fork 仓库，按照 [CONTRIBUTING.md](../CONTRIBUTING.md) 指南开发
5. 提交 PR，等待 Review

### 认领建议

| 经验水平 | 推荐任务 |
|---------|---------|
| **新手** (首次贡献) | DC-05, DC-06, QQ-03, LN-04 — 简单功能增强 |
| **中级** (有 IM Bot 开发经验) | DC-01, SL-01, LN-01, MX-01 — 新平台基础接入 |
| **高级** (熟悉复杂 API) | WA-01, MT-01, SG-01, WW-04 — 复杂平台接入或架构重构 |

---

## 六、接入方式对比

| 平台 | 接入方式 | 需要公网 IP | 免费层 | Bot API 成熟度 |
|------|---------|------------|--------|---------------|
| Discord | WebSocket Gateway | ❌ | ✅ 完全免费 | ⭐⭐⭐⭐⭐ |
| Slack | Socket Mode / Events API | ❌ (Socket Mode) | ✅ 免费版可用 | ⭐⭐⭐⭐⭐ |
| WhatsApp | Cloud API + Webhook | ⚠️ 需要 | ⚠️ 1000条免费/月 | ⭐⭐⭐⭐ |
| Teams | Bot Framework | ⚠️ 需要 | ✅ 需 Azure 账户 | ⭐⭐⭐⭐ |
| LINE | Webhook | ⚠️ 需要 | ✅ 免费版有限制 | ⭐⭐⭐⭐ |
| Signal | signal-cli REST API | ❌ (本地部署) | ✅ 完全免费 | ⭐⭐ (非官方) |
| Matrix | Client-Server API | ❌ | ✅ 完全免费 | ⭐⭐⭐⭐ |
| Messenger | Webhook | ⚠️ 需要 | ✅ 免费版有限制 | ⭐⭐⭐⭐ |
| iMessage | BlueBubbles API / AppleScript | ❌ (本地 macOS) | ✅ 免费 (需 Mac 设备) | ⭐⭐ (非官方) |

---

*本文档持续更新。如有问题或建议，请在 [GitHub Discussions](https://github.com/openakita/openakita/discussions) 中讨论。*
