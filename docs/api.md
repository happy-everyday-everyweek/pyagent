# PyAgent API ææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»æè¿°PyAgent v0.8.0æä¾çææAPIæ¥å£ã?
---

## ç®å½

- [æ¦è¿°](#æ¦è¿°)
- [REST API](#rest-api)
- [WebSocket API](#websocket-api)
- [Todo API](#todo-api)
- [ææ¡£API](#ææ¡£api)
- [è§é¢API](#è§é¢api)
- [åç³»ç»API](#åç³»ç»api)
- [ä»»å¡ç®¡çAPI](#ä»»å¡ç®¡çapi)
- [MCPæå¡å¨API](#mcpæå¡å¨api)
- [æè½API](#æè½api)
- [ç­æ´æ°API](#ç­æ´æ°api)
- [æ°æ®æ¨¡å](#æ°æ®æ¨¡å)
- [éè¯¯å¤ç](#éè¯¯å¤ç)

---

## æ¦è¿°

PyAgentæä¾ä»¥ä¸ç±»åçAPIï¼?
- **REST API**: æ åçHTTPæ¥å£ï¼ç¨äºå¤§é¨åæä½
- **WebSocket API**: å®æ¶éä¿¡æ¥å£ï¼ç¨äºèå¤©åå®æ¶æ´æ°
- **SSE (Server-Sent Events)**: æå¡å¨æ¨éæ¥å£ï¼å¯éï¼

åºç¡URL: `http://localhost:8000`

---

## REST API

### 1. ç³»ç»æ¥å£

#### 1.1 å¥åº·æ£æ?
```http
GET /
```

**ååºç¤ºä¾**:
```json
{
  "message": "PyAgent API",
  "version": "0.8.0",
  "status": "healthy",
  "timestamp": "2026-04-03T10:00:00Z"
}
```

#### 1.2 ç³»ç»ç¶æ?
```http
GET /health
```

**ååºç¤ºä¾**:
```json
{
  "status": "healthy",
  "components": {
    "llm": "connected",
    "memory": "active",
    "todo": "active"
  },
  "uptime": 3600
}
```

---

### 2. èå¤©æ¥å£

#### 2.1 åéæ¶æ?
```http
POST /api/chat
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| message | string | æ?| æ¶æ¯åå®¹ |
| chat_id | string | å?| èå¤©IDï¼é»è®?default" |
| platform | string | å?| å¹³å°æ è¯ï¼é»è®?web" |
| context | object | å?| ä¸ä¸æä¿¡æ?|

**è¯·æ±ç¤ºä¾**:
```json
{
  "message": "ä½ å¥½ï¼è¯·ä»ç»ä¸ä¸èªå·?,
  "chat_id": "group_123",
  "platform": "web",
  "context": {
    "user_id": "user_001",
    "session_id": "session_abc"
  }
}
```

**ååºç¤ºä¾**:
```json
{
  "success": true,
  "response": "ä½ å¥½ï¼ææ¯PyAgentï¼ä¸ä¸ªæºè½å©æ?..",
  "chat_id": "group_123",
  "message_id": "msg_xxx",
  "timestamp": 1704067200,
  "actions": [],
  "metadata": {
    "model": "gpt-4o",
    "tokens_used": 150
  }
}
```

#### 2.2 è·åèå¤©åå²

```http
GET /api/chat/{chat_id}/history?limit=50&offset=0
```

**ååºç¤ºä¾**:
```json
{
  "chat_id": "group_123",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "ä½ å¥½",
      "timestamp": 1704067100
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "ä½ å¥½ï¼æä»ä¹å¯ä»¥å¸®å©ä½ çåï¼?,
      "timestamp": 1704067105
    }
  ],
  "total": 100
}
```

---

### 3. éç½®æ¥å£

#### 3.1 è·åéç½®

```http
GET /api/config
```

**ååºç¤ºä¾**:
```json
{
  "models": {
    "base_model": {
      "provider": "openai",
      "model": "gpt-4o",
      "enabled": true
    },
    "tier_models": {
      "strong": { ... },
      "performance": { ... },
      "cost_effective": { ... }
    }
  },
  "features": {
    "mate_mode": false,
    "collaboration_mode": "single"
  }
}
```

#### 3.2 æ´æ°éç½®

```http
PUT /api/config
Content-Type: application/json
```

**è¯·æ±ç¤ºä¾**:
```json
{
  "key": "mate_mode",
  "value": true
}
```

---

## Todo API

### 1. é¶æ®µç®¡ç

#### 1.1 åå»ºé¶æ®µ

```http
POST /api/todo/phases
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| title | string | æ?| é¶æ®µæ é¢ |
| description | string | å?| é¶æ®µæè¿° |
| priority | string | å?| ä¼åçº? critical/high/medium/low |
| min_reflections | int | å?| æå°åæè½®æ°ï¼é»è®¤2 |
| max_reflections | int | å?| æå¤åæè½®æ°ï¼é»è®¤5 |

**è¯·æ±ç¤ºä¾**:
```json
{
  "title": "å¼åæ°åè½",
  "description": "å®ç°ç¨æ·è¯·æ±çæ°åè½",
  "priority": "high",
  "min_reflections": 2,
  "max_reflections": 5
}
```

**ååºç¤ºä¾**:
```json
{
  "id": "phase_abc123",
  "title": "å¼åæ°åè½",
  "description": "å®ç°ç¨æ·è¯·æ±çæ°åè½",
  "status": "pending",
  "priority": "high",
  "tasks": [],
  "reflections": [],
  "reflection_count": 0,
  "min_reflections": 2,
  "max_reflections": 5,
  "created_at": 1704067200,
  "progress": 0
}
```

#### 1.2 ååºé¶æ®µ

```http
GET /api/todo/phases?status=pending&priority=high
```

**æ¥è¯¢åæ°**:

| åæ° | ç±»å | è¯´æ |
|------|------|------|
| status | string | å¯éï¼è¿æ»¤ç¶æ? pending/active/completed |
| priority | string | å¯éï¼è¿æ»¤ä¼åçº?|

**ååºç¤ºä¾**:
```json
{
  "phases": [
    {
      "id": "phase_abc123",
      "title": "å¼åæ°åè½",
      "status": "pending",
      "priority": "high",
      "progress": 0.5,
      "task_count": 5,
      "completed_tasks": 2
    }
  ],
  "total": 10
}
```

#### 1.3 è·åé¶æ®µè¯¦æ

```http
GET /api/todo/phases/{phase_id}
```

**ååºç¤ºä¾**:
```json
{
  "id": "phase_abc123",
  "title": "å¼åæ°åè½",
  "description": "å®ç°ç¨æ·è¯·æ±çæ°åè½",
  "status": "completed",
  "priority": "high",
  "tasks": [...],
  "reflections": [...],
  "reflection_count": 3,
  "completed_at": 1704153600,
  "progress": 1.0
}
```

#### 1.4 æ´æ°é¶æ®µ

```http
PUT /api/todo/phases/{phase_id}
Content-Type: application/json
```

**è¯·æ±ç¤ºä¾**:
```json
{
  "title": "æ°æ é¢?,
  "description": "æ°æè¿?,
  "priority": "medium"
}
```

#### 1.5 å é¤é¶æ®µ

```http
DELETE /api/todo/phases/{phase_id}
```

---

### 2. ä»»å¡ç®¡ç

#### 2.1 åå»ºä»»å¡

```http
POST /api/todo/tasks
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| phase_id | string | æ?| æå±é¶æ®µID |
| title | string | æ?| ä»»å¡æ é¢ |
| description | string | å?| ä»»å¡æè¿° |
| priority | string | å?| ä¼åçº?|
| steps | array | å?| æ­¥éª¤åå®¹åè¡¨ |

**è¯·æ±ç¤ºä¾**:
```json
{
  "phase_id": "phase_abc123",
  "title": "å®ç°æ ¸å¿åè½",
  "description": "å®ç°åè½çæ ¸å¿é»è¾",
  "priority": "high",
  "steps": [
    "è®¾è®¡æ°æ®æ¨¡å",
    "å®ç°ä¸å¡é»è¾",
    "ç¼åååæµè¯"
  ]
}
```

**ååºç¤ºä¾**:
```json
{
  "id": "task_def456",
  "phase_id": "phase_abc123",
  "title": "å®ç°æ ¸å¿åè½",
  "description": "å®ç°åè½çæ ¸å¿é»è¾",
  "status": "pending",
  "priority": "high",
  "steps": [...],
  "progress": 0,
  "verification_document": {
    "id": "verify_xxx",
    "title": "éªæ¶ææ¡£: å®ç°æ ¸å¿åè½",
    "acceptance_criteria": [...]
  },
  "created_at": 1704067200
}
```

#### 2.2 è·åä»»å¡è¯¦æ

```http
GET /api/todo/tasks/{task_id}
```

#### 2.3 æ´æ°ä»»å¡

```http
PUT /api/todo/tasks/{task_id}
Content-Type: application/json
```

#### 2.4 å é¤ä»»å¡

```http
DELETE /api/todo/tasks/{task_id}
```

---

### 3. æ­¥éª¤ç®¡ç

#### 3.1 åå»ºæ­¥éª¤

```http
POST /api/todo/steps
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| task_id | string | æ?| æå±ä»»å¡ID |
| content | string | æ?| æ­¥éª¤åå®¹ |
| priority | string | å?| ä¼åçº?|
| dependencies | array | å?| ä¾èµæ­¥éª¤IDåè¡¨ |

#### 3.2 æ´æ°æ­¥éª¤ç¶æ?
```http
PUT /api/todo/steps/{step_id}/status
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| status | string | æ?| ç¶æ? pending/in_progress/completed/blocked/skipped |

**ååºç¤ºä¾**:
```json
{
  "success": true,
  "step_id": "step_xxx",
  "status": "completed",
  "updated_at": 1704067200
}
```

#### 3.3 å®ææ­¥éª¤

```http
POST /api/todo/steps/{step_id}/complete
```

**è¯´æ**: å®ææ­¥éª¤å¹¶èªå¨è§¦åä»»å¡åé¶æ®µç¶ææ´æ?
**ååºç¤ºä¾**:
```json
{
  "success": true,
  "step_id": "step_xxx",
  "task_progress": 75.0,
  "task_completed": false,
  "phase_progress": 0.5,
  "cascade_updated": true
}
```

---

### 4. ç»è®¡ä¿¡æ¯

#### 4.1 è·åç»è®¡

```http
GET /api/todo/statistics
```

**ååºç¤ºä¾**:
```json
{
  "total_phases": 5,
  "total_tasks": 12,
  "total_steps": 35,
  "completed_phases": 2,
  "completed_tasks": 8,
  "completed_steps": 28,
  "progress": {
    "phases": 0.4,
    "tasks": 0.67,
    "steps": 0.8
  },
  "by_priority": {
    "critical": { "total": 2, "completed": 1 },
    "high": { "total": 5, "completed": 3 },
    "medium": { "total": 8, "completed": 4 },
    "low": { "total": 2, "completed": 0 }
  }
}
```

#### 4.2 è·åTodoåè¡¨

```http
GET /api/todo/list
```

**ååºç¤ºä¾**:
```json
{
  "content": "# Todo List\n\n## [>] å¼åæ°åè½ (50%)\n...",
  "format": "markdown"
}
```

---

## ææ¡£API

### 1. ææ¡£ç®¡ç

#### 1.1 åå»ºææ¡£

```http
POST /api/documents
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| type | string | æ?| ææ¡£ç±»å: word/excel/ppt |
| title | string | æ?| ææ¡£æ é¢ |
| template | string | å?| æ¨¡æ¿ID |

**è¯·æ±ç¤ºä¾**:
```json
{
  "type": "word",
  "title": "æçææ¡£",
  "template": "default"
}
```

**ååºç¤ºä¾**:
```json
{
  "id": "doc_abc123",
  "type": "word",
  "title": "æçææ¡£",
  "edit_url": "http://localhost:8000/documents/doc_abc123/edit",
  "created_at": 1704067200,
  "status": "active"
}
```

#### 1.2 è·åææ¡£

```http
GET /api/documents/{document_id}
```

**ååºç¤ºä¾**:
```json
{
  "id": "doc_abc123",
  "type": "word",
  "title": "æçææ¡£",
  "content_url": "http://localhost:8000/documents/doc_abc123/content",
  "edit_url": "http://localhost:8000/documents/doc_abc123/edit",
  "version": 1,
  "created_at": 1704067200,
  "updated_at": 1704067200
}
```

#### 1.3 ååºææ¡£

```http
GET /api/documents?type=word&status=active
```

**ååºç¤ºä¾**:
```json
{
  "documents": [
    {
      "id": "doc_abc123",
      "type": "word",
      "title": "æçææ¡£",
      "status": "active",
      "updated_at": 1704067200
    }
  ],
  "total": 10
}
```

#### 1.4 å é¤ææ¡£

```http
DELETE /api/documents/{document_id}
```

---

### 2. AIè¾å©åè½

#### 2.1 AIæ¹å

```http
POST /api/documents/{document_id}/ai/rewrite
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| paragraph_id | string | æ?| æ®µè½ID |
| style | string | å?| é£æ ¼: formal/casual/concise/expanded |

**è¯·æ±ç¤ºä¾**:
```json
{
  "paragraph_id": "p_1",
  "style": "formal"
}
```

**ååºç¤ºä¾**:
```json
{
  "original": "åæåå®¹",
  "suggestions": [
    "æ¹åå»ºè®®1",
    "æ¹åå»ºè®®2",
    "æ¹åå»ºè®®3"
  ],
  "style": "formal"
}
```

#### 2.2 AIç¿»è¯

```http
POST /api/documents/{document_id}/ai/translate
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| target_language | string | æ?| ç®æ è¯­è¨: en/zh/ja/koç­?|
| source_language | string | å?| æºè¯­è¨ï¼èªå¨æ£æµï¼ |

#### 2.3 AIæè¦

```http
POST /api/documents/{document_id}/ai/summarize
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| max_length | int | å?| æå¤§é¿åº¦ï¼é»è®¤200 |

---

### 3. ææ¡£å¯¼åº

#### 3.1 å¯¼åºææ¡£

```http
POST /api/documents/{document_id}/export
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| format | string | æ?| æ ¼å¼: pdf/docx/xlsx/pptx/txt |

**ååºç¤ºä¾**:
```json
{
  "download_url": "http://localhost:8000/documents/doc_abc123/export/download?token=xxx",
  "expires_at": 1704070800
}
```

---

## è§é¢API

### 1. é¡¹ç®ç®¡ç

#### 1.1 åå»ºè§é¢é¡¹ç®

```http
POST /api/videos/projects
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| name | string | æ?| é¡¹ç®åç§° |
| resolution | array | å?| åè¾¨ç?[width, height]ï¼é»è®¤[1920, 1080] |
| fps | int | å?| å¸§çï¼é»è®?0 |
| duration | float | å?| æ¶é¿ï¼ç§ï¼?|

**è¯·æ±ç¤ºä¾**:
```json
{
  "name": "æçVlog",
  "resolution": [1920, 1080],
  "fps": 30,
  "duration": 300
}
```

**ååºç¤ºä¾**:
```json
{
  "id": "video_project_abc123",
  "name": "æçVlog",
  "resolution": [1920, 1080],
  "fps": 30,
  "duration": 300,
  "tracks": [],
  "created_at": 1704067200
}
```

#### 1.2 è·åé¡¹ç®

```http
GET /api/videos/projects/{project_id}
```

#### 1.3 ååºé¡¹ç®

```http
GET /api/videos/projects
```

#### 1.4 å é¤é¡¹ç®

```http
DELETE /api/videos/projects/{project_id}
```

---

### 2. è½¨éç®¡ç

#### 2.1 æ·»å è½¨é

```http
POST /api/videos/projects/{project_id}/tracks
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| type | string | æ?| ç±»å: video/audio/text/effect |
| name | string | æ?| è½¨éåç§° |

#### 2.2 å é¤è½¨é

```http
DELETE /api/videos/projects/{project_id}/tracks/{track_id}
```

---

### 3. AIåè½

#### 3.1 AIåæè§é¢

```http
POST /api/videos/ai/analyze
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| video_path | string | æ?| è§é¢æä»¶è·¯å¾ |
| analysis_type | string | å?| åæç±»å: highlights/scenes/audio/all |

**ååºç¤ºä¾**:
```json
{
  "highlights": [
    { "start": 10.5, "end": 25.3, "score": 0.9 },
    { "start": 45.0, "end": 60.0, "score": 0.85 }
  ],
  "scenes": [
    { "start": 0, "end": 30, "type": "intro" },
    { "start": 30, "end": 120, "type": "content" }
  ]
}
```

#### 3.2 çæå­å¹

```http
POST /api/videos/subtitles/generate
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| video_path | string | æ?| è§é¢æä»¶è·¯å¾ |
| language | string | å?| è¯­è¨ï¼é»è®?zh" |
| translate_to | string | å?| ç¿»è¯ç®æ è¯­è¨ |

**ååºç¤ºä¾**:
```json
{
  "subtitles": [
    { "start": 0.5, "end": 3.2, "text": "å¤§å®¶å¥½ï¼æ¬¢è¿è§ç" },
    { "start": 3.5, "end": 6.0, "text": "ä»å¤©æä»¬è¦ä»ç»?.." }
  ],
  "language": "zh",
  "format": "srt"
}
```

#### 3.3 æºè½åªè¾

```http
POST /api/videos/ai/smart-edit
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| project_id | string | æ?| é¡¹ç®ID |
| style | string | å?| åªè¾é£æ ¼: vlog/tutorial/montage |
| target_duration | float | å?| ç®æ æ¶é¿ |

---

### 4. å¯¼åº

#### 4.1 å¯¼åºè§é¢

```http
POST /api/videos/export
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| project_id | string | æ?| é¡¹ç®ID |
| format | string | å?| æ ¼å¼: mp4/mov/webmï¼é»è®¤mp4 |
| quality | string | å?| è´¨é: low/medium/high/ultra |
| resolution | array | å?| è¾åºåè¾¨ç?|

**ååºç¤ºä¾**:
```json
{
  "job_id": "export_job_xxx",
  "status": "processing",
  "progress": 0,
  "estimated_time": 120
}
```

#### 4.2 è·åå¯¼åºç¶æ?
```http
GET /api/videos/export/{job_id}/status
```

**ååºç¤ºä¾**:
```json
{
  "job_id": "export_job_xxx",
  "status": "completed",
  "progress": 100,
  "download_url": "http://localhost:8000/videos/export/export_job_xxx/download",
  "expires_at": 1704070800
}
```

---

## åç³»ç»API

### 1. åç®¡ç?
#### 1.1 åå»ºå?
```http
POST /api/domains
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| name | string | æ?| ååç§?|
| description | string | å?| åæè¿?|

**è¯·æ±ç¤ºä¾**:
```json
{
  "name": "æçå?,
  "description": "ä¸ªäººè®¾å¤å?
}
```

**ååºç¤ºä¾**:
```json
{
  "id": "domain_abc123",
  "name": "æçå?,
  "description": "ä¸ªäººè®¾å¤å?,
  "created_at": 1704067200,
  "device_count": 0
}
```

#### 1.2 è·ååä¿¡æ?
```http
GET /api/domains/{domain_id}
```

**ååºç¤ºä¾**:
```json
{
  "id": "domain_abc123",
  "name": "æçå?,
  "description": "ä¸ªäººè®¾å¤å?,
  "created_at": 1704067200,
  "devices": [
    {
      "id": "device_xxx",
      "name": "å·¥ä½çµè",
      "type": "pc",
      "status": "online",
      "last_sync": 1704067200
    }
  ]
}
```

#### 1.3 ååºå?
```http
GET /api/domains
```

#### 1.4 å é¤å?
```http
DELETE /api/domains/{domain_id}
```

---

### 2. è®¾å¤ç®¡ç

#### 2.1 è®¾å¤å å¥å?
```http
POST /api/domains/{domain_id}/devices/join
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| device_name | string | æ?| è®¾å¤åç§° |
| device_type | string | æ?| ç±»å: pc/mobile/server/edge |
| capabilities | object | å?| è®¾å¤è½å |

**è¯·æ±ç¤ºä¾**:
```json
{
  "device_name": "å·¥ä½çµè",
  "device_type": "pc",
  "capabilities": {
    "cpu_cores": 8,
    "memory_gb": 16,
    "storage_gb": 512,
    "has_gpu": true
  }
}
```

**ååºç¤ºä¾**:
```json
{
  "device_id": "device_xxx",
  "domain_id": "domain_abc123",
  "name": "å·¥ä½çµè",
  "type": "pc",
  "status": "active",
  "joined_at": 1704067200
}
```

#### 2.2 è®¾å¤ç¦»å¼å?
```http
POST /api/domains/{domain_id}/devices/{device_id}/leave
```

#### 2.3 ååºååè®¾å¤

```http
GET /api/domains/{domain_id}/devices
```

---

### 3. æ°æ®åæ­¥

#### 3.1 åæ­¥æ°æ®

```http
POST /api/domains/{domain_id}/sync
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| data_type | string | æ?| æ°æ®ç±»å: memory/todo/config |
| data | object | æ?| åæ­¥æ°æ® |
| sync_mode | string | å?| æ¨¡å¼: realtime/scheduled/manual |

**ååºç¤ºä¾**:
```json
{
  "sync_id": "sync_xxx",
  "status": "completed",
  "conflicts": [],
  "timestamp": 1704067200
}
```

#### 3.2 è·ååæ­¥ç¶æ?
```http
GET /api/domains/{domain_id}/sync/status
```

**ååºç¤ºä¾**:
```json
{
  "domain_id": "domain_abc123",
  "last_sync": 1704067200,
  "sync_mode": "realtime",
  "pending_changes": 0,
  "conflicts": []
}
```

---

## ä»»å¡ç®¡çAPI

### 1. ä»»å¡æä½

#### 1.1 ååºä»»å¡

```http
GET /api/tasks?status=running&limit=20
```

**æ¥è¯¢åæ°**:

| åæ° | ç±»å | è¯´æ |
|------|------|------|
| status | string | è¿æ»¤ç¶æ? pending/running/completed/failed |
| limit | int | è¿åæ°ééå¶ |

**ååºç¤ºä¾**:
```json
{
  "tasks": [
    {
      "task_id": "task_xxx",
      "status": "running",
      "type": "execution",
      "progress": 0.5,
      "created_at": 1704067200
    }
  ],
  "running_count": 5,
  "queue_size": 3
}
```

#### 1.2 è·åä»»å¡è¯¦æ

```http
GET /api/tasks/{task_id}
```

**ååºç¤ºä¾**:
```json
{
  "task_id": "task_xxx",
  "status": "running",
  "type": "execution",
  "progress": 0.5,
  "result": null,
  "error": null,
  "created_at": 1704067200,
  "started_at": 1704067205,
  "estimated_end": 1704067500
}
```

#### 1.3 åæ¶ä»»å¡

```http
POST /api/tasks/{task_id}/cancel
```

#### 1.4 æ§è¡ä»»å¡

```http
POST /api/tasks/{task_id}/execute
Content-Type: application/json
```

---

## MCPæå¡å¨API

### 1. æå¡å¨ç®¡ç?
#### 1.1 ååºMCPæå¡å?
```http
GET /api/mcp/servers
```

**ååºç¤ºä¾**:
```json
{
  "total_servers": 2,
  "connected_servers": 1,
  "total_tools": 5,
  "servers": {
    "filesystem": {
      "connected": true,
      "tool_count": 3,
      "error": null
    },
    "database": {
      "connected": false,
      "tool_count": 0,
      "error": "Connection timeout"
    }
  }
}
```

#### 1.2 è¿æ¥MCPæå¡å?
```http
POST /api/mcp/servers/{server_name}/connect
```

**ååºç¤ºä¾**:
```json
{
  "success": true,
  "error": null,
  "tool_count": 3
}
```

#### 1.3 æ­å¼MCPæå¡å?
```http
POST /api/mcp/servers/{server_name}/disconnect
```

#### 1.4 è·åæå¡å¨å·¥å?
```http
GET /api/mcp/servers/{server_name}/tools
```

---

## æè½API

### 1. æè½ç®¡ç?
#### 1.1 ååºæè?
```http
GET /api/skills
```

**ååºç¤ºä¾**:
```json
{
  "loaded": 3,
  "skills": [
    {
      "id": "file_manager",
      "name": "File Manager",
      "description": "æä»¶ç®¡çæè?,
      "version": "1.0.0",
      "enabled": true
    },
    {
      "id": "web_search",
      "name": "Web Search",
      "description": "ç½ç»æç´¢æè?,
      "version": "1.0.0",
      "enabled": true
    }
  ]
}
```

#### 1.2 å®è£æè?
```http
POST /api/skills/install
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| source | string | æ?| æè½æ¥æº? clawhub://name ææ¬å°è·¯å¾?|

#### 1.3 å¸è½½æè?
```http
DELETE /api/skills/{skill_id}
```

#### 1.4 å¯ç¨/ç¦ç¨æè?
```http
PUT /api/skills/{skill_id}/status
Content-Type: application/json
```

**è¯·æ±ç¤ºä¾**:
```json
{
  "enabled": false
}
```

---

## ç­æ´æ°API

### 1. æ´æ°ç®¡ç

#### 1.1 ä¸ä¼ æ´æ°å?
```http
POST /api/hot-reload/upload
Content-Type: multipart/form-data
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| file | file | æ?| zipæ´æ°å?|
| version | string | å?| çæ¬å?|

**ååºç¤ºä¾**:
```json
{
  "upload_id": "upload_xxx",
  "status": "uploaded",
  "size": 1024000
}
```

#### 1.2 éªè¯æ´æ°å?
```http
POST /api/hot-reload/verify
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| upload_id | string | æ?| ä¸ä¼ ID |

#### 1.3 åºç¨æ´æ°

```http
POST /api/hot-reload/apply
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| upload_id | string | æ?| ä¸ä¼ ID |
| backup | boolean | å?| æ¯å¦å¤ä»½ï¼é»è®¤true |

**ååºç¤ºä¾**:
```json
{
  "update_id": "update_xxx",
  "status": "applied",
  "backup_id": "backup_xxx",
  "requires_restart": false
}
```

#### 1.4 åæ»æ´æ°

```http
POST /api/hot-reload/rollback
Content-Type: application/json
```

**è¯·æ±åæ°**:

| åæ° | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| backup_id | string | æ?| å¤ä»½ID |

---

## WebSocket API

è¿æ¥å°å: `ws://localhost:8000/ws`

### æ¶æ¯æ ¼å¼

æææ¶æ¯ä½¿ç¨JSONæ ¼å¼ã?
### å®¢æ·ç«¯æ¶æ?
#### 1. èå¤©æ¶æ¯

```json
{
  "type": "chat",
  "message": "ä½ å¥½",
  "chat_id": "default",
  "platform": "web"
}
```

**å­æ®µè¯´æ**:

| å­æ®µ | ç±»å | å¿å¡« | è¯´æ |
|------|------|------|------|
| type | string | æ?| æ¶æ¯ç±»åï¼åºå®å?chat" |
| message | string | æ?| æ¶æ¯åå®¹ |
| chat_id | string | å?| èå¤©ID |
| platform | string | å?| å¹³å°æ è¯ |

#### 2. å¿è·³æ¶æ¯

```json
{
  "type": "ping"
}
```

#### 3. è®¢éæ¶æ¯

```json
{
  "type": "subscribe",
  "channel": "task_updates"
}
```

### æå¡ç«¯æ¶æ?
#### 1. ååºæ¶æ¯

```json
{
  "type": "response",
  "message": "ä½ å¥½ï¼ææ¯PyAgentï¼æä»ä¹å¯ä»¥å¸®å©ä½ çåï¼?,
  "chat_id": "default",
  "timestamp": 1704067200,
  "message_id": "msg_xxx"
}
```

#### 2. æµå¼ååº

```json
{
  "type": "stream",
  "chunk": "è¿æ¯",
  "chat_id": "default",
  "is_end": false
}
```

#### 3. ä»»å¡æ´æ°

```json
{
  "type": "task_update",
  "task_id": "task_xxx",
  "status": "running",
  "progress": 0.5,
  "timestamp": 1704067200
}
```

#### 4. å¿è·³ååº

```json
{
  "type": "pong"
}
```

#### 5. éè¯¯æ¶æ¯

```json
{
  "type": "error",
  "message": "Chat agent not initialized",
  "code": "AGENT_NOT_READY",
  "timestamp": 1704067200
}
```

### è¿æ¥ç¤ºä¾ (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected');
  
  // åéæ¶æ?  ws.send(JSON.stringify({
    type: 'chat',
    message: 'ä½ å¥½',
    chat_id: 'default'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'response':
      console.log('Response:', data.message);
      break;
    case 'stream':
      process.stdout.write(data.chunk);
      if (data.is_end) console.log();
      break;
    case 'task_update':
      console.log('Task progress:', data.progress);
      break;
    case 'error':
      console.error('Error:', data.message);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};

// å¿è·³
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

---

## æ°æ®æ¨¡å

### ChatRequest

èå¤©è¯·æ±æ¨¡åã?
```typescript
interface ChatRequest {
  message: string;           // æ¶æ¯åå®¹
  chat_id?: string;          // èå¤©IDï¼é»è®?default"
  platform?: string;         // å¹³å°æ è¯ï¼é»è®?web"
  context?: object;          // ä¸ä¸æä¿¡æ?}
```

### ChatResponse

èå¤©ååºæ¨¡åã?
```typescript
interface ChatResponse {
  success: boolean;          // æ¯å¦æå
  response: string;          // ååºåå®¹
  chat_id: string;           // èå¤©ID
  message_id: string;        // æ¶æ¯ID
  timestamp: number;         // æ¶é´æ?  actions: Action[];         // æ§è¡çå¨ä½åè¡?  metadata?: object;         // åæ°æ?}
```

### TodoPhase

é¶æ®µæ¨¡åã?
```typescript
interface TodoPhase {
  id: string;                // é¶æ®µID
  title: string;             // æ é¢
  description: string;       // æè¿°
  status: TodoStatus;        // ç¶æ?  priority: TodoPriority;    // ä¼åçº?  tasks: TodoTask[];         // ä»»å¡åè¡¨
  reflections: ReflectionResult[];  // åæç»æ?  reflection_count: number;  // åææ¬¡æ?  min_reflections: number;   // æå°åæè½®æ?  max_reflections: number;   // æå¤åæè½®æ?  created_at: number;        // åå»ºæ¶é´
  completed_at?: number;     // å®ææ¶é´
  progress: number;          // è¿åº¦ 0-1
}
```

### TodoTask

ä»»å¡æ¨¡åã?
```typescript
interface TodoTask {
  id: string;                // ä»»å¡ID
  phase_id: string;          // æå±é¶æ®µID
  title: string;             // æ é¢
  description: string;       // æè¿°
  status: TodoStatus;        // ç¶æ?  priority: TodoPriority;    // ä¼åçº?  steps: TodoStep[];         // æ­¥éª¤åè¡¨
  progress: number;          // è¿åº¦ 0-1
  verification_document?: VerificationDocument;  // éªæ¶ææ¡£
  created_at: number;        // åå»ºæ¶é´
  completed_at?: number;     // å®ææ¶é´
}
```

### TodoStep

æ­¥éª¤æ¨¡åã?
```typescript
interface TodoStep {
  id: string;                // æ­¥éª¤ID
  task_id: string;           // æå±ä»»å¡ID
  content: string;           // åå®¹
  status: TodoStatus;        // ç¶æ?  priority: TodoPriority;    // ä¼åçº?  dependencies: string[];    // ä¾èµæ­¥éª¤ID
  created_at: number;        // åå»ºæ¶é´
  completed_at?: number;     // å®ææ¶é´
}
```

### Document

ææ¡£æ¨¡åã?
```typescript
interface Document {
  id: string;                // ææ¡£ID
  type: 'word' | 'excel' | 'ppt';  // ææ¡£ç±»å
  title: string;             // æ é¢
  content_url: string;       // åå®¹URL
  edit_url: string;          // ç¼è¾URL
  version: number;           // çæ¬å?  created_at: number;        // åå»ºæ¶é´
  updated_at: number;        // æ´æ°æ¶é´
  status: 'active' | 'archived';  // ç¶æ?}
```

### VideoProject

è§é¢é¡¹ç®æ¨¡åã?
```typescript
interface VideoProject {
  id: string;                // é¡¹ç®ID
  name: string;              // åç§°
  resolution: [number, number];  // åè¾¨ç?[width, height]
  fps: number;               // å¸§ç
  duration: number;          // æ¶é¿ï¼ç§ï¼?  tracks: VideoTrack[];      // è½¨éåè¡¨
  created_at: number;        // åå»ºæ¶é´
  updated_at: number;        // æ´æ°æ¶é´
}
```

### Domain

åæ¨¡åã?
```typescript
interface Domain {
  id: string;                // åID
  name: string;              // åç§°
  description: string;       // æè¿°
  devices: Device[];         // è®¾å¤åè¡¨
  created_at: number;        // åå»ºæ¶é´
  updated_at: number;        // æ´æ°æ¶é´
}
```

### Device

è®¾å¤æ¨¡åã?
```typescript
interface Device {
  id: string;                // è®¾å¤ID
  domain_id: string;         // æå±åID
  name: string;              // åç§°
  type: 'pc' | 'mobile' | 'server' | 'edge';  // ç±»å
  capabilities: DeviceCapabilities;  // è½å
  status: 'online' | 'offline' | 'syncing';  // ç¶æ?  last_sync?: number;        // æååæ­¥æ¶é?  joined_at: number;         // å å¥æ¶é´
}
```

---

## éè¯¯å¤ç

### HTTPç¶æç 

| ç¶æç  | è¯´æ |
|--------|------|
| 200 | è¯·æ±æå |
| 400 | è¯·æ±åæ°éè¯¯ |
| 401 | æªææ?|
| 403 | ç¦æ­¢è®¿é® |
| 404 | èµæºä¸å­å?|
| 422 | è¯·æ±ä½æ ¼å¼éè¯?|
| 429 | è¯·æ±è¿äºé¢ç¹ |
| 500 | æå¡å¨åé¨éè¯?|
| 503 | æå¡æªå°±ç»?|

### éè¯¯ååºæ ¼å¼

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "éè¯¯æè¿°ä¿¡æ¯",
    "details": {},
    "timestamp": 1704067200
  }
}
```

### å¸¸è§éè¯¯ç ?
| éè¯¯ç ?| è¯´æ | è§£å³æ¹æ¡ |
|--------|------|----------|
| AGENT_NOT_READY | èå¤©Agentæªåå§å | æ£æ¥æå¡å¯å¨ç¶æ?|
| EXECUTOR_NOT_READY | æ§è¡Agentæªåå§å | æ£æ¥æå¡å¯å¨ç¶æ?|
| PHASE_NOT_FOUND | é¶æ®µä¸å­å?| æ£æ¥é¶æ®µIDæ¯å¦æ­£ç¡® |
| TASK_NOT_FOUND | ä»»å¡ä¸å­å?| æ£æ¥ä»»å¡IDæ¯å¦æ­£ç¡® |
| STEP_NOT_FOUND | æ­¥éª¤ä¸å­å?| æ£æ¥æ­¥éª¤IDæ¯å¦æ­£ç¡® |
| DOMAIN_NOT_FOUND | åä¸å­å¨ | æ£æ¥åIDæ¯å¦æ­£ç¡® |
| DEVICE_NOT_FOUND | è®¾å¤ä¸å­å?| æ£æ¥è®¾å¤IDæ¯å¦æ­£ç¡® |
| DOCUMENT_NOT_FOUND | ææ¡£ä¸å­å?| æ£æ¥ææ¡£IDæ¯å¦æ­£ç¡® |
| VIDEO_PROJECT_NOT_FOUND | è§é¢é¡¹ç®ä¸å­å?| æ£æ¥é¡¹ç®IDæ¯å¦æ­£ç¡® |
| INVALID_REQUEST | è¯·æ±åæ°æ æ | æ£æ¥è¯·æ±åæ?|
| RATE_LIMITED | è¯·æ±è¿äºé¢ç¹ | éä½è¯·æ±é¢ç |
| INTERNAL_ERROR | åé¨éè¯¯ | èç³»ç®¡çå?|

---

## ä½¿ç¨ç¤ºä¾

### Python ç¤ºä¾

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Todoæä½
class TodoClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def create_phase(self, title, **kwargs):
        response = requests.post(
            f"{self.base_url}/api/todo/phases",
            json={"title": title, **kwargs}
        )
        return response.json()
    
    def create_task(self, phase_id, title, **kwargs):
        response = requests.post(
            f"{self.base_url}/api/todo/tasks",
            json={"phase_id": phase_id, "title": title, **kwargs}
        )
        return response.json()
    
    def complete_step(self, step_id):
        response = requests.post(
            f"{self.base_url}/api/todo/steps/{step_id}/complete"
        )
        return response.json()
    
    def get_statistics(self):
        response = requests.get(f"{self.base_url}/api/todo/statistics")
        return response.json()

# ææ¡£æä½
class DocumentClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def create_document(self, doc_type, title):
        response = requests.post(
            f"{self.base_url}/api/documents",
            json={"type": doc_type, "title": title}
        )
        return response.json()
    
    def ai_rewrite(self, doc_id, paragraph_id, style):
        response = requests.post(
            f"{self.base_url}/api/documents/{doc_id}/ai/rewrite",
            json={"paragraph_id": paragraph_id, "style": style}
        )
        return response.json()

# åç³»ç»æä½?class DomainClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def create_domain(self, name, description=""):
        response = requests.post(
            f"{self.base_url}/api/domains",
            json={"name": name, "description": description}
        )
        return response.json()
    
    def join_domain(self, domain_id, device_name, device_type, capabilities):
        response = requests.post(
            f"{self.base_url}/api/domains/{domain_id}/devices/join",
            json={
                "device_name": device_name,
                "device_type": device_type,
                "capabilities": capabilities
            }
        )
        return response.json()

# ä½¿ç¨ç¤ºä¾
if __name__ == "__main__":
    todo = TodoClient(BASE_URL)
    doc = DocumentClient(BASE_URL)
    domain = DomainClient(BASE_URL)
    
    # åå»ºé¶æ®µ
    phase = todo.create_phase(
        "å¼åæ°åè½",
        description="å®ç°AIåè½",
        priority="high"
    )
    
    # åå»ºä»»å¡
    task = todo.create_task(
        phase["id"],
        "å®ç°æ ¸å¿é»è¾",
        steps=["è®¾è®¡", "ç¼ç ", "æµè¯"]
    )
    
    # åå»ºææ¡£
    document = doc.create_document("word", "é¡¹ç®ææ¡£")
    print(f"ç¼è¾URL: {document['edit_url']}")
    
    # åå»ºå?    domain_info = domain.create_domain("æçå?, "ä¸ªäººè®¾å¤å?)
    print(f"åID: {domain_info['id']}")
```

### cURL ç¤ºä¾

```bash
# åå»ºé¶æ®µ
curl -X POST http://localhost:8000/api/todo/phases \
  -H "Content-Type: application/json" \
  -d '{"title": "å¼åæ°åè½", "priority": "high"}'

# å®ææ­¥éª¤
curl -X POST http://localhost:8000/api/todo/steps/step_xxx/complete

# è·åç»è®¡
curl http://localhost:8000/api/todo/statistics

# åå»ºææ¡£
curl -X POST http://localhost:8000/api/documents \
  -H "Content-Type: application/json" \
  -d '{"type": "word", "title": "æçææ¡£"}'

# åå»ºå?curl -X POST http://localhost:8000/api/domains \
  -H "Content-Type: application/json" \
  -d '{"name": "æçå?, "description": "ä¸ªäººè®¾å¤å?}'

# è®¾å¤å å¥å?curl -X POST http://localhost:8000/api/domains/domain_xxx/devices/join \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "å·¥ä½çµè",
    "device_type": "pc",
    "capabilities": {"cpu_cores": 8, "memory_gb": 16}
  }'
```

---

## éçéå¶

å½åçæ¬ææªå®ç°éçéå¶ãå»ºè®®å®¢æ·ç«¯èªè¡æ§å¶è¯·æ±é¢çï¼é¿åå¯¹æå¡å¨é æè¿å¤§ååã?
---

## è®¤è¯

å½åçæ¬APIä¸ºå¼æ¾è®¿é®ï¼æ éè®¤è¯ãçäº§ç¯å¢å»ºè®®æ·»å ï¼
- API Keyè®¤è¯
- JWT Tokenè®¤è¯
- IPç½åå?
---

**PyAgent API v0.8.0 - è®©AIæ´æºè½ï¼è®©åä½æ´é«æ**
