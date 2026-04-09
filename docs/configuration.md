# PyAgent éç½®ææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»è¯´æPyAgent v0.8.0çææéç½®éé¡¹ã?
## ç®å½

- [ç¯å¢åééç½®](#ç¯å¢åééç½®)
- [æ¨¡åéç½®](#æ¨¡åéç½®)
- [MCPéç½®](#mcpéç½®)
- [IMå¹³å°éç½®](#imå¹³å°éç½®)
- [Todoç³»ç»éç½®](#todoç³»ç»éç½®)
- [Mateæ¨¡å¼éç½®](#mateæ¨¡å¼éç½®)
- [è®°å¿ç³»ç»éç½®](#è®°å¿ç³»ç»éç½®)
- [èªæå­¦ä¹ éç½®](#èªæå­¦ä¹ éç½®)
- [ç³»ç»éç½®](#ç³»ç»éç½®)

## ç¯å¢åééç½®

éè¿ `.env` æä»¶æç³»ç»ç¯å¢åééç½®ã?
### LLM APIå¯é¥

#### OpenAI

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1  # å¯éï¼ç¨äºä»£ç
```

#### DeepSeek

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
```

#### æºè°±AI

```env
ZHIPU_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
ZHIPU_MODEL=glm-4
```

#### Anthropic

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### IMå¹³å°éç½®

#### OneBot (QQ)

```env
ONEBOT_WS_URL=ws://127.0.0.1:3001
ONEBOT_ACCESS_TOKEN=your_token
ONEBOT_PLATFORM=qq
```

#### éé

```env
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your_secret
```

#### é£ä¹¦

```env
FEISHU_APP_ID=cli_xxxxxxxx
FEISHU_APP_SECRET=xxxxxxxx
```

#### ä¼ä¸å¾®ä¿¡

```env
WECOM_CORP_ID=wwxxxxxxxxxxxxxxxx
WECOM_AGENT_ID=1000002
WECOM_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Webæå¡éç½®

```env
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_RELOAD=false
```

### æ¥å¿éç½®

```env
LOG_LEVEL=INFO
LOG_FILE=data/logs/pyagent.log
```

### Todoéç½®

```env
TODO_DATA_DIR=data/todo
TODO_AUTO_SAVE=true
TODO_REFLECTION_MIN_ROUNDS=2
TODO_REFLECTION_MAX_ROUNDS=5
```

### Mateæ¨¡å¼éç½®

```env
MATE_MODE_ENABLED=false
MATE_MODE_MAX_REFLECTION_ROUNDS=3
MATE_MODE_SHOW_REASONING=true
```

### è®°å¿ç³»ç»éç½®

```env
MEMORY_CHAT_DATA_DIR=data/memory/chat
MEMORY_WORK_DATA_DIR=data/memory/work
MEMORY_AUTO_CONSOLIDATION=true
```

---

## æ¨¡åéç½®

éç½®æä»¶è·¯å¾: `config/models.yaml`

### éç½®ç»æ

```yaml
models:
  # å¼ºåæ¨¡å - ç¨äºå¤æä»»å¡
  strong:
    provider: openai
    model: gpt-4o
    api_key: ${OPENAI_API_KEY}
    base_url: ${OPENAI_BASE_URL}
    priority: 1
    max_tokens: 4096
    temperature: 0.7
    timeout: 180
    max_retries: 3
    retry_delay: 1.0
    enabled: true
    capabilities:
      - text
      - vision
      - tools

  # åè¡¡æ¨¡å - æ¥å¸¸ä½¿ç¨
  balanced:
    provider: deepseek
    model: deepseek-chat
    api_key: ${DEEPSEEK_API_KEY}
    priority: 2
    max_tokens: 4096
    temperature: 0.8
    timeout: 120
    max_retries: 3
    retry_delay: 1.0
    enabled: true
    capabilities:
      - text
      - tools

  # å¿«éæ¨¡å?- ç®åä»»å?  fast:
    provider: zhipu
    model: glm-4-flash
    api_key: ${ZHIPU_API_KEY}
    priority: 3
    max_tokens: 2048
    temperature: 0.9
    timeout: 60
    max_retries: 2
    retry_delay: 0.5
    enabled: true
    capabilities:
      - text

  # è½»éæ¨¡å - æä½ææ?  tiny:
    provider: zhipu
    model: glm-4-flash
    api_key: ${ZHIPU_API_KEY}
    priority: 4
    max_tokens: 1024
    temperature: 1.0
    timeout: 30
    max_retries: 1
    retry_delay: 0.5
    enabled: true
    capabilities:
      - text
```

### éç½®é¡¹è¯´æ?
| éç½®é¡?| ç±»å | é»è®¤å?| è¯´æ |
|--------|------|--------|------|
| provider | string | å¿å¡« | æä¾å? openai, deepseek, zhipu, anthropic |
| model | string | å¿å¡« | æ¨¡ååç§° |
| api_key | string | å¿å¡« | APIå¯é¥ |
| base_url | string | null | èªå®ä¹APIåºç¡URL |
| priority | int | 1 | ä¼åçº§ï¼æ°å­è¶å°ä¼åçº§è¶é«?|
| max_tokens | int | 4096 | æå¤§çætokenæ?|
| temperature | float | 1.0 | æ¸©åº¦åæ°(0-2) |
| timeout | int | 180 | è¯·æ±è¶æ¶æ¶é´(ç§? |
| max_retries | int | 3 | æå¤§éè¯æ¬¡æ?|
| retry_delay | float | 1.0 | éè¯å»¶è¿(ç§? |
| enabled | bool | true | æ¯å¦å¯ç¨ |
| capabilities | list | ["text"] | è½ååè¡¨: text, vision, tools |

### è´è½½åè¡¡ç­ç¥

å?`src/llm/client.py` ä¸­éç½®ï¼

```python
llm_client = LLMClient(
    models=models,
    selection_strategy="balance"  # å¯é? "random", "balance"
)
```

- **random**: éæºéæ©å¯ç¨æ¨¡å
- **balance**: åºäºtokenä½¿ç¨éåè¡¡ï¼é»è®¤ï¼?
---

## MCPéç½®

éç½®æä»¶è·¯å¾: `config/mcp.json`

### éç½®ç»æ

```json
{
  "servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
      "transport": "stdio",
      "description": "æä»¶ç³»ç»è®¿é®"
    },
    {
      "name": "sqlite",
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/path/to/db.sqlite"],
      "transport": "stdio",
      "description": "SQLiteæ°æ®åºè®¿é?
    },
    {
      "name": "fetch",
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "transport": "stdio",
      "description": "ç½ç»è¯·æ±"
    }
  ]
}
```

### éç½®é¡¹è¯´æ?
| éç½®é¡?| ç±»å | å¿å¡« | è¯´æ |
|--------|------|------|------|
| name | string | æ?| æå¡å¨åç§?|
| command | string | æ?| å¯å¨å½ä»¤ |
| args | array | å?| å½ä»¤åæ° |
| env | object | å?| ç¯å¢åé |
| transport | string | æ?| ä¼ è¾æ¹å¼: stdio, sse |
| url | string | å?| SSEæå¡å¨URL |
| description | string | å?| æè¿°ä¿¡æ¯ |

### å¸¸ç¨MCPæå¡å?
| æå¡å?| å½ä»¤ | åè½ |
|--------|------|------|
| filesystem | npx @modelcontextprotocol/server-filesystem | æä»¶ç³»ç»è®¿é® |
| sqlite | uvx mcp-server-sqlite | SQLiteæ°æ®åº?|
| fetch | uvx mcp-server-fetch | ç½ç»è¯·æ± |
| git | uvx mcp-server-git | Gitæä½ |
| github | npx @modelcontextprotocol/server-github | GitHub API |
| postgres | npx @modelcontextprotocol/server-postgres | PostgreSQL |

---

## Todoç³»ç»éç½®

éç½®æä»¶è·¯å¾: `config/todo.yaml`

### éç½®ç»æ

```yaml
todo:
  # åæéç½?  reflection:
    min_rounds: 2              # æå°åæè½®æ?    max_rounds: 5              # æå¤åæè½®æ?    auto_generate: true        # èªå¨çæåæåå®?    llm_model: "balanced"      # ç¨äºçæåæçæ¨¡å
  
  # éªæ¶éç½®
  verification:
    auto_create: true          # èªå¨åå»ºéªæ¶ææ¡£
    auto_verify: true          # ä»»å¡å®æåèªå¨éªæ?    format: "markdown"         # éªæ¶ææ¡£æ ¼å¼
    template: "default"        # éªæ¶ææ¡£æ¨¡æ¿
  
  # èªå¨æ´æ°éç½®
  auto_update:
    enabled: true              # å¯ç¨èªå¨æ´æ°
    cascade: true              # çº§èæ´æ°ï¼æ­¥éª¤âä»»å¡âé¶æ®µï¼
    verify_on_complete: true   # å®ææ¶èªå¨éªæ?  
  # å­å¨éç½®
  storage:
    data_dir: "data/todo"
    verification_dir: "data/todo/verifications"
    auto_save: true
    save_interval: 300         # èªå¨ä¿å­é´é(ç§?
  
  # éç¥éç½®
  notification:
    on_phase_complete: true    # é¶æ®µå®æéç¥
    on_task_complete: true     # ä»»å¡å®æéç¥
    on_step_complete: false    # æ­¥éª¤å®æéç¥
```

### éç½®é¡¹è¯´æ?
| éç½®é¡?| ç±»å | é»è®¤å?| è¯´æ |
|--------|------|--------|------|
| reflection.min_rounds | int | 2 | é¶æ®µå®æåæå°åæè½®æ?|
| reflection.max_rounds | int | 5 | é¶æ®µå®æåæå¤åæè½®æ?|
| verification.auto_create | bool | true | åå»ºä»»å¡æ¶èªå¨åå»ºéªæ¶ææ¡?|
| auto_update.cascade | bool | true | å¯ç¨çº§èæ´æ°æºå¶ |
| storage.auto_save | bool | true | èªå¨ä¿å­æ°æ® |

---

## Mateæ¨¡å¼éç½®

éç½®æä»¶è·¯å¾: `config/mate.yaml`

### éç½®ç»æ

```yaml
mate_mode:
  # åºæ¬éç½®
  enabled: false               # é»è®¤æ¯å¦å¯ç¨
  max_reflection_rounds: 3     # æå¤§åæè½®æ?  
  # é¢æ¨çåæéç½?  pre_reasoning:
    enabled: true              # æ¯å¦å¯ç¨é¢æ¨çåæ?    min_rounds: 2              # æå°åæè½®æ?    max_rounds: 3              # æå¤åæè½®æ?    depth: "deep"              # åææ·±åº? shallow/medium/deep
  
  # æ¨çæ¾ç¤ºéç½®
  display:
    show_reasoning: true       # æ¾ç¤ºæ¨çè¿ç¨
    show_reflections: true     # æ¾ç¤ºåæè¿ç¨?    format: "structured"       # æ¾ç¤ºæ ¼å¼: simple/structured/detailed
    real_time: true            # å®æ¶æ¾ç¤º
  
  # WebSocketéç½®
  websocket:
    enabled: true              # å¯ç¨WebSocketæ¨é?    broadcast_reasoning: true  # å¹¿æ­æ¨çæ­¥éª¤
    broadcast_reflections: true # å¹¿æ­åæåå®?  
  # å­å¨éç½®
  storage:
    save_reasoning: true       # ä¿å­æ¨çé?    save_reflections: true     # ä¿å­åæè®°å½?    max_history: 100           # æå¤§åå²è®°å½æ°
```

### éç½®é¡¹è¯´æ?
| éç½®é¡?| ç±»å | é»è®¤å?| è¯´æ |
|--------|------|--------|------|
| enabled | bool | false | é»è®¤æ¯å¦å¯ç¨Mateæ¨¡å¼ |
| max_reflection_rounds | int | 3 | åæ¬¡æ¨çæå¤§åæè½®æ?|
| pre_reasoning.enabled | bool | true | æ¯å¦å¯ç¨é¢æ¨çåæ?|
| display.show_reasoning | bool | true | æ¯å¦æ¾ç¤ºæ¨çè¿ç¨ |
| websocket.enabled | bool | true | æ¯å¦å¯ç¨WebSocketæ¨é?|

---

## è®°å¿ç³»ç»éç½®

éç½®æä»¶è·¯å¾: `config/memory.yaml`

### èå¤©è®°å¿éç½®

```yaml
memory:
  chat:
    data_dir: "data/memory/chat"
    
    # æ´çéç½®
    consolidation:
      daily_to_weekly:
        enabled: true
        interval_days: 7
        min_entries: 5           # æå°æ¡ç®æ°ææ´ç?      weekly_to_monthly:
        enabled: true
        interval_weeks: 4
        min_entries: 3
      monthly_to_quarterly:
        enabled: true
        interval_months: 3
        min_entries: 2
    
    # å¬åéç½®
    recall:
      max_entries_per_level: 50
      include_metadata: true
      sort_by_importance: true
    
    # æç´¢éç½®
    search:
      default_limit: 20
      fuzzy_match: true
      min_score: 0.5
```

### å·¥ä½è®°å¿éç½®

```yaml
memory:
  work:
    data_dir: "data/memory/work"
    
    # é¡¹ç®è®°å¿éç½®
    project:
      max_memories_per_domain: 100
      default_decay_rate: 0.05   # é»è®¤è¡°åç?æ¯å¤©)
      cleanup_interval_days: 30  # æ¸çé´é(å¤?
      
      # è®°å¿ç±»åæé
      type_weights:
        fact: 1.0
        code: 1.2
        decision: 1.5
        issue: 1.3
    
    # åå¥½è®°å¿éç½®
    preference:
      max_preferences: 50
      categories:
        - general
        - coding
        - communication
        - workflow
      auto_add_to_prompt: true   # èªå¨å å¥ç³»ç»æç¤ºè¯?    
    # è¡°åéç½®
    decay:
      enabled: true
      thresholds:
        delete: 0.1              # ä½äºæ­¤å¼å é?        demote: 0.3              # ä½äºæ­¤å¼éçº?      
      # ä¼åçº§è¡°åç
      rates:
        permanent: 0.0           # æ°¸ä¹è®°å¿ä¸è¡°å?        high: 0.03
        medium: 0.05
        low: 0.1
```

### éç½®é¡¹è¯´æ?
| éç½®é¡?| ç±»å | é»è®¤å?| è¯´æ |
|--------|------|--------|------|
| chat.consolidation.enabled | bool | true | å¯ç¨è®°å¿æ´ç |
| work.project.max_memories_per_domain | int | 100 | æ¯ä¸ªåæå¤§è®°å¿æ° |
| work.project.default_decay_rate | float | 0.05 | é»è®¤è®°å¿è¡°åç?|
| work.preference.auto_add_to_prompt | bool | true | èªå¨æ·»å åå¥½å°æç¤ºè¯ |
| work.decay.enabled | bool | true | å¯ç¨è®°å¿è¡°å |

---

## èªæå­¦ä¹ éç½®

éç½®æä»¶è·¯å¾: `config/self_learning.yaml`

### éç½®ç»æ

```yaml
self_learning:
  # è¡¨è¾¾å­¦ä¹ éç½®
  expression:
    enabled: true
    
    # å­¦ä¹ éå?    thresholds:
      min_occurrences: 3       # æå°åºç°æ¬¡æ?      min_confidence: 0.7      # æå°ç½®ä¿¡åº¦
    
    # å­å¨éç½®
    storage:
      max_expressions: 200     # æå¤§è¡¨è¾¾æ°
      save_interval: 3600      # ä¿å­é´é(ç§?
    
    # å¹ééç½®
    matching:
      similarity_threshold: 0.8  # ç¸ä¼¼åº¦éå?      max_matches: 5             # æå¤§å¹éæ°
  
  # é»è¯å­¦ä¹ éç½®
  jargon:
    enabled: true
    
    # æ¸è¿å¼å­¦ä¹ éå?    thresholds:
      initial: 3               # åæ­¥è¯å«
      infer: 6                 # å°è¯æ¨æ­å«ä¹
      confirm: 10              # ç¡®è®¤å«ä¹
      complete: 100            # å®æå­¦ä¹ 
    
    # æ¨æ­éç½®
    inference:
      enabled: true
      use_llm: true            # ä½¿ç¨LLMæ¨æ­å«ä¹
      model: "balanced"        # ä½¿ç¨çæ¨¡å?    
    # å­å¨éç½®
    storage:
      max_entries: 500         # æå¤§é»è¯æ¡ç®æ°
      auto_save: true
  
  # å­¦ä¹ æ¨¡å¼
  mode:
    auto_learn: true           # èªå¨å­¦ä¹ 
    manual_review: false       # æå¨å®¡æ ¸
    feedback_loop: true        # åé¦å¾ªç¯
```

### éç½®é¡¹è¯´æ?
| éç½®é¡?| ç±»å | é»è®¤å?| è¯´æ |
|--------|------|--------|------|
| expression.enabled | bool | true | å¯ç¨è¡¨è¾¾å­¦ä¹  |
| expression.thresholds.min_occurrences | int | 3 | æå°åºç°æ¬¡æ°æå­¦ä¹  |
| jargon.enabled | bool | true | å¯ç¨é»è¯å­¦ä¹  |
| jargon.thresholds.initial | int | 3 | åæ­¥è¯å«éå?|
| jargon.thresholds.complete | int | 100 | å®æå­¦ä¹ éå?|
| mode.auto_learn | bool | true | èªå¨å­¦ä¹ æ¨¡å¼ |

---

## IMå¹³å°éç½®

### OneBotéç½®

```yaml
# config/onebot.yaml
enabled: true
ws_url: ws://127.0.0.1:3001
access_token: your_token
platform: qq
heartbeat_interval: 30
reconnect_interval: 5
```

### éééç½®

```yaml
# config/dingtalk.yaml
enabled: true
webhook_url: https://oapi.dingtalk.com/robot/send?access_token=xxx
secret: your_secret
at_all: false
```

### é£ä¹¦éç½®

```yaml
# config/feishu.yaml
enabled: true
app_id: cli_xxxxxxxx
app_secret: xxxxxxxx
encrypt_key: optional
verification_token: optional
```

### ä¼ä¸å¾®ä¿¡éç½®

```yaml
# config/wecom.yaml
enabled: true
corp_id: wwxxxxxxxxxxxxxxxx
agent_id: 1000002
secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
token: optional
encoding_aes_key: optional
```

---

## ç³»ç»éç½®

### Chat Agentéç½®

```yaml
# config/chat.yaml
chat:
  heart_flow:
    planner_smooth: 0.5        # è§åå¨å¹³æ»æ¶é?ç§?
    talk_value: 0.5            # åè¨ææ¿å?0-1)
    max_context_size: 50       # æå¤§ä¸ä¸æå¤§å°
    
  action_planner:
    max_plan_history: 20       # æå¤§è§ååå²è®°å½æ°
    
  frequency_control:
    enabled: true
    min_interval: 10           # æå°åè¨é´é(ç§?
    max_daily_messages: 1000   # æ¯æ¥æå¤§æ¶æ¯æ°
```

### Executor Agentéç½®

```yaml
# config/executor.yaml
executor:
  react_engine:
    max_iterations: 10         # æå¤§è¿­ä»£æ¬¡æ?    max_tool_calls_per_step: 3 # æ¯æ­¥æå¤§å·¥å·è°ç¨æ°
    enable_loop_detection: true
    enable_tool_jitter_detection: true
    
  task_queue:
    max_concurrent_tasks: 5    # æå¤§å¹¶åä»»å¡æ°
    default_timeout: 300       # é»è®¤è¶æ¶æ¶é´(ç§?
```

### å®å¨éç½®

```yaml
# config/security.yaml
security:
  policy:
    enable_content_filter: true
    blocked_keywords:
      - "ææè¯?"
      - "ææè¯?"
    max_message_length: 2000
    
  rate_limit:
    enabled: true
    requests_per_minute: 60
    
  access_control:
    enabled: false
    whitelist: []
    blacklist: []
```

---

## éç½®å è½½ä¼åçº?
éç½®å è½½æä»¥ä¸ä¼åçº§ï¼é«å°ä½ï¼ï¼

1. ä»£ç ä¸­çé»è®¤å?2. éç½®æä»¶
3. ç¯å¢åé
4. è¿è¡æ¶åæ?
---

## éç½®éªè¯

å¯å¨æ¶ä¼èªå¨éªè¯éç½®ï¼å¸¸è§éè¯¯ï¼

| éè¯¯ | åå  | è§£å³ |
|------|------|------|
| No API keys found | æªéç½®ä»»ä½LLM APIå¯é¥ | æ£æ?envæä»¶ |
| Invalid model config | æ¨¡åéç½®æ ¼å¼éè¯¯ | æ£æ¥models.yaml |
| MCP config not found | MCPéç½®æä»¶ä¸å­å?| åå»ºconfig/mcp.json |
| Todo config error | Todoéç½®éè¯¯ | æ£æ¥config/todo.yaml |
| Memory config error | è®°å¿éç½®éè¯¯ | æ£æ¥config/memory.yaml |
