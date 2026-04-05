# PyAgent 语音交互系统

**版本**: v0.8.0  
**模块路径**: `src/voice/`  
**最后更新**: 2025-04-03

---

## 概述

语音交互系统是 PyAgent v0.8.0 引入的全新模块，提供语音识别（ASR）和语音合成（TTS）功能。支持多种中文语音识别服务（Whisper、百度、阿里）和语音合成服务（Edge TTS、百度、阿里），实现自然流畅的语音交互体验。

### 核心特性

- **多 ASR 引擎**: 支持 Whisper、百度、阿里等多种语音识别服务
- **多 TTS 引擎**: 支持 Edge TTS、百度、阿里等多种语音合成服务
- **实时语音处理**: 支持流式语音识别和合成
- **多语言支持**: 支持中文、英文、日文、韩文等多种语言
- **语音活动检测**: 自动检测语音开始和结束
- **热词优化**: 支持自定义热词提升识别准确率

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                   Voice Interaction System                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   ASR Module    │    │   TTS Module    │                 │
│  │  (语音识别)      │    │  (语音合成)      │                 │
│  │                 │    │                 │                 │
│  │  ┌───────────┐  │    │  ┌───────────┐  │                 │
│  │  │ Whisper   │  │    │  │ Edge TTS  │  │                 │
│  │  │ 百度      │  │    │  │ 百度      │  │                 │
│  │  │ 阿里      │  │    │  │ 阿里      │  │                 │
│  │  └───────────┘  │    │  └───────────┘  │                 │
│  └────────┬────────┘    └────────┬────────┘                 │
│           │                       │                          │
│           └───────────┬───────────┘                          │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Voice Processor                        │    │
│  │         (实时语音流处理)                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 语音识别 (ASR)

**位置**: `src/voice/asr.py`

```python
from src.voice.asr import ASRModule, ASRConfig

# 创建 ASR 实例
config = ASRConfig(
    language="zh-CN",
    model="default",
    enable_vad=True,
    vad_threshold=0.5,
    sample_rate=16000,
)
asr = ASRModule(config)

# 初始化
asr.initialize()
```

#### ASRConfig 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `language` | str | "zh-CN" | 识别语言 |
| `model` | str | "default" | 模型名称 |
| `enable_vad` | bool | True | 启用语音活动检测 |
| `vad_threshold` | float | 0.5 | VAD 阈值 |
| `sample_rate` | int | 16000 | 采样率 |

#### 主要方法

```python
# 识别音频数据
text = await asr.transcribe(audio_data: bytes) -> str

# 识别音频文件
text = await asr.transcribe_file(file_path: str) -> str

# 流式识别
async for text in asr.transcribe_stream(audio_stream):
    print(text)

# 设置语言
asr.set_language("en-US")

# 添加热词
asr.add_hotwords({"PyAgent": 0.9, "AI": 0.8})

# 获取支持的语言
languages = asr.get_supported_languages()
```

---

### 2. 语音合成 (TTS)

**位置**: `src/voice/tts.py`

```python
from src.voice.tts import TTSModule, TTSConfig, VoiceInfo

# 创建 TTS 实例
config = TTSConfig(
    voice_id="default",
    speed=1.0,
    pitch=1.0,
    volume=1.0,
    sample_rate=22050,
)
tts = TTSModule(config)

# 初始化
tts.initialize()
```

#### TTSConfig 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `voice_id` | str | "default" | 音色ID |
| `speed` | float | 1.0 | 语速 (0.5-2.0) |
| `pitch` | float | 1.0 | 音调 (0.5-2.0) |
| `volume` | float | 1.0 | 音量 (0.0-1.0) |
| `sample_rate` | int | 22050 | 采样率 |

#### 主要方法

```python
# 合成语音
audio_data = await tts.synthesize(text: str, voice_id: str = None) -> bytes

# 合成并保存到文件
success = await tts.synthesize_to_file(
    text: str,
    file_path: str,
    voice_id: str = None
) -> bool

# 流式合成
async for chunk in tts.stream_synthesize(text: str, chunk_size: int = 1024):
    play_audio(chunk)

# 获取可用音色
voices = tts.get_voices()

# 设置音色
tts.set_voice("female-zh")

# 调整参数
tts.set_speed(1.2)   # 加快语速
tts.set_pitch(0.9)   # 降低音调
tts.set_volume(0.8)  # 降低音量
```

#### 内置音色

| voice_id | 名称 | 语言 | 性别 |
|----------|------|------|------|
| `default` | 默认女声 | zh-CN | female |
| `male-zh` | 中文男声 | zh-CN | male |
| `female-en` | English Female | en-US | female |
| `male-en` | English Male | en-US | male |
| `female-ja` | 日本語女性 | ja-JP | female |
| `female-ko` | 한국어 여성 | ko-KR | female |

---

## 使用示例

### 基础语音识别

```python
import asyncio
from src.voice.asr import ASRModule

async def transcribe_example():
    asr = ASRModule()
    asr.initialize()
    
    # 从文件识别
    text = await asr.transcribe_file("audio.wav")
    print(f"识别结果: {text}")
    
    # 从字节数据识别
    with open("audio.wav", "rb") as f:
        audio_data = f.read()
    text = await asr.transcribe(audio_data)
    print(f"识别结果: {text}")

asyncio.run(transcribe_example())
```

### 基础语音合成

```python
import asyncio
from src.voice.tts import TTSModule

async def synthesize_example():
    tts = TTSModule()
    tts.initialize()
    
    # 合成并保存
    await tts.synthesize_to_file(
        text="你好，我是 PyAgent 语音助手。",
        file_path="output.wav"
    )
    
    # 流式合成
    async for chunk in tts.stream_synthesize("这是一段长文本..."):
        # 播放音频块
        pass

asyncio.run(synthesize_example())
```

### 完整对话示例

```python
import asyncio
from src.voice.asr import ASRModule
from src.voice.tts import TTSModule
from src.llm.client import llm_client

async def voice_conversation():
    # 初始化模块
    asr = ASRModule()
    tts = TTSModule()
    asr.initialize()
    tts.initialize()
    
    print("语音对话已启动，请说话...")
    
    # 1. 语音识别
    print("正在聆听...")
    user_input = await asr.transcribe_file("user_input.wav")
    print(f"用户说: {user_input}")
    
    # 2. AI 处理
    response = await llm_client.chat(
        messages=[{"role": "user", "content": user_input}]
    )
    ai_reply = response["content"]
    print(f"AI 回复: {ai_reply}")
    
    # 3. 语音合成
    print("正在播放回复...")
    await tts.synthesize_to_file(ai_reply, "ai_reply.wav")
    # play_audio("ai_reply.wav")

asyncio.run(voice_conversation())
```

### 多语言支持

```python
from src.voice.asr import ASRModule
from src.voice.tts import TTSModule

asr = ASRModule()
tts = TTSModule()

# 英文识别
asr.set_language("en-US")
text = await asr.transcribe_file("english_audio.wav")

# 日文合成
tts.set_voice("female-ja")
audio = await tts.synthesize("こんにちは")

# 支持的语言
languages = asr.get_supported_languages()
# ['zh-CN', 'zh-TW', 'en-US', 'en-GB', 'ja-JP', 'ko-KR', ...]
```

---

## API 接口

### REST API

#### 语音识别
```http
POST /api/voice/transcribe
Content-Type: multipart/form-data

file: <audio_file.wav>
language: zh-CN
```

#### 语音合成
```http
POST /api/voice/synthesize
Content-Type: application/json

{
  "text": "要合成的文本",
  "voice_id": "default",
  "speed": 1.0,
  "pitch": 1.0,
  "volume": 1.0
}
```

#### 获取可用音色
```http
GET /api/voice/voices
```

---

## 配置选项

```yaml
# config/voice.yaml
voice:
  asr:
    provider: "whisper"  # whisper, baidu, alibaba
    language: "zh-CN"
    model: "base"
    enable_vad: true
    api_key: "${ASR_API_KEY}"
    secret_key: "${ASR_SECRET_KEY}"
  
  tts:
    provider: "edge"  # edge, baidu, alibaba
    voice_id: "default"
    speed: 1.0
    pitch: 1.0
    volume: 1.0
    api_key: "${TTS_API_KEY}"
    secret_key: "${TTS_SECRET_KEY}"
```

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持 ASR 语音识别
- 支持 TTS 语音合成
- 支持多语言
- 支持流式处理

---

## 相关文档

- [LLM 客户端](./llm-client-v2.md) - 语言模型交互
- [API 文档](../api.md) - 完整 API 参考
