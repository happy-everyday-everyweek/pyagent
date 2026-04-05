# PyAgent 邮件客户端

**版本**: v0.8.0  
**模块路径**: `src/email/`  
**最后更新**: 2025-04-03

---

## 概述

邮件客户端是 PyAgent v0.8.0 引入的全新模块，提供完整的 SMTP/IMAP 邮件收发功能。支持发送纯文本和 HTML 邮件、附件上传、邮件搜索、文件夹管理等标准邮件操作。

### 核心特性

- **SMTP 发送**: 支持 SSL/TLS 加密发送邮件
- **IMAP 接收**: 支持收取、搜索、管理邮件
- **多格式支持**: 纯文本、HTML、混合内容
- **附件处理**: 支持多附件上传下载
- **邮件解析**: 自动解析邮件头、正文、附件
- **文件夹操作**: 支持多邮箱文件夹管理

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Email Client System                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  EmailClient                        │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │ SMTP Client  │  │ IMAP Client  │                │   │
│  │  │  (发送邮件)   │  │  (接收邮件)   │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Email Model                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  Header  │  │   Body   │  │Attachment│          │   │
│  │  │  (头部)  │  │  (正文)  │  │  (附件)  │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 邮件客户端 (EmailClient)

**位置**: `src/email/client.py`

```python
from src.email.client import EmailClient, email_client

# 使用全局实例
client = email_client

# 或创建新实例
client = EmailClient(
    smtp_host="smtp.example.com",
    smtp_port=587,
    smtp_user="user@example.com",
    smtp_password="password",
    imap_host="imap.example.com",
    imap_port=993,
    imap_user="user@example.com",
    imap_password="password",
)
```

#### 主要方法

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `connect_smtp()` | 连接 SMTP 服务器 | `bool` |
| `connect_imap()` | 连接 IMAP 服务器 | `bool` |
| `disconnect()` | 断开所有连接 | `None` |
| `send_email()` | 发送邮件 | `tuple[bool, str]` |
| `get_emails()` | 获取邮件列表 | `list[Email]` |
| `delete_email()` | 删除邮件 | `bool` |
| `move_email()` | 移动邮件到文件夹 | `bool` |
| `search_emails()` | 搜索邮件 | `list[Email]` |

---

### 2. 邮件数据模型

#### Email

```python
@dataclass
class Email:
    message_id: str                 # 邮件唯一ID
    from_address: str               # 发件人
    to_addresses: list[str]         # 收件人列表
    subject: str                    # 主题
    body_text: str                  # 纯文本正文
    body_html: str                  # HTML正文
    cc_addresses: list[str]         # 抄送列表
    attachments: list[Attachment]   # 附件列表
    received_at: datetime           # 接收时间
    flags: list[str]                # 标志（read, replied, starred）
```

#### Attachment

```python
@dataclass
class Attachment:
    filename: str       # 文件名
    content_type: str   # 内容类型
    size: int           # 文件大小
    data: bytes         # 文件数据
```

---

## 使用示例

### 发送邮件

```python
from src.email.client import EmailClient

client = EmailClient(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your_email@gmail.com",
    smtp_password="your_app_password",
)

# 发送纯文本邮件
success, message = client.send_email(
    to="recipient@example.com",
    subject="测试邮件",
    body="这是一封测试邮件。",
)

# 发送 HTML 邮件
success, message = client.send_email(
    to="recipient@example.com",
    subject="HTML 测试邮件",
    body="纯文本版本",
    body_html="<h1>HTML 版本</h1><p>这是一封 HTML 邮件。</p>",
)

# 发送带附件的邮件
success, message = client.send_email(
    to="recipient@example.com",
    subject="带附件的邮件",
    body="请查看附件。",
    attachments=["/path/to/file1.pdf", "/path/to/file2.jpg"],
)

# 发送给多人
success, message = client.send_email(
    to=["user1@example.com", "user2@example.com"],
    cc="manager@example.com",
    subject="群发邮件",
    body="大家好...",
)
```

### 接收邮件

```python
from src.email.client import EmailClient

client = EmailClient(
    imap_host="imap.gmail.com",
    imap_port=993,
    imap_user="your_email@gmail.com",
    imap_password="your_app_password",
)

# 获取收件箱邮件
emails = client.get_emails(folder="INBOX", limit=20)

for email in emails:
    print(f"来自: {email.from_address}")
    print(f"主题: {email.subject}")
    print(f"时间: {email.received_at}")
    print(f"已读: {'read' in email.flags}")
    print("-" * 40)

# 搜索邮件
results = client.search_emails("PyAgent", folder="INBOX")

# 移动邮件到已删除
client.move_email(message_id, dest_folder="Trash")
```

### 处理附件

```python
# 获取邮件附件
emails = client.get_emails(limit=5)

for email in emails:
    if email.attachments:
        print(f"邮件 '{email.subject}' 有 {len(email.attachments)} 个附件:")
        for att in email.attachments:
            print(f"  - {att.filename} ({att.size} bytes)")
            
            # 保存附件
            if att.data:
                with open(f"downloads/{att.filename}", "wb") as f:
                    f.write(att.data)
```

---

## API 接口

### REST API

#### 发送邮件
```http
POST /api/email/send
Content-Type: application/json

{
  "to": "recipient@example.com",
  "subject": "邮件主题",
  "body": "邮件正文",
  "body_html": "<p>HTML 正文</p>",
  "cc": "cc@example.com",
  "attachments": ["/path/to/file.pdf"]
}
```

#### 获取邮件列表
```http
GET /api/email/inbox?folder=INBOX&limit=20
```

#### 搜索邮件
```http
GET /api/email/search?query=PyAgent&folder=INBOX
```

#### 删除邮件
```http
DELETE /api/email/{message_id}
```

---

## 配置选项

```yaml
# config/email.yaml
email:
  smtp:
    host: "smtp.gmail.com"
    port: 587
    user: "your_email@gmail.com"
    password: "${EMAIL_PASSWORD}"
    use_tls: true
  
  imap:
    host: "imap.gmail.com"
    port: 993
    user: "your_email@gmail.com"
    password: "${EMAIL_PASSWORD}"
    use_ssl: true
```

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持 SMTP 发送邮件
- 支持 IMAP 接收邮件
- 支持 HTML 和纯文本
- 支持附件上传下载

---

## 相关文档

- [日历系统](./calendar.md) - 日程管理
- [API 文档](../api.md) - 完整 API 参考
