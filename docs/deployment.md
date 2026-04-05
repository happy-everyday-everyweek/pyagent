# PyAgent 部署文档 v0.8.0

本文档详细说明如何部署PyAgent v0.8.0到生产环境�?
## 目录

- [本地部署](#本地部署)
- [Docker部署](#docker部署)
- [生产环境部署](#生产环境部署)
- [IM平台接入](#im平台接入)

## 本地部署

### 环境准备

- Python 3.10+
- pip �?uv
- Git

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd pyagent
```

2. **创建虚拟环境**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，填入API密钥等配�?```

5. **运行**

```bash
# Web模式
python -m src.main --mode web

# IM模式
python -m src.main --mode im

# 同时运行
python -m src.main --mode both
```

---

## Docker部署

### 使用Docker运行

1. **构建镜像**

```bash
docker build -t pyagent:latest .
```

2. **运行容器**

```bash
docker run -d \
  --name pyagent \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  pyagent:latest
```

### 使用Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  pyagent:
    build: .
    container_name: pyagent
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./skills:/app/skills
      - ./.env:/app/.env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    
  # 可选：OneBot服务
  onebot:
    image: ghcr.io/mrs4s/go-cqhttp:master
    container_name: onebot
    volumes:
      - ./onebot-data:/data
    ports:
      - "3001:3001"
    restart: unless-stopped
```

启动�?
```bash
docker-compose up -d
```

---

## 生产环境部署

### 使用Gunicorn

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.web.app:app -b 0.0.0.0:8000
```

### 使用Nginx反向代理

Nginx配置�?
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 使用Systemd服务

创建 `/etc/systemd/system/pyagent.service`:

```ini
[Unit]
Description=PyAgent Service
After=network.target

[Service]
Type=simple
User=pyagent
WorkingDirectory=/opt/pyagent
Environment=PATH=/opt/pyagent/venv/bin
ExecStart=/opt/pyagent/venv/bin/python -m src.main --mode both
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务�?
```bash
sudo systemctl daemon-reload
sudo systemctl enable pyagent
sudo systemctl start pyagent
sudo systemctl status pyagent
```

### 使用PM2 (Node.js进程管理�?

创建 `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'pyagent',
    script: 'python',
    args: '-m src.main --mode both',
    cwd: '/opt/pyagent',
    interpreter: '/opt/pyagent/venv/bin/python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    log_file: '/var/log/pyagent/combined.log',
    out_file: '/var/log/pyagent/out.log',
    error_file: '/var/log/pyagent/error.log'
  }]
};
```

启动�?
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## IM平台接入

### OneBot (QQ) 接入

#### 使用 go-cqhttp

1. **下载安装**

```bash
# 下载对应平台的release
wget https://github.com/Mrs4s/go-cqhttp/releases/download/v1.2.0/go-cqhttp_linux_amd64.tar.gz
tar -xzf go-cqhttp_linux_amd64.tar.gz
chmod +x go-cqhttp
```

2. **初始化配�?*

```bash
./go-cqhttp
# 选择 0: HTTP通信
```

3. **编辑配置**

编辑 `config.yml`:

```yaml
account:
  uin: 123456789  # QQ�?  password: ''    # 密码（留空扫码登录）

servers:
  - ws:
      host: 0.0.0.0
      port: 3001
      middlewares:
        access-token: your_token
```

4. **启动**

```bash
./go-cqhttp
```

5. **配置PyAgent**

�?`.env` 中添加：

```env
ONEBOT_WS_URL=ws://127.0.0.1:3001
ONEBOT_ACCESS_TOKEN=your_token
```

---

### 钉钉接入

1. **创建机器�?*

- 登录钉钉开放平�?- 创建企业内部应用
- 添加机器�?- 获取Webhook地址和Secret

2. **配置PyAgent**

```env
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your_secret
```

3. **设置回调URL**（可选，用于接收消息�?
在钉钉开放平台设置回调URL指向你的服务器�?
---

### 飞书接入

1. **创建应用**

- 登录飞书开放平�?- 创建企业自建应用
- 获取 App ID �?App Secret

2. **配置PyAgent**

```env
FEISHU_APP_ID=cli_xxxxxxxx
FEISHU_APP_SECRET=xxxxxxxx
```

3. **启用机器人能�?*

在应用管理后台启用机器人能力�?
4. **设置事件订阅**（可选）

配置事件订阅URL以接收消息�?
---

### 企业微信接入

1. **创建应用**

- 登录企业微信管理后台
- 应用管理 -> 创建应用
- 获取 CorpID, AgentID, Secret

2. **配置PyAgent**

```env
WECOM_CORP_ID=wwxxxxxxxxxxxxxxxx
WECOM_AGENT_ID=1000002
WECOM_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

3. **设置接收消息**（可选）

配置接收消息的URL、Token和EncodingAESKey�?
---

## 监控与日�?
### 日志配置

```python
# 日志文件位置
data/logs/pyagent.log

# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### 使用Prometheus监控

添加Prometheus客户端：

```python
from prometheus_client import Counter, Histogram, generate_latest

# 定义指标
request_count = Counter('pyagent_requests_total', 'Total requests')
request_duration = Histogram('pyagent_request_duration_seconds', 'Request duration')

# 在FastAPI中添加metrics端点
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 健康检�?
```bash
curl http://localhost:8000/health
```

---

## 备份与恢�?
### 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/pyagent/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据目录
cp -r data $BACKUP_DIR/

# 备份配置
cp -r config $BACKUP_DIR/
cp .env $BACKUP_DIR/

# 备份技�?cp -r skills $BACKUP_DIR/

# 压缩
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

### 数据恢复

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
tar -xzf $BACKUP_FILE

# 恢复数据
cp -r data/* data/
cp -r config/* config/
cp .env .env
```

---

## 故障排查

### 常见问题

#### 1. 启动失败

```bash
# 检查日�?tail -f data/logs/pyagent.log

# 检查依�?pip list | grep -E "fastapi|uvicorn|openai"

# 检查端口占�?netstat -tlnp | grep 8000
```

#### 2. IM连接失败

```bash
# 检查OneBot连接
curl http://localhost:3001/get_version_info

# 检查WebSocket
wscat -c ws://localhost:3001
```

#### 3. LLM调用失败

```bash
# 测试API密钥
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 4. 内存不足

```bash
# 查看内存使用
free -h

# 限制Python内存
ulimit -v 2097152  # 2GB
```

### 调试模式

```bash
# 开启调试日�?LOG_LEVEL=DEBUG python -m src.main
```
