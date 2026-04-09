# PyAgent æéæé¤æå v0.8.0

æ¬ææ¡£å¸®å©ç¨æ·è¯æ­åè§£å³PyAgent v0.8.0ä½¿ç¨è¿ç¨ä¸­éå°çå¸¸è§é®é¢ã?
---

## ç®å½

- [å¿«éè¯æ­](#å¿«éè¯æ?
- [å®è£é®é¢](#å®è£é®é¢)
- [å¯å¨é®é¢](#å¯å¨é®é¢)
- [è¿è¡æ¶é®é¢](#è¿è¡æ¶é®é¢?
- [IMå¹³å°é®é¢](#imå¹³å°é®é¢)
- [LLMé®é¢](#llmé®é¢)
- [è®°å¿ç³»ç»é®é¢](#è®°å¿ç³»ç»é®é¢)
- [Todoç³»ç»é®é¢](#todoç³»ç»é®é¢)
- [åç³»ç»é®é¢](#åç³»ç»é®é¢?
- [æ§è½é®é¢](#æ§è½é®é¢)
- [è·åå¸®å©](#è·åå¸®å©)

---

## å¿«éè¯æ?
### 1. æ£æ¥ç³»ç»ç¶æ?
```bash
# æ£æ¥æå¡æ¯å¦è¿è¡?curl http://localhost:8000/health

# æ¥çæ¥å¿
tail -f data/logs/pyagent.log

# æ£æ¥è¿ç¨?ps aux | grep pyagent
```

### 2. å¸¸è§é®é¢éæ¥è¡?
| é®é¢ | å¯è½åå  | å¿«éè§£å?|
|------|----------|----------|
| æå¡æ æ³å¯å¨ | ç«¯å£è¢«å ç?| ä¿®æ¹ç«¯å£æå³é­å ç¨è¿ç¨?|
| APIæ ååº?| æå¡æªå¯å?| æ£æ¥æå¡ç¶æ?|
| LLMè°ç¨å¤±è´¥ | APIå¯é¥éè¯¯ | æ£æ?envéç½® |
| è®°å¿ä¸¢å¤± | æ°æ®ç®å½æé | æ£æ¥dataç®å½æé |
| IMæ¶æ¯ä¸æ¥æ?| Webhookéç½®éè¯¯ | æ£æ¥IMå¹³å°éç½® |

---

## å®è£é®é¢

### é®é¢1: pipå®è£ä¾èµå¤±è´¥

**çç¶**:
```
ERROR: Could not find a version that satisfies the requirement xxx
```

**è§£å³æ¹æ¡**:

1. åçº§pip:
```bash
pip install --upgrade pip
```

2. ä½¿ç¨å½åéå:
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. æ£æ¥Pythonçæ¬:
```bash
python --version  # éè¦?.10+
```

### é®é¢2: åç«¯æå»ºå¤±è´¥

**çç¶**:
```
npm ERR! code ENOENT
npm ERR! syscall open
```

**è§£å³æ¹æ¡**:

1. æ¸é¤npmç¼å­:
```bash
npm cache clean --force
```

2. å é¤node_moduleséæ°å®è£:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

3. æ£æ¥Node.jsçæ¬:
```bash
node --version  # éè¦?6+
```

---

## å¯å¨é®é¢

### é®é¢1: ç«¯å£è¢«å ç?
**çç¶**:
```
OSError: [Errno 98] Address already in use
```

**è§£å³æ¹æ¡**:

1. æ¥æ¾å ç¨ç«¯å£çè¿ç¨?
```bash
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

2. å³é­å ç¨è¿ç¨ææ´æ¢ç«¯å?
```bash
python -m src.main --port 8001
```

### é®é¢2: ç¼ºå°ç¯å¢åé

**çç¶**:
```
KeyError: 'OPENAI_API_KEY'
```

**è§£å³æ¹æ¡**:

1. åå»º.envæä»¶:
```bash
cp .env.example .env
```

2. ç¼è¾.envæä»¶ï¼æ·»å APIå¯é¥:
```env
OPENAI_API_KEY=sk-your-key
```

3. éæ°å è½½ç¯å¢åé:
```bash
source .env  # Linux/Mac
# æéå¯ç»ç«?```

### é®é¢3: æ¨¡åå¯¼å¥éè¯¯

**çç¶**:
```
ModuleNotFoundError: No module named 'src.xxx'
```

**è§£å³æ¹æ¡**:

1. ç¡®ä¿å¨é¡¹ç®æ ¹ç®å½è¿è¡:
```bash
cd /path/to/pyagent
python -m src.main
```

2. æ£æ¥PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

3. å®è£editableæ¨¡å¼:
```bash
pip install -e .
```

---

## è¿è¡æ¶é®é¢?
### é®é¢1: APIè¿å500éè¯¯

**çç¶**:
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

**ææ¥æ­¥éª¤**:

1. æ¥çè¯¦ç»æ¥å¿:
```bash
tail -n 100 data/logs/pyagent.log
```

2. æ£æ¥å³é®ç»ä»¶ç¶æ?
```bash
curl http://localhost:8000/health
```

3. éå¯æå¡:
```bash
# åæ­¢ç°ææå¡
pkill -f "python -m src.main"

# éæ°å¯å¨
python -m src.main
```

### é®é¢2: WebSocketè¿æ¥å¤±è´¥

**çç¶**:
```
WebSocket connection failed
```

**è§£å³æ¹æ¡**:

1. æ£æ¥æå¡æ¯å¦æ¯æWebSocket:
```bash
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: xxx" \
  http://localhost:8000/ws
```

2. æ£æ¥é²ç«å¢è®¾ç½®:
```bash
# Linux
sudo ufw status
sudo ufw allow 8000
```

3. ä½¿ç¨æ­£ç¡®çWebSocket URL:
```javascript
// æ­£ç¡®
const ws = new WebSocket('ws://localhost:8000/ws');

// éè¯¯
const ws = new WebSocket('http://localhost:8000/ws');
```

### é®é¢3: åå­å ç¨è¿é«

**çç¶**:
- ç³»ç»åæ¢
- è¿ç¨è¢«OOM killerç»æ­¢

**è§£å³æ¹æ¡**:

1. éå¶å¹¶åä»»å¡æ?
```python
# config/config.yaml
max_concurrent_tasks: 5
```

2. å®ææ¸çç¼å­:
```python
# æå¨æ¸ç
await memory_manager.clear_cache()
```

3. å¢å ç³»ç»åå­æå¯ç¨swap

---

## IMå¹³å°é®é¢

### é®é¢1: å¾®ä¿¡ç»å½å¤±è´¥

**çç¶**:
```
å¾®ä¿¡ç»å½è¶æ¶
äºç»´ç æ æ³æ«æ?```

**è§£å³æ¹æ¡**:

1. æ£æ¥ç½ç»è¿æ?
```bash
ping wx.qq.com
```

2. æ¸é¤ç»å½ç¼å­:
```bash
rm -rf data/im/wechat/session_*
```

3. éæ°æ«ç ç»å½

4. æ£æ¥å¾®ä¿¡çæ¬å¼å®¹æ?
### é®é¢2: ééæ¶æ¯ä¸æ¥æ?
**çç¶**:
```
Webhookéªè¯å¤±è´¥
æ¶æ¯æ æ³åé?```

**è§£å³æ¹æ¡**:

1. æ£æ¥Webhook URL:
```bash
# æµè¯Webhook
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"text","text":{"content":"test"}}' \
  YOUR_WEBHOOK_URL
```

2. æ£æ¥IPç½åå?
- ééæºå¨äººéè¦éç½®IPç½åå?- æ·»å æå¡å¨IPå°ç½åå

3. éªè¯ç­¾å:
```python
import hmac
import hashlib
import base64

timestamp = str(round(time.time() * 1000))
secret = 'your-secret'
secret_enc = secret.encode('utf-8')
string_to_sign = '{}
{}'.format(timestamp, secret)
string_to_sign_enc = string_to_sign.encode('utf-8')
hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
```

### é®é¢3: QQæ¶æ¯ä¹±ç 

**çç¶**:
```
æ¶æ¯åå®¹æ¾ç¤ºä¸ºä¹±ç ?```

**è§£å³æ¹æ¡**:

1. æ£æ¥ç¼ç è®¾ç½?
```python
# ç¡®ä¿ä½¿ç¨UTF-8
import sys
sys.setdefaultencoding('utf-8')
```

2. éç½®OneBotç¼ç :
```yaml
# config/onebot.yaml
encoding: utf-8
```

---

## LLMé®é¢

### é®é¢1: APIè°ç¨å¤±è´¥

**çç¶**:
```
Error: 401 Unauthorized
Error: 429 Too Many Requests
```

**è§£å³æ¹æ¡**:

1. æ£æ¥APIå¯é¥:
```bash
# æµè¯APIå¯é¥
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

2. æ£æ¥éé¢?
- ç»å½OpenAIæ§å¶å°æ¥çä½¿ç¨æå?- æ£æ¥æ¯å¦è¶åºéçéå¶

3. ä½¿ç¨å¤ç¨æ¨¡å:
```yaml
# config/models.yaml
base_model:
  provider: deepseek  # åæ¢å°å¤ç¨æä¾å
```

### é®é¢2: ååºè¶æ¶

**çç¶**:
```
TimeoutError: Request timed out
```

**è§£å³æ¹æ¡**:

1. å¢å è¶æ¶æ¶é´:
```python
# src/llm/client.py
response = await client.generate(
    messages=messages,
    timeout=60  # å¢å å?0ç§?)
```

2. ä½¿ç¨æµå¼ååº:
```python
async for chunk in client.generate_stream(messages):
    yield chunk
```

3. ä¼åPrompté¿åº¦:
```python
# æªæ­è¿é¿çä¸ä¸æ
messages = messages[-10:]  # åªä¿çæè¿?0æ?```

### é®é¢3: æ¨¡åéæ©éè¯¯

**çç¶**:
```
Model not found: xxx
```

**è§£å³æ¹æ¡**:

1. æ£æ¥æ¨¡åéç½?
```yaml
# config/models.yaml
base_model:
  provider: openai
  model: gpt-4o  # ç¡®ä¿æ¨¡ååç§°æ­£ç¡®
```

2. æ¥çå¯ç¨æ¨¡å:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## è®°å¿ç³»ç»é®é¢

### é®é¢1: è®°å¿æ æ³å­å¨

**çç¶**:
```
è®°å¿æ·»å æåä½æ æ³æ£ç´?```

**è§£å³æ¹æ¡**:

1. æ£æ¥æ°æ®ç®å½æé?
```bash
ls -la data/memory/
chmod 755 data/memory/
```

2. æ£æ¥ç£çç©ºé?
```bash
df -h
```

3. éå»ºè®°å¿ç´¢å¼:
```python
await memory_manager.rebuild_index()
```

### é®é¢2: è®°å¿æ£ç´¢ä¸åç¡®

**çç¶**:
```
æ£ç´¢ç»æä¸æ¥è¯¢ä¸ç¸å?```

**è§£å³æ¹æ¡**:

1. è°æ´ç¸ä¼¼åº¦éå?
```python
# config/memory.yaml
retrieval:
  similarity_threshold: 0.7
  top_k: 5
```

2. ä½¿ç¨å³é®è¯è¿æ»?
```python
memories = await memory_manager.retrieve(
    query="Python",
    keywords=["programming", "coding"]
)
```

3. å®ææ´çè®°å¿:
```python
await memory_manager.organize()
```

---

## Todoç³»ç»é®é¢

### é®é¢1: é¶æ®µæ æ³å®æ

**çç¶**:
```
ææä»»å¡å·²å®æä½é¶æ®µç¶ææªæ´æ°
```

**è§£å³æ¹æ¡**:

1. æå¨è§¦åç¶ææ´æ?
```python
await todo_manager.update_phase_status(phase_id)
```

2. æ£æ¥ä»»å¡ç¶æ?
```python
phase = await todo_manager.get_phase(phase_id)
for task in phase.tasks:
    print(f"{task.title}: {task.status}")
```

3. å¼ºå¶å®æé¶æ®µ:
```python
await todo_manager.force_complete_phase(phase_id)
```

### é®é¢2: åææªè§¦å

**çç¶**:
```
é¶æ®µå®æåæ²¡æè¿è¡åæ?```

**è§£å³æ¹æ¡**:

1. æ£æ¥åæéç½?
```yaml
# config/todo.yaml
reflection:
  auto_trigger: true
  min_rounds: 2
  max_rounds: 5
```

2. æå¨è§¦ååæ?
```python
await todo_manager.trigger_reflection(phase_id)
```

3. æ¥çåææ¥å¿?
```bash
grep "reflection" data/logs/pyagent.log
```

---

## åç³»ç»é®é¢?
### é®é¢1: è®¾å¤æ æ³å å¥å?
**çç¶**:
```
å å¥åå¤±è´? Domain not found
```

**è§£å³æ¹æ¡**:

1. æ£æ¥åID:
```bash
curl http://localhost:8000/api/domains
```

2. æ£æ¥ç½ç»è¿æ?
```bash
ping domain-server-ip
```

3. æ£æ¥åéç½®:
```yaml
# config/domain.yaml
domain:
  max_devices: 10
```

### é®é¢2: æ°æ®åæ­¥å¤±è´¥

**çç¶**:
```
Sync failed: Connection timeout
```

**è§£å³æ¹æ¡**:

1. æ£æ¥åæ­¥æ¨¡å¼?
```yaml
# config/domain.yaml
sync:
  default_mode: scheduled
  scheduled:
    interval_minutes: 30
```

2. æå¨è§¦ååæ­¥:
```python
await sync_engine.sync_to_domain(
    device_id="device_xxx",
    data_type="memory",
    data=memory_data
)
```

3. æ£æ¥å²çª?
```python
conflicts = await conflict_resolver.get_conflicts(domain_id)
for conflict in conflicts:
    await conflict_resolver.resolve(conflict.id, strategy="newer_wins")
```

---

## æ§è½é®é¢

### é®é¢1: ååºéåº¦æ?
**çç¶**:
```
APIååºæ¶é´è¶è¿5ç§?```

**è§£å³æ¹æ¡**:

1. å¯ç¨æ§è½åæ:
```python
# æ·»å è£é¥°å?@profile
async def slow_function():
    pass
```

2. ä¼åæ°æ®åºæ¥è¯?
```python
# æ·»å ç´¢å¼
await db.execute("CREATE INDEX IF NOT EXISTS idx_memory ON memories(timestamp)")
```

3. ä½¿ç¨ç¼å­:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(key):
    pass
```

### é®é¢2: CPUå ç¨è¿é«

**çç¶**:
```
CPUä½¿ç¨çæç»­è¶è¿?0%
```

**è§£å³æ¹æ¡**:

1. éå¶å¹¶å:
```python
semaphore = asyncio.Semaphore(5)
```

2. ä¼åç®æ³:
```python
# ä½¿ç¨çæå¨æ¿ä»£åè¡?for item in generator():  # èä¸æ?list
    process(item)
```

3. ä½¿ç¨å¤è¿ç¨?
```python
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.map(process, items)
```

---

## è·åå¸®å©

### 1. æ¶éè¯æ­ä¿¡æ¯

```bash
# åå»ºè¯æ­æ¥å
python -c "
import json
import psutil
import platform

diagnostic = {
    'platform': platform.platform(),
    'python_version': platform.python_version(),
    'cpu_count': psutil.cpu_count(),
    'memory': psutil.virtual_memory()._asdict(),
    'disk': psutil.disk_usage('/')._asdict()
}
print(json.dumps(diagnostic, indent=2))
"
```

### 2. æ¥çæ¥å¿

```bash
# æ¥çæè¿çéè¯¯
grep "ERROR" data/logs/pyagent.log | tail -20

# æ¥çç¹å®æ¨¡åçæ¥å¿?grep "todo" data/logs/pyagent.log | tail -50
```

### 3. æäº¤Issue

å¦æä»¥ä¸æ¹æ³é½æ æ³è§£å³é®é¢ï¼è¯·æäº¤Issueï¼?
1. æè¿°é®é¢ç°è±¡
2. æä¾å¤ç°æ­¥éª¤
3. éä¸ç¸å³æ¥å¿
4. æä¾ç¯å¢ä¿¡æ¯
5. è¯´æå·²å°è¯çè§£å³æ¹æ¡

**Issueæ¨¡æ¿**:
```markdown
## é®é¢æè¿°
[æ¸æ°æè¿°é®é¢]

## å¤ç°æ­¥éª¤
1. [æ­¥éª¤1]
2. [æ­¥éª¤2]
3. [æ­¥éª¤3]

## ææè¡ä¸º
[æè¿°ææçç»æ]

## å®éè¡ä¸º
[æè¿°å®éçç»æ]

## ç¯å¢ä¿¡æ¯
- OS: [æä½ç³»ç»]
- Python: [Pythonçæ¬]
- PyAgent: [PyAgentçæ¬]

## æ¥å¿
[éä¸ç¸å³æ¥å¿]

## å·²å°è¯çè§£å³æ¹æ¡
[ååºå·²å°è¯çæ¹æ³]
```

---

**PyAgent v0.8.0 - è®©AIæ´æºè½ï¼è®©åä½æ´é«æ**
