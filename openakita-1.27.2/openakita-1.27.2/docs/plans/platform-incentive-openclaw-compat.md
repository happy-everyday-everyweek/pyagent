# OpenAkita Platform — 激励机制 + OpenClaw 兼容方案

> 版本: 2.0 | 日期: 2026-02-28
> 状态: **APPROVED**

---

## 一、调研结论

### 1.1 OpenClaw / ClawHub 生态现状

| 指标 | 数据 |
|---|---|
| GitHub Stars | 180,000+ |
| ClawHub 技能数 | 3,286 ~ 5,700+ (安全清理后约 3,200) |
| 日新增技能 | 40-60 |
| 累计下载量 | 1,500,000+ |
| 技术栈 | TanStack Start (React) + Convex + OpenAI Embeddings + GitHub OAuth |
| 安全事件 | 2026.02 "ClawHavoc" — 341 恶意技能，已引入 VirusTotal 自动扫描 |

### 1.2 ClawHub Skill 格式

ClawHub 技能与 OpenAkita 都使用 **SKILL.md + YAML frontmatter**，核心格式高度兼容：

```yaml
# ClawHub 格式
---
name: my-skill
description: What it does. Use when [trigger].
metadata: {"openclaw":{"emoji":"🔧","requires":{"bins":["uv"]},"os":["linux","darwin","win32"]}}
---
（Markdown 正文 = AI 指令）
```

```yaml
# OpenAkita 格式
---
name: my-skill
description: What it does
version: "1.0.0"
system: false
handler: my_handler
tool-name: my_tool
category: Productivity
---
（Markdown 正文 = AI 指令）
```

**关键差异对照表：**

| 特性 | OpenAkita | ClawHub |
|---|---|---|
| 文件名 | `SKILL.md` | `SKILL.md` |
| 必填字段 | `name`, `description` | `name`, `description` |
| 工具映射 | `handler` + `tool-name` | 无（纯自然语言指令） |
| 环境要求 | `metadata.openakita.os` | `metadata.openclaw.requires` |
| 版本号 | `version` 字段 | 无（通过 git tag 管理） |
| 发布 | 平台 API | `clawhub publish` CLI |
| 安装 | 平台 API / git clone | `clawhub install` CLI |

**结论：格式本身高度兼容。ClawHub 技能的 SKILL.md 可直接被 OpenAkita 解析加载（忽略 metadata.openclaw 即可），反之亦然。唯一需要适配的是 `handler`/`tool-name` 映射（纯指令型技能不需要）。**

### 1.3 EvoMap 参考

EvoMap 使用邀请码制注册，通过微信公众号/社区群/GitHub Issue 分发。注册后获得 3 个邀请码。核心模式：邀请码制造稀缺感，社区渠道保证不真正阻断——真正的门槛是"加入社区"。

---

## 二、产品审计 — 砍掉/替换项 (v2.0)

### 2.1 替换口号

**砍掉**: "一个AI学会，百万AI继承"（EvoMap 基因模型口号，与我们模型不匹配）

**替换为**:
- 英文: "Share Agents, Not Just Skills"
- 中文: "分享智能体，不只是技能"
- 副标语: "Build your AI team. Share it with the world."

### 2.2 砍掉平台实时数据展示

前期不展示具体数字。阈值触发策略：
- 用户数 > 500 → 展示 "500+ developers"
- Skill 数 > 100 → 展示 "100+ skills"
- 阈值前用定性描述: "Growing community" / "Early access"

### 2.3 砍掉每日签到

**替换为活动型奖励**:
- 本月首次发布内容: +20 AP
- 连续 4 周有活跃: +50 AP (月度活跃奖)
- 首次评价他人作品: +10 AP

### 2.4 砍掉其他

- 硬件指纹 device_id → 随机 UUID
- API Key 单向 hash → AES 加密可查看
- T0 每月 10 次下载限制 → 所有等级无限下载
- Rate Limit 按 req/h → 按业务操作频率
- 海报实时注册计数 → 静态内容

---

## 三、激励机制设计

### 3.1 核心理念

**"贡献越多，获得越多"** — 不是付费墙，而是贡献阶梯。
免费下载吸引流量 → 发布限制激励贡献 → 贡献越多权限越大。

### 3.2 用户等级体系 (Tiers)

| 等级 | 名称 | 条件 | 权限 |
|---|---|---|---|
| T0 | **Explorer** | 注册即可 | 无限下载，可发布 1 个 Skill |
| T1 | **Contributor** | 发布 1+ 且通过审核 | 可发布 5 个，提交 Agent |
| T2 | **Builder** | 发布 3+ 且均分 >= 3.5 | 无限发布，"Builder" 徽章 |
| T3 | **Champion** | 发布 10+ 或邀请 20+ 活跃 | 审核权，推荐位 |

等级只升不降。

### 3.3 积分系统 (Akita Points / AP)

**获取 AP：**

| 行为 | AP |
|---|---|
| 注册账号 | +100 |
| 发布 Skill | +50 |
| 发布 Agent | +100 |
| 你发布的内容被下载（每次） | +1 |
| 你发布的内容获得好评（≥4星） | +10 |
| 提交有效 Bug Report | +20 |
| 邀请用户注册（被邀请人激活后） | +30 |
| 邀请用户成为 Contributor（被邀请人发布内容后） | +50 |
| 本月首次发布内容 | +20 |
| 连续 4 周有活跃 | +50 |
| 首次评价他人作品 | +10 |
| 绑定 OpenClaw 账号 | +50（一次性） |
| 从 OpenClaw 迁移 Skill 到平台 | +30/个 |
| 为 Skill 添加双兼容支持 | +20/个 |

**消费 AP：**

| 行为 | AP |
|---|---|
| 申请 Skill 加精/推荐 | -100 |
| 申请 "Certified" 认证审核 | -200 |
| 自定义个人主页 | -50 |
| 兑换 Agent 打包模板 | -30 |

### 3.4 邀请体系

```
用户 A 生成邀请码 → 用户 B 使用邀请码注册
  ├─ B 注册成功 → A 获得 +30 AP
  ├─ B 发布第一个 Skill → A 获得 +50 AP，B 获得 +20 AP
  └─ B 成为 Builder → A 获得 +100 AP
```

**邀请码规则：**
- 注册后获得 3 个邀请码
- 升级 Builder 后增加到 10 个
- Champion 无限邀请码
- 支持邀请链接：`https://openakita.ai/invite/{code}`
- 支持活动批量邀请码（用于社区推广）

**获取邀请码渠道：**
- Discord 社区
- GitHub Discussions
- 微信群
- 微信公众号

### 3.5 反作弊机制

| 风险 | 对策 |
|---|---|
| 批量注册刷积分 | GitHub OAuth 强制绑定 + 邮箱验证 + 同一 IP 24h 限 3 次注册 |
| 发布垃圾 Skill 刷等级 | 发布后 48h 审核窗口，被举报 3 次自动下架；仅通过 Review Bot 的发布计入等级 |
| 自己下载自己的 Skill | 同一账号下载自己的内容不计 AP |
| 多设备刷下载 | 同一 device_id 对同一 Skill 仅计 1 次下载 |
| 刷评分 | 只有实际下载安装后才能评分 |

### 3.6 Rate Limiting 按业务操作

| 操作 | 匿名 | T0+ |
|---|---|---|
| 浏览/搜索 | 不限 | 不限 |
| 下载 | 不限 | 不限 |
| 发布 | 禁止 | 按等级 |
| 评价 | 禁止 | 3 次/天 |
| API 调用（自动化） | 30/h | 300/h |

---

## 四、认证与设备绑定

### 4.1 邀请制注册

所有人都需要邀请码，OpenClaw 用户也不例外。
活动码 `CLAWTOACKIT`（限量 500，限时 30 天，额外 +50 AP）通过 OpenClaw 社区定向投放。

注册页面设计：邀请码字段放最顶部 → GitHub OAuth → 邮箱注册 → "没有邀请码？加入社区获取"引导。

### 4.2 设备标识 (Device Identity)

首次运行时生成随机 UUID 并持久化到 `data/device.json`：

```python
import uuid, json
from pathlib import Path

def get_or_create_device_id(data_dir: Path) -> str:
    fp = data_dir / "device.json"
    if fp.exists():
        return json.loads(fp.read_text())["device_id"]
    did = uuid.uuid4().hex[:16]
    fp.write_text(json.dumps({"device_id": did}))
    return did
```

### 4.3 桌面端 OAuth — Device Authorization Flow

```
用户在 Setup Center 点击 "登录"
  → 桌面端调用 POST /api/auth/device/code
  → 平台返回 { user_code, verification_uri, device_code, interval }
  → 桌面端显示代码并自动打开系统浏览器
  → 桌面端轮询 POST /api/auth/device/token
  → 授权完成后保存 token，显示已登录状态
```

### 4.4 API Key 体系

```
Account (1) ──── has ──── API Key (1)
    │                        │
    ├── has many ── Devices (N)
    ├── has ────── Tier (T0-T3)
    ├── has ────── AP Balance
    └── has ────── Invite Codes (N)
```

- 格式：`ak_live_<32位随机字符>` / `ak_test_<32位随机字符>`
- AES 加密存储，仪表盘密码确认后可查看
- 请求签名：`X-Akita-Key`, `X-Akita-Device`
- 绑定最多 5 台设备

### 4.5 先锋编号

- 先锋编号**仅对自己可见**（仪表盘、成就卡）
- 公开展示为**段位**: "Early Pioneer" (前 100)、"Pioneer" (前 1000)、"Member" (1000+)

---

## 五、网站规则说明页面

路径: `/rules`，面向所有用户（含未登录访客），清晰展示：

1. **等级体系** — T0-T3 表格 + 进度条可视化
2. **积分规则** — AP 获取/消费一览表
3. **邀请机制** — 流程图 + 获取渠道（Discord/GitHub/微信群/公众号）
4. **审核规则** — Review Bot 检查项 + 审核周期
5. **行为准则** — 反作弊 + DMCA + 内容规范
6. **FAQ** — 常见问题

导航栏 Navbar 新增 "Rules" 链接。

---

## 六、桌面端图片导出

Setup Center 支持生成和导出邀请海报、成就卡片。

技术方案：
- `html-to-image` npm 依赖
- Tauri: `@tauri-apps/plugin-dialog` save 对话框
- Web 模式: `<a download>` 降级

**邀请海报**: Logo + 口号 + 用户头像/名字/段位 + QR 码 + 邀请链接
**成就卡片**: 头像 + Pioneer 编号 + 段位 + 贡献统计 + 品牌

入口: 高级设置 > 平台账号区域（需登录）。

---

## 七、海报与分享机制

### 7.1 Web 端邀请海报

用户在「邀请中心」页面 Canvas 生成海报 PNG，保存后手动分享。
不含平台统计数据、实时注册数、具体先锋编号。

### 7.2 OG 社交卡片

链接分享 `openakita.ai/invite/{code}` 自动展示 Open Graph 预览图。

### 7.3 注册页移动端适配

确保移动端浏览器完美显示。

---

## 八、Review Bot

| 检查项 | 说明 | 严重级 |
|---|---|---|
| YAML frontmatter 格式 | 必填字段 name/description | Error |
| Markdown 正文非空 | 至少有操作指令 | Error |
| 链接有效性 | URL 是否 404 | Warning |
| 敏感词过滤 | 脏话、广告 | Error |
| 许可证合规 | SPDX 标识符 | Warning |
| Agent 包结构 | .akita-agent ZIP spec v1.1 | Error |
| 重复检测 | name/description 相似度 | Warning |

不做：代码执行安全扫描、深度依赖分析。

---

## 九、OpenClaw 兼容 (V1 简化)

### 9.1 V1 范围

**保留**: 兼容性标志字段 + 发布时自动检测 + 迁移文档 + 活动码投放
**砍掉**: ClawHub 搜索代理、双向适配器、迁移向导（V2 再做）

### 9.2 格式兼容策略

- parser 忽略不认识的 frontmatter 字段
- `handler` + `tool-name` 仅 OpenAkita 原生工具需要
- 纯指令型 Skill 天然双兼容

### 9.3 兼容性标志

| 标志 | 含义 |
|---|---|
| `akita-native` | 仅 OpenAkita 可用 |
| `openclaw-native` | 仅 OpenClaw 可用 |
| `dual-compatible` | 双平台可用 |

自动检测规则：
- 有 `handler` + `tool-name` → akita-native
- 有 `metadata.openclaw` → openclaw-native
- 纯指令型 → dual-compatible
- 同时有两者 → dual-compatible

---

## 十、补充功能

### 10.1 公开用户主页

路径: `/u/{username}`，展示头像、段位、发布列表、成就徽章、GitHub 链接。

### 10.2 更新通知

- API: `POST /api/updates/check` (body: `[{id, version}, ...]`)
- 桌面端启动时检查，顶部显示 "N 个更新可用"

### 10.3 内容举报

- Agent/Skill 详情页 "Report" 按钮
- 举报类型: 侵权、恶意、垃圾、不当内容
- 被举报 3 次自动下架待审

---

## 十一、数据库 Schema 扩展

### 11.1 用户表扩展

```sql
ALTER TABLE users ADD COLUMN tier VARCHAR(20) DEFAULT 'explorer';
ALTER TABLE users ADD COLUMN ap_balance INTEGER DEFAULT 100;
ALTER TABLE users ADD COLUMN total_ap_earned INTEGER DEFAULT 100;
ALTER TABLE users ADD COLUMN api_key_encrypted TEXT;
ALTER TABLE users ADD COLUMN pioneer_number SERIAL;
ALTER TABLE users ADD COLUMN invited_by_user_id UUID REFERENCES users(id);
ALTER TABLE users ADD COLUMN openclaw_github_username VARCHAR(100);
ALTER TABLE users ADD COLUMN publish_count INTEGER DEFAULT 0;
```

### 11.2 设备表

```sql
CREATE TABLE devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  device_id VARCHAR(32) NOT NULL,
  device_name VARCHAR(100),
  platform VARCHAR(20),
  first_seen_at TIMESTAMP DEFAULT NOW(),
  last_seen_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE,
  UNIQUE(user_id, device_id)
);
```

### 11.3 积分流水表

```sql
CREATE TABLE ap_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) NOT NULL,
  amount INTEGER NOT NULL,
  action VARCHAR(50) NOT NULL,
  reference_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 11.4 邀请码表

```sql
CREATE TABLE invite_codes (
  code VARCHAR(16) PRIMARY KEY,
  owner_user_id UUID REFERENCES users(id) NOT NULL,
  used_by_user_id UUID REFERENCES users(id),
  campaign VARCHAR(50),
  bonus_ap INTEGER DEFAULT 0,
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 11.5 Skill/Agent 兼容性扩展

```sql
ALTER TABLE skills ADD COLUMN compatibility VARCHAR(30) DEFAULT 'akita-native';
ALTER TABLE skills ADD COLUMN clawhub_id VARCHAR(100);
ALTER TABLE skills ADD COLUMN openclaw_metadata JSONB;
ALTER TABLE agents ADD COLUMN compatibility VARCHAR(30) DEFAULT 'akita-native';
```

### 11.6 内容举报表

```sql
CREATE TABLE content_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_user_id UUID REFERENCES users(id),
  target_type VARCHAR(20) NOT NULL,
  target_id VARCHAR(100) NOT NULL,
  reason VARCHAR(50) NOT NULL,
  description TEXT,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 十二、API 设计

### 12.1 认证 API

```
POST   /api/auth/register          邀请码 + GitHub OAuth / 邮箱注册
POST   /api/auth/login             登录
POST   /api/auth/device/code       Device Auth Flow — 获取验证码
POST   /api/auth/device/token      Device Auth Flow — 轮询令牌
POST   /api/auth/device/bind       绑定设备
GET    /api/auth/me                当前用户信息
POST   /api/auth/apikey/regenerate 重新生成 API Key
GET    /api/auth/apikey             查看 API Key (需密码确认)
```

### 12.2 积分 API

```
GET    /api/credits/balance        AP 余额
GET    /api/credits/history        AP 流水（分页）
```

### 12.3 邀请 API

```
GET    /api/invite/codes           我的邀请码列表
POST   /api/invite/generate        生成新邀请码
GET    /api/invite/stats           邀请统计
```

### 12.4 兼容性 API

```
GET    /api/skills?compatibility=dual   按兼容性筛选
```

### 12.5 更新检查 API

```
POST   /api/updates/check          检查已安装内容是否有更新
```

### 12.6 举报 API

```
POST   /api/reports                提交举报
GET    /api/reports                管理员查看举报（分页）
```

---

## 十三、本地客户端改造

### 13.1 config.py

```python
HUB_API_KEY: str = ""
HUB_DEVICE_ID: str = ""
```

### 13.2 Hub Client 认证

请求头添加 `X-Akita-Key` 和 `X-Akita-Device`。未登录时仍可正常使用本地功能。

### 13.3 Setup Center UI

- 高级设置: 平台登录(Device Auth Flow) + 设备管理 + 邀请码管理 + 海报/成就卡导出
- Agent/Skill Store: 登录状态栏 + 兼容性筛选 + 更新通知

---

## 十四、平台前端改造

### 14.1 新增页面

| 页面 | 路径 | 说明 |
|---|---|---|
| 规则说明 | `/rules` | 等级/积分/邀请/审核规则 |
| 用户仪表盘 | `/dashboard` | 等级、AP、统计、API Key |
| 排行榜 | `/leaderboard` | AP / 下载量 / 发布数排名 |
| 邀请中心 | `/invite` | 邀请码管理、海报生成 |
| 公开主页 | `/u/{username}` | 用户公开资料 |
| 邀请落地页 | `/invite/{code}` | 邀请链接落地 |

### 14.2 页面改造

- 注册页: 邀请码 + GitHub OAuth + 社区引导
- Navbar: 登录状态 + Rules 链接
- Store 卡片: 兼容性图标
- 首页: 口号替换 + 去掉实时数据

---

## 十五、实施阶段

### Phase 1 — metadata.openakita 规范 + 本地解析 (3 天)

### Phase 2 — 认证 + 邀请制注册 (1 周)
- 注册页改造、邀请码表、Device Auth Flow、设备标识、API Key、本地客户端集成

### Phase 3 — 等级 + 积分 + 规则页面 (1 周)
- 用户表扩展、AP 事务、等级计算、仪表盘、公开主页、/rules 页面

### Phase 4 — 情绪价值 + 传播 + 图片导出 (4 天)
- 先锋段位、邀请海报 (Web + 桌面端)、OG 卡片、成就徽章、成就卡导出

### Phase 5 — Review Bot + 内容治理 (3 天)
- 7 项自动检查、内容举报、更新通知 API

### Phase 6 — OpenClaw 兼容 V1 (3 天)
- 兼容性标志 + 自动检测、迁移文档、活动码投放

---

## 十六、安全考量

1. **API Key AES 加密存储** — 仪表盘密码确认后可查看
2. **Rate Limiting** — 按业务操作频率限制
3. **Review Bot** — 发布前自动检查（7 项）
4. **DMCA 流程** — zacon365@gmail.com
5. **匿名降级** — 不登录依然可用（无限下载），仅发布/评价受限
6. **设备标识** — 随机 UUID，无隐私风险
