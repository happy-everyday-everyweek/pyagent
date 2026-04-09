# PyAgent æä½³å®è·µæå?v0.8.0

æ¬ææ¡£æä¾PyAgent v0.8.0çä½¿ç¨æä½³å®è·µï¼å¸®å©ç¨æ·æ´é«æå°ä½¿ç¨æ¡æ¶ã?
---

## ç®å½

- [é¡¹ç®ç»ææä½³å®è·µ](#é¡¹ç®ç»ææä½³å®è·?
- [éç½®ç®¡çæä½³å®è·µ](#éç½®ç®¡çæä½³å®è·?
- [LLMä½¿ç¨æä½³å®è·µ](#llmä½¿ç¨æä½³å®è·?
- [è®°å¿ç³»ç»æä½³å®è·µ](#è®°å¿ç³»ç»æä½³å®è·?
- [Todoç³»ç»æä½³å®è·µ](#todoç³»ç»æä½³å®è·?
- [IMéææä½³å®è·µ](#iméææä½³å®è·?
- [æ§è½ä¼åæä½³å®è·µ](#æ§è½ä¼åæä½³å®è·?
- [å®å¨æä½³å®è·µ](#å®å¨æä½³å®è·?
- [å¼åæä½³å®è·µ](#å¼åæä½³å®è·?
- [é¨ç½²æä½³å®è·µ](#é¨ç½²æä½³å®è·?

---

## é¡¹ç®ç»ææä½³å®è·?
### 1. ç®å½ç»ç»

```
pyagent/
âââ src/                    # æºä»£ç ?â?  âââ interaction/        # äº¤äºæ¨¡å
â?  âââ execution/          # æ§è¡æ¨¡å
â?  âââ memory/             # è®°å¿ç³»ç»
â?  âââ todo/               # Todoç³»ç»
â?  âââ llm/                # LLMå®¢æ·ç«?â?  âââ im/                 # IMééå?â?  âââ device/             # åç³»ç»?â?  âââ document/           # ææ¡£ç¼è¾å?â?  âââ video/              # è§é¢ç¼è¾å?â?  âââ web/                # Webæå¡
âââ config/                 # éç½®æä»¶
âââ data/                   # æ°æ®ç®å½
âââ skills/                 # æè½ç®å½?âââ tests/                  # æµè¯æä»¶
âââ docs/                   # ææ¡£
âââ frontend/               # åç«¯ä»£ç 
```

### 2. ä»£ç ç»ç»åå

```python
# å¥½çå®è·µï¼æ¨¡åèè´£æ¸æ?# src/todo/manager.py
class TodoManager:
    """Todoç®¡çå¨ï¼è´è´£Phase/Task/StepçCRUD"""
    
    async def create_phase(self, title: str) -> Phase:
        """åå»ºé¶æ®µ"""
        pass
    
    async def complete_step(self, step_id: str) -> None:
        """å®ææ­¥éª¤"""
        pass

# é¿åï¼ä¸ä¸ªæä»¶åå«å¤ä¸ªèè´?# bad_example.py
class TodoAndMemoryAndChat:  # ä¸è¦è¿æ ·å?    pass
```

---

## éç½®ç®¡çæä½³å®è·?
### 1. ç¯å¢åéç®¡ç

```bash
# .env æä»¶ï¼ä¸è¦æäº¤å°çæ¬æ§å¶ï¼?OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=ds-xxx

# .env.example æä»¶ï¼æäº¤å°çæ¬æ§å¶ï¼?OPENAI_API_KEY=your-openai-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
```

### 2. éç½®æä»¶åå±

```yaml
# config/models.yaml - æ¨¡åéç½®
base_model:
  provider: openai
  model: gpt-4o

tier_models:
  strong:
    provider: zhipu
    model: glm-5

# config/todo.yaml - Todoéç½®
reflection:
  min_rounds: 2
  max_rounds: 5

# config/memory.yaml - è®°å¿éç½®
chat:
  levels:
    daily:
      max_size: 1000
```

### 3. éç½®éªè¯

```python
from pydantic import BaseModel, validator

class ModelConfig(BaseModel):
    provider: str
    model: str
    temperature: float = 0.7
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('temperature must be between 0 and 2')
        return v
```

---

## LLMä½¿ç¨æä½³å®è·?
### 1. ä»»å¡ç±»åéæ©

```python
from src.llm import TaskType

# è§åä»»å¡ - ä½¿ç¨å¼ºè½åæ¨¡å?plan_response = await llm_client.generate(
    messages=planning_messages,
    task_type=TaskType.PLANNING  # èªå¨éæ© strong æ¨¡å
)

# æ¥å¸¸å¯¹è¯ - ä½¿ç¨é«æ§è½æ¨¡å
chat_response = await llm_client.generate(
    messages=chat_messages,
    task_type=TaskType.GENERAL  # èªå¨éæ© performance æ¨¡å
)

# è®°å¿æ´ç - ä½¿ç¨æ§ä»·æ¯æ¨¡å?memory_response = await llm_client.generate(
    messages=memory_messages,
    task_type=TaskType.MEMORY  # èªå¨éæ© cost_effective æ¨¡å
)
```

### 2. Promptä¼å

```python
# å¥½çå®è·µï¼æ¸æ°çæä»¤åä¸ä¸æ
messages = [
    {
        "role": "system",
        "content": """ä½ æ¯ä¸ä¸ªä¸ä¸çPythonå¼åèã?ä»»å¡ï¼åæä»£ç å¹¶æä¾ä¼åå»ºè®®ã?è¦æ±ï¼?1. æåºæ½å¨çæ§è½é®é¢
2. æä¾å·ä½çæ¹è¿æ¹æ¡?3. ç»åºéæåçä»£ç ç¤ºä¾"""
    },
    {
        "role": "user",
        "content": f"è¯·åæä»¥ä¸ä»£ç ï¼\n```python\n{code}\n```"
    }
]

# é¿åï¼æ¨¡ç³çæä»¤
# bad_messages = [
#     {"role": "user", "content": "ççè¿æ®µä»£ç "}  # å¤ªæ¨¡ç³?# ]
```

### 3. éè¯¯å¤ç

```python
from src.llm import LLMError

async def safe_generate(messages):
    try:
        response = await llm_client.generate(messages)
        return response
    except LLMError.RateLimit:
        # éçéå¶ï¼ç­å¾åéè¯
        await asyncio.sleep(60)
        return await safe_generate(messages)
    except LLMError.Timeout:
        # è¶æ¶ï¼ä½¿ç¨å¤ç¨æ¨¡å?        return await llm_client.generate(
            messages,
            model="backup_model"
        )
    except LLMError as e:
        logger.error(f"LLM error: {e}")
        return None
```

---

## è®°å¿ç³»ç»æä½³å®è·?
### 1. è®°å¿åå±ä½¿ç¨

```python
from src.memory import MemoryLevel

# ç­æè®°å¿ - é«é¢è®¿é®
await memory_manager.add_memory(
    content="ç¨æ·ä»å¤©è¯¢é®äºPythoné®é¢",
    level=MemoryLevel.DAILY
)

# é¿æè®°å¿ - éè¦ä¿¡æ¯
await memory_manager.add_memory(
    content="ç¨æ·æ¯Pythonå¼åèï¼åæ¬¢ä½¿ç¨FastAPI",
    level=MemoryLevel.QUARTERLY
)
```

### 2. è®°å¿æ£ç´¢ä¼å?
```python
# ä½¿ç¨å³é®è¯è¿æ»?memories = await memory_manager.retrieve(
    query="Pythoné¡¹ç®",
    keywords=["python", "fastapi", "django"],
    top_k=5
)

# ææ¶é´èå´è¿æ»?recent_memories = await memory_manager.retrieve(
    query="é¡¹ç®è¿å±",
    start_time=time.time() - 86400,  # æè¿?4å°æ¶
    end_time=time.time()
)
```

### 3. è®°å¿æ´ç

```python
# å®ææ´çè®°å¿
async def organize_memories():
    # åå¹¶ç¸ä¼¼è®°å¿
    await memory_manager.merge_similar(
        similarity_threshold=0.9
    )
    
    # å é¤è¿æè®°å¿
    await memory_manager.cleanup_expired()
    
    # çææè¦
    await memory_manager.summarize_old_memories()

# å®æ¶ä»»å¡
scheduler.add_job(organize_memories, 'cron', hour=3)
```

---

## Todoç³»ç»æä½³å®è·?
### 1. ä»»å¡åè§£

```python
# å¥½çå®è·µï¼åççä»»å¡ç²åº¦
phase = await todo_manager.create_phase("å¼åç¨æ·ç³»ç»?)

# ä»»å¡åºè¯¥è¶³å¤å°ï¼å¯ä»¥å¨ä¸å¤©åå®æ
task1 = await todo_manager.create_task(
    phase_id=phase.id,
    title="è®¾è®¡ç¨æ·æ°æ®æ¨¡å",
    steps=[
        "åæéæ±?,
        "è®¾è®¡æ°æ®åºè¡¨",
        "ç¼åSQLè¯­å¥"
    ]
)

task2 = await todo_manager.create_task(
    phase_id=phase.id,
    title="å®ç°ç¨æ·æ³¨åAPI",
    steps=[
        "åå»ºè·¯ç±",
        "å®ç°ä¸å¡é»è¾",
        "æ·»å éªè¯",
        "ç¼åæµè¯"
    ]
)
```

### 2. ä¾èµç®¡ç

```python
# å®ä¹ä»»å¡ä¾èµ
step1 = await todo_manager.create_step(
    task_id=task.id,
    content="è®¾è®¡æ°æ®åºè¡¨"
)

step2 = await todo_manager.create_step(
    task_id=task.id,
    content="å®ç°API",
    dependencies=[step1.id]  # ä¾èµstep1
)

# æ£æ¥ä¾èµæ¯å¦æ»¡è¶?can_complete = await todo_manager.check_dependencies(step2.id)
```

### 3. ä¼åçº§ç®¡ç?
```python
from src.todo import Priority

# ä½¿ç¨ä¼åçº?task = await todo_manager.create_task(
    phase_id=phase.id,
    title="ä¿®å¤å®å¨æ¼æ´",
    priority=Priority.CRITICAL  # æé«ä¼åçº§
)

# è·åå¾ååè¡¨ï¼æä¼åçº§æåºï¼
tasks = await todo_manager.get_pending_tasks(
    sort_by="priority"
)
```

---

## IMéææä½³å®è·?
### 1. æ¶æ¯å¤ç

```python
class MessageHandler:
    async def handle_message(self, message: Message):
        # 1. é¢å¤ç?        cleaned_content = self.preprocess(message.content)
        
        # 2. æ£æ¥æ¯å¦æ¯å½ä»¤
        if cleaned_content.startswith('/'):
            return await self.handle_command(cleaned_content)
        
        # 3. æ£æ¥æ¯å¦éè¦åå¤?        if not await self.should_reply(message):
            return
        
        # 4. çæåå¤
        response = await self.generate_response(cleaned_content)
        
        # 5. åéåå¤?        await self.send_reply(message.chat_id, response)
```

### 2. å¹³å°éé

```python
# ç»ä¸çæ¶æ¯æ ¼å¼?class UnifiedMessage:
    content: str
    sender_id: str
    chat_id: str
    platform: str
    timestamp: float
    attachments: List[Attachment]

# å¹³å°ééå?class WechatAdapter(IMAdapter):
    async def to_unified(self, raw_message) -> UnifiedMessage:
        return UnifiedMessage(
            content=raw_message['Content'],
            sender_id=raw_message['FromUserName'],
            chat_id=raw_message['FromUserName'],
            platform='wechat',
            timestamp=raw_message['CreateTime']
        )
```

### 3. ç¾¤ç»ç®¡ç

```python
# ç¾¤ç»ç½åå?ALLOWED_GROUPS = ['group_123', 'group_456']

async def handle_group_message(message):
    if message.chat_id not in ALLOWED_GROUPS:
        logger.info(f"Ignoring message from unauthorized group: {message.chat_id}")
        return
    
    # å¤çæ¶æ¯
    ...
```

---

## æ§è½ä¼åæä½³å®è·?
### 1. å¼æ­¥ç¼ç¨

```python
# å¥½çå®è·µï¼ä½¿ç¨å¼æ­?async def fetch_data():
    # å¹¶è¡è·åå¤ä¸ªèµæº
    results = await asyncio.gather(
        fetch_from_api1(),
        fetch_from_api2(),
        fetch_from_api3()
    )
    return results

# é¿åï¼åæ­¥é»å¡?# def bad_fetch_data():  # ä¸è¦è¿æ ·å?#     result1 = sync_fetch_from_api1()  # é»å¡
#     result2 = sync_fetch_from_api2()  # é»å¡
#     return result1, result2
```

### 2. ç¼å­ç­ç¥

```python
from functools import lru_cache
import aiocache

# åå­ç¼å­
@lru_cache(maxsize=128)
def expensive_computation(key):
    return heavy_calculation(key)

# Redisç¼å­ï¼åå¸å¼ï¼?cache = aiocache.Cache(aiocache.RedisCache)

@cache.cached(ttl=300)
async def get_user_data(user_id):
    return await db.fetch_user(user_id)
```

### 3. æ°æ®åºä¼å?
```python
# ä½¿ç¨è¿æ¥æ±?async with db_pool.acquire() as conn:
    result = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)

# æ¹éæä½
async with db_pool.acquire() as conn:
    async with conn.transaction():
        await conn.executemany(
            "INSERT INTO logs (level, message) VALUES ($1, $2)",
            log_entries
        )

# æ·»å ç´¢å¼
await db.execute("""
    CREATE INDEX CONCURRENTLY IF NOT EXISTS 
    idx_messages_chat_id_timestamp 
    ON messages(chat_id, timestamp DESC)
""")
```

---

## å®å¨æä½³å®è·?
### 1. APIå¯é¥ç®¡ç

```python
# ä½¿ç¨ç¯å¢åé
import os

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")

# ä¸è¦å¨ä»£ç ä¸­ç¡¬ç¼ç ?# BAD: api_key = "sk-xxx"  # ä¸è¦è¿æ ·å?```

### 2. è¾å¥éªè¯

```python
from pydantic import BaseModel, validator
import bleach

class ChatRequest(BaseModel):
    message: str
    chat_id: str
    
    @validator('message')
    def sanitize_message(cls, v):
        # æ¸çHTMLæ ç­¾
        return bleach.clean(v, tags=[], strip=True)
    
    @validator('chat_id')
    def validate_chat_id(cls, v):
        # éªè¯æ ¼å¼
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid chat_id format')
        return v
```

### 3. è®¿é®æ§å¶

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not validate_token(token):
            raise HTTPException(status_code=401, detail="Unauthorized")
        return await f(*args, **kwargs)
    return decorated

@app.post("/api/admin/config")
@require_auth
async def update_config(request: ConfigRequest):
    pass
```

---

## å¼åæä½³å®è·?
### 1. ä»£ç é£æ ¼

```python
# éµå¾ªPEP 8
# ä½¿ç¨ç±»åæ³¨è§£
from typing import Optional, List

async def process_message(
    message: str,
    chat_id: str,
    context: Optional[dict] = None
) -> dict:
    """å¤çæ¶æ¯å¹¶è¿åååºã?    
    Args:
        message: ç¨æ·æ¶æ¯åå®¹
        chat_id: èå¤©ä¼è¯ID
        context: å¯éçä¸ä¸æä¿¡æ?        
    Returns:
        åå«ååºåå®¹çå­å?    """
    pass
```

### 2. éè¯¯å¤ç

```python
# èªå®ä¹å¼å¸?class PyAgentError(Exception):
    """åºç¡å¼å¸¸ç±?""
    pass

class ValidationError(PyAgentError):
    """éªè¯éè¯¯"""
    pass

# ä½¿ç¨å¼å¸¸
async def create_phase(title: str):
    if not title:
        raise ValidationError("Title cannot be empty")
    
    try:
        phase = await db.insert_phase(title)
        return phase
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise PyAgentError("Failed to create phase") from e
```

### 3. æµè¯

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_phase():
    # åå¤
    mock_db = AsyncMock()
    mock_db.insert_phase.return_value = {"id": "123", "title": "Test"}
    
    # æ§è¡
    with patch('src.todo.manager.db', mock_db):
        result = await todo_manager.create_phase("Test")
    
    # éªè¯
    assert result["id"] == "123"
    assert result["title"] == "Test"
    mock_db.insert_phase.assert_called_once_with("Test")
```

---

## é¨ç½²æä½³å®è·?
### 1. ç¯å¢éç½®

```bash
# çäº§ç¯å¢
export ENV=production
export LOG_LEVEL=WARNING
export WORKERS=4

# å¼åç¯å¢?export ENV=development
export LOG_LEVEL=DEBUG
export RELOAD=true
```

### 2. è¿ç¨ç®¡ç

```ini
# supervisord.conf
[program:pyagent]
command=python -m src.main --host 0.0.0.0 --port 8000
directory=/opt/pyagent
user=pyagent
autostart=true
autorestart=true
stderr_logfile=/var/log/pyagent/err.log
stdout_logfile=/var/log/pyagent/out.log
```

### 3. çæ§åè­¦

```python
# å¥åº·æ£æ?@app.get("/health")
async def health_check():
    checks = {
        "llm": await check_llm_health(),
        "memory": await check_memory_health(),
        "todo": await check_todo_health()
    }
    
    if not all(checks.values()):
        await send_alert("Service unhealthy", checks)
        raise HTTPException(status_code=503)
    
    return {"status": "healthy", "checks": checks}
```

### 4. æ¥å¿ç®¡ç

```python
import logging
from logging.handlers import RotatingFileHandler

# éç½®æ¥å¿
logger = logging.getLogger('pyagent')
logger.setLevel(logging.INFO)

# æä»¶æ¥å¿
file_handler = RotatingFileHandler(
    'data/logs/pyagent.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

# ç»æåæ¥å¿?import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        })
```

---

## æ»ç»

éµå¾ªè¿äºæä½³å®è·µå¯ä»¥å¸®å©ä½ ï¼?
1. **æé«ä»£ç è´¨é**: æ´æ¸æ°ãæ´æç»´æ?2. **æåæ§è½**: æ´å¿«çååºéåº¦
3. **å¢å¼ºå®å¨æ?*: ä¿æ¤æææ°æ®
4. **ç®åé¨ç½?*: æ´ç¨³å®çè¿è¡ç¯å¢
5. **æ¹åç¨æ·ä½éª**: æ´å¯é çæå¡

---

**PyAgent v0.8.0 - è®©AIæ´æºè½ï¼è®©åä½æ´é«æ**
