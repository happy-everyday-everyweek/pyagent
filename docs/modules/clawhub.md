# ClawHub Skill安装协议文档 v0.8.0

本文档详细描述PyAgent v0.8.0 ClawHub Skill安装协议的设计和实现�?
## 概述

ClawHub是一个便捷的Skill技能发现和安装协议，支持通过URL快速安装Skill技能到PyAgent�?
## 支持的URL格式

```
clawhub://skill-name
https://clawhub.io/skills/skill-name
https://registry.clawhub.io/skills/skill-name
```

## 核心组件

### ClawHubSkillInfo

技能信息数据类�?
```python
@dataclass
class ClawHubSkillInfo:
    name: str                    # 技能名�?    description: str             # 技能描�?    version: str                 # 版本�?    author: str                  # 作�?    repository: str | None       # 代码仓库
    homepage: str | None         # 主页
    skill_md_url: str | None     # SKILL.md下载地址
    scripts: dict | None         # 脚本文件
    references: list | None      # 参考文�?    tags: list | None            # 标签
    license: str | None          # 许可�?```

### ClawHubInstaller

Skill安装器：

```python
class ClawHubInstaller:
    def parse_clawhub_url(self, url: str) -> str | None:
        """解析ClawHub URL获取技能名�?""
        
    async def fetch_skill_info(self, skill_name: str) -> ClawHubSkillInfo | None:
        """从注册表获取技能信�?""
        
    async def install_from_clawhub(self, url: str) -> ClawHubInstallResult:
        """从ClawHub安装技�?""
        
    async def search_skills(self, query: str, limit: int = 10) -> list[ClawHubSkillInfo]:
        """搜索技�?""
        
    async def list_popular_skills(self, limit: int = 20) -> list[ClawHubSkillInfo]:
        """获取热门技能列�?""
        
    async def uninstall_skill(self, skill_name: str) -> bool:
        """卸载技�?""
```

## 使用示例

### 安装技�?
```python
from src.skills.clawhub import install_from_clawhub

# 使用URL安装
result = await install_from_clawhub("clawhub://weather-skill")

if result.success:
    print(f"安装成功: {result.skill_name}")
    print(f"安装路径: {result.skill_path}")
else:
    print(f"安装失败: {result.error}")
```

### 搜索技�?
```python
from src.skills.clawhub import get_clawhub_installer

installer = get_clawhub_installer()

# 搜索技�?results = await installer.search_skills("weather", limit=5)
for skill in results:
    print(f"{skill.name}: {skill.description}")
```

### 获取热门技�?
```python
# 获取热门技�?popular = await installer.list_popular_skills(limit=10)
for skill in popular:
    print(f"{skill.name} by {skill.author}")
```

### 卸载技�?
```python
# 卸载技�?success = await installer.uninstall_skill("weather-skill")
if success:
    print("卸载成功")
```

## 安装流程

```
解析URL �?获取技能信�?�?创建目录 �?下载SKILL.md
                                              �?下载参考文�?�?下载脚本文件 �?生成SKILL.md（如需要）
```

### 目录结构

安装后的技能目录结构：

```
skills/
└── skill-name/
    ├── SKILL.md              # 技能定义文�?    ├── scripts/              # 脚本文件（可选）
    �?  ├── script1.py
    �?  └── script2.js
    └── references/           # 参考文件（可选）
        └── reference.txt
```

## API接口

### 安装技�?
```http
POST /api/skills/install
Content-Type: application/json

{
  "url": "clawhub://skill-name"
}
```

**响应**:
```json
{
  "success": true,
  "skill_name": "skill-name",
  "skill_path": "skills/skill-name",
  "skill_info": {
    "name": "skill-name",
    "description": "技能描�?,
    "version": "1.0.0",
    "author": "author-name"
  }
}
```

### 搜索技�?
```http
GET /api/skills/search?q=weather&limit=10
```

**响应**:
```json
{
  "results": [
    {
      "name": "weather-skill",
      "description": "天气查询技�?,
      "version": "1.0.0",
      "author": "weather-team"
    }
  ]
}
```

### 获取热门技�?
```http
GET /api/skills/popular?limit=20
```

### 卸载技�?
```http
DELETE /api/skills/{skill_name}
```

## 配置文件

### 注册表地址

```python
CLAWHUB_REGISTRY_URL = "https://registry.clawhub.io"
CLAWHUB_API_URL = "https://api.clawhub.io"
```

### 环境变量

```env
CLAWHUB_REGISTRY_URL=https://registry.clawhub.io
CLAWHUB_API_URL=https://api.clawhub.io
```

## SKILL.md格式

ClawHub使用标准的SKILL.md格式�?
```markdown
---
name: skill-name
description: 技能描�?version: "1.0.0"
author: author-name
license: MIT
tags: ["weather", "utility"]
---

# 技能名�?
技能详细描�?..

## 使用示例

示例代码...
```

## 故障排除

### 技能未找到

**现象**: 安装时提�?04错误

**解决**:
1. 检查技能名称是否正�?2. 确认技能已发布到ClawHub
3. 检查网络连�?
### 下载失败

**现象**: 无法下载SKILL.md或脚�?
**解决**:
1. 检查网络连�?2. 确认skill_md_url配置正确
3. 查看日志获取详细错误信息

### 权限不足

**现象**: 无法创建技能目�?
**解决**:
1. 检查skills目录权限
2. 确保运行用户有写入权�?
## 最佳实�?
1. **验证URL**: 安装前验证ClawHub URL格式
2. **查看信息**: 安装前查看技能信息和评价
3. **定期更新**: 关注技能更新，及时升级
4. **备份重要技�?*: 重要技能建议备份SKILL.md
