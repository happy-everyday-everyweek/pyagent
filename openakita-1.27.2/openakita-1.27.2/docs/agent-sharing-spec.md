# Open Agent Sharing Specification v1.0

## 概述

本规范定义了 OpenAkita Agent 包（`.akita-agent`）的格式标准，用于在用户之间共享完整的 AI Agent 配置，包括提示词、技能和元数据。

## 包格式

`.akita-agent` 文件是标准 ZIP 压缩包，扩展名为 `.akita-agent`。

### 目录结构

```
{agent-id}.akita-agent (ZIP)
├── manifest.json          # 必需 — 包元数据
├── profile.json           # 必需 — Agent 配置
├── README.md              # 可选 — 使用说明
├── icon.png               # 可选 — 图标（<=256KB, PNG/SVG）
└── skills/                # 可选 — 捆绑技能
    ├── skill-a/
    │   └── SKILL.md
    └── skill-b/
        └── SKILL.md
```

## manifest.json

包元数据文件，所有字段说明如下：

```json
{
  "spec_version": "1.0",
  "id": "customer-service-agent",
  "name": "客服专员",
  "name_i18n": {
    "zh": "客服专员",
    "en": "Customer Service Agent"
  },
  "description": "专业客服 Agent，擅长处理客户咨询和投诉",
  "description_i18n": {
    "zh": "专业客服 Agent，擅长处理客户咨询和投诉",
    "en": "Professional customer service agent"
  },
  "version": "1.0.0",
  "author": {
    "name": "张三",
    "url": "https://github.com/zhangsan"
  },
  "category": "enterprise",
  "tags": ["客服", "对话", "enterprise"],
  "license": "MIT",
  "min_platform_version": "1.25.0",
  "bundled_skills": ["skill-a", "skill-b"],
  "required_builtin_skills": ["web_search"],
  "created_at": "2026-02-28T10:00:00Z",
  "checksum": "sha256:abc123..."
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `spec_version` | string | 是 | 规范版本号，当前为 `"1.0"` |
| `id` | string | 是 | Agent 唯一标识符，slug 格式（小写字母、数字、连字符） |
| `name` | string | 是 | Agent 显示名称 |
| `name_i18n` | object | 否 | 多语言名称，key 为语言代码 |
| `description` | string | 是 | Agent 描述 |
| `description_i18n` | object | 否 | 多语言描述 |
| `version` | string | 是 | 语义化版本号（SemVer） |
| `author` | object | 是 | 作者信息 |
| `author.name` | string | 是 | 作者名称 |
| `author.url` | string | 否 | 作者主页 URL |
| `category` | string | 否 | 分类 ID |
| `tags` | string[] | 否 | 标签数组 |
| `license` | string | 否 | 许可证标识符，默认 `"MIT"` |
| `min_platform_version` | string | 否 | 要求的最低 OpenAkita 版本 |
| `bundled_skills` | string[] | 否 | 包内捆绑的技能目录名列表 |
| `required_builtin_skills` | string[] | 否 | 依赖的内置技能名称列表 |
| `created_at` | string | 是 | ISO 8601 创建时间 |
| `checksum` | string | 否 | 包内容校验和（`sha256:` 前缀） |

### ID 格式约束

- 长度 3-64 字符
- 仅允许 `[a-z0-9-]`
- 不能以连字符开头或结尾
- 不能包含连续连字符

## profile.json

Agent 运行时配置，与 OpenAkita 的 `AgentProfile` 数据结构对应：

```json
{
  "id": "customer-service-agent",
  "name": "客服专员",
  "description": "专业客服 Agent",
  "type": "custom",
  "skills": ["web_search", "skill-a"],
  "skills_mode": "inclusive",
  "custom_prompt": "你是一位专业的客服代表...",
  "icon": "💬",
  "color": "#4A90D9",
  "category": "enterprise",
  "name_i18n": {},
  "description_i18n": {}
}
```

### 导入行为

- `id`：如果本地已存在同 ID 的 Profile，将自动追加后缀（如 `-1`）
- `type`：导入后始终为 `custom`
- `skills`：捆绑技能会被安装到本地技能目录后自动添加
- `skills_mode`：保持原值

## skills/ 目录

捆绑技能遵循标准的 OpenAkita Skill 格式。每个子目录代表一个技能，必须包含 `SKILL.md` 文件。

### SKILL.md 格式

```markdown
---
name: skill-name
description: 技能描述
version: 1.0.0
author: 张三
tags: [tag1, tag2]
tools:
  - name: tool_name
    description: 工具描述
---

# 技能名称

技能详细说明和使用方法...
```

## icon.png

- 格式：PNG 或 SVG
- 最大大小：256KB
- 推荐尺寸：256x256 像素
- 如未提供，使用 `profile.json` 中的 `icon` 字段（emoji）

## 安全约束

1. 包内不允许包含可执行文件（`.exe`, `.bat`, `.sh`, `.py` 等）
2. 包最大总大小：50MB
3. 单个文件最大：10MB
4. 不允许符号链接
5. 所有文件路径必须在包根目录内（防止路径遍历）
6. `profile.json` 中的 `type` 字段导入时强制设为 `custom`

## 校验流程

导入 `.akita-agent` 包时，应按以下顺序校验：

1. 验证 ZIP 格式有效
2. 验证 `manifest.json` 存在且格式正确
3. 验证 `profile.json` 存在且格式正确
4. 验证 `spec_version` 兼容性
5. 如有 `min_platform_version`，检查当前平台版本是否满足
6. 如有 `checksum`，验证包完整性
7. 扫描安全约束（文件类型、大小、路径）
8. 验证 `bundled_skills` 中列出的技能目录都存在且含有效 `SKILL.md`

## 版本兼容

- `spec_version: "1.0"` 包可被所有支持 v1.x 的平台导入
- 主版本号变更表示不向后兼容的格式变更
- 次版本号变更保持向后兼容

## MIME Type

```
application/x-akita-agent
```

文件扩展名：`.akita-agent`
