# PyAgent æµè¯ææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»è¯´æPyAgent v0.8.0çæµè¯å¥ä»¶åè¿è¡æ¹æ³ã?
## æ¦è¿°

**v0.8.0** çæ¬å¼å¥äºå®æ´çæµè¯å¥ä»¶ï¼åå?8ä¸ªæµè¯ç¨ä¾ï¼è¦çæäººåç³»ç»ãTodoç³»ç»åè®°å¿ç³»ç»ã?
## æµè¯ç»æ

```
tests/
âââ conftest.py              # æµè¯éç½®åfixture
âââ test_humanized.py        # æäººåç³»ç»æµè¯ï¼14ä¸ªæµè¯ï¼
âââ test_todo.py            # Todoç³»ç»æµè¯ï¼?0ä¸ªæµè¯ï¼
âââ test_memory.py          # è®°å¿ç³»ç»æµè¯ï¼?ä¸ªæµè¯ï¼
```

## æµè¯æä»¶è¯´æ

### 1. conftest.py - æµè¯éç½®

**ä½ç¨**: æä¾pytestçéç½®åå±äº«fixture

```python
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """åå»ºäºä»¶å¾ªç¯ï¼ç¨äºå¼æ­¥æµè¯?""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

### 2. test_humanized.py - æäººåç³»ç»æµè¯?
**æµè¯æ°é**: 14ä¸ªæµè¯ç¨ä¾?
**æµè¯ç±?*:

#### TestHumanizedPromptBuilder
æµè¯æäººåPromptæå»ºå?

| æµè¯æ¹æ³ | è¯´æ |
|----------|------|
| `test_create_builder` | æµè¯åå»ºæå»ºå?|
| `test_get_persona_text` | æµè¯è·åäººè®¾ææ¬ |
| `test_build_direct_reply_prompt` | æµè¯æå»ºç´æ¥åå¤Prompt |
| `test_build_follow_up_prompt` | æµè¯æå»ºè¿½é®Prompt |
| `test_build_goodbye_prompt` | æµè¯æå»ºåå«è¯­Prompt |
| `test_update_emotion` | æµè¯æ´æ°ææç¶æ?|
| `test_get_status` | æµè¯è·åç¶æä¿¡æ?|

#### TestBehaviorPlanner
æµè¯è¡ä¸ºè§åå?

| æµè¯æ¹æ³ | è¯´æ |
|----------|------|
| `test_create_planner` | æµè¯åå»ºè§åå?|
| `test_should_greet` | æµè¯é®åå¤æ?|
| `test_get_greeting_message` | æµè¯è·åé®åæ¶æ?|
| `test_plan_action` | æµè¯è§åè¡å¨ |
| `test_should_end_conversation` | æµè¯ç»æå¯¹è¯å¤æ­ |
| `test_get_end_conversation_message` | æµè¯è·åç»æå¯¹è¯æ¶æ¯ |

### 3. test_todo.py - Todoç³»ç»æµè¯

**æµè¯æ°é**: 10ä¸ªæµè¯ç¨ä¾?
**æµè¯ç±?*:

#### TestTodoManager
æµè¯Todoç®¡çå?

| æµè¯æ¹æ³ | è¯´æ |
|----------|------|
| `test_create_manager` | æµè¯åå»ºç®¡çå?|
| `test_create_phase` | æµè¯åå»ºé¶æ®µ |
| `test_create_task` | æµè¯åå»ºä»»å¡ |
| `test_complete_step` | æµè¯å®ææ­¥éª¤ |
| `test_get_statistics` | æµè¯è·åç»è®¡ä¿¡æ¯ |

#### TestMateModeManager
æµè¯Mateæ¨¡å¼ç®¡çå?

| æµè¯æ¹æ³ | è¯´æ |
|----------|------|
| `test_create_manager` | æµè¯åå»ºç®¡çå?|
| `test_enable_disable` | æµè¯å¯ç¨/ç¦ç¨ |
| `test_toggle` | æµè¯åæ¢ç¶æ?|
| `test_add_reasoning_step` | æµè¯æ·»å æ¨çæ­¥éª¤ |
| `test_add_reflection` | æµè¯æ·»å åæ?|

### 4. test_memory.py - è®°å¿ç³»ç»æµè¯

**æµè¯æ°é**: 4ä¸ªæµè¯ç¨ä¾?
**æµè¯ç±?*:

#### TestChatMemoryStorage
æµè¯èå¤©è®°å¿å­å¨:

| æµè¯æ¹æ³ | è¯´æ |
|----------|------|
| `test_create_storage` | æµè¯åå»ºå­å¨ |
| `test_store_memory` | æµè¯å­å¨è®°å¿ |
| `test_recall_all` | æµè¯å¬åææè®°å¿?|

#### TestWorkMemoryStorage
æµè¯å·¥ä½è®°å¿å­å¨:

| æµè¯æ¹æ³ | è¯´æ |
|----------|------|
| `test_create_storage` | æµè¯åå»ºå­å¨ |
| `test_create_project_domain` | æµè¯åå»ºé¡¹ç®è®°å¿å?|
| `test_add_preference` | æµè¯æ·»å åå¥½ |

## è¿è¡æµè¯

### å®è£æµè¯ä¾èµ

```bash
pip install pytest pytest-asyncio pytest-cov
```

### è¿è¡æææµè¯?
```bash
pytest
```

### è¿è¡ç¹å®æµè¯æä»¶

```bash
# æäººåç³»ç»æµè¯?pytest tests/test_humanized.py

# Todoç³»ç»æµè¯
pytest tests/test_todo.py

# è®°å¿ç³»ç»æµè¯
pytest tests/test_memory.py
```

### è¿è¡ç¹å®æµè¯ç±?
```bash
# åªè¿è¡è¡ä¸ºè§åå¨æµè¯
pytest tests/test_humanized.py::TestBehaviorPlanner

# åªè¿è¡Todoç®¡çå¨æµè¯?pytest tests/test_todo.py::TestTodoManager
```

### è¿è¡ç¹å®æµè¯æ¹æ³

```bash
# åªè¿è¡æææ´æ°æµè¯?pytest tests/test_humanized.py::TestHumanizedPromptBuilder::test_update_emotion
```

### æ¾ç¤ºè¯¦ç»ä¿¡æ¯

```bash
pytest -v
```

### çæè¦ççæ¥å?
```bash
# çæHTMLè¦ççæ¥å?pytest --cov=src --cov-report=html

# çæç»ç«¯è¦ççæ¥å?pytest --cov=src --cov-report=term
```

### è°è¯æµè¯

```bash
# éå°ç¬¬ä¸ä¸ªå¤±è´¥å°±åæ­¢
pytest -x

# è¿å¥PDBè°è¯æ¨¡å¼
pytest --pdb

# æ¾ç¤ºææ¢çæµè¯
pytest --durations=10
```

## æµè¯è¦çèå´

### æäººåç³»ç»?(14ä¸ªæµè¯?

- **Promptæå»º**: ç´æ¥åå¤ãè¿½é®ãåå«è¯­ãè¡å¨è§å?- **ææç³»ç»**: ææç±»åãæææ¨æ­ãæææ´æ?- **è¡ä¸ºè§å**: é®åå¤æ­ãè¡å¨å³ç­ãå¯¹è¯ç»æå¤æ?- **ç¶æç®¡ç?*: ç¶æè·åãäººè®¾ææ¬çæ?
### Todoç³»ç» (10ä¸ªæµè¯?

- **é¶æ®µç®¡ç**: åå»ºé¶æ®µãé¶æ®µå±æ?- **ä»»å¡ç®¡ç**: åå»ºä»»å¡ãä»»å¡å±æ§ãæ­¥éª¤ç®¡ç?- **èªå¨æ´æ°**: å®ææ­¥éª¤ãçº§èæ´æ?- **Mateæ¨¡å¼**: å¯ç¨/ç¦ç¨ãæ¨çæ­¥éª¤ãåæè®°å½?- **ç»è®¡ä¿¡æ¯**: è¿åº¦è®¡ç®ãç»è®¡è·å?
### è®°å¿ç³»ç» (4ä¸ªæµè¯?

- **èå¤©è®°å¿**: å­å¨è®°å¿ãå¬åè®°å¿ãçº§å«ç®¡ç?- **å·¥ä½è®°å¿**: é¡¹ç®ååå»ºãåå¥½ç®¡ç?- **æ°æ®æä¹å?*: å­å¨åå è½?
## ç¼åæ°æµè¯?
### æµè¯æ¨¡æ¿

```python
"""
PyAgent [æ¨¡åå] æµè¯
"""

import pytest

from src.module import ClassName


class TestClassName:
    """ç±»æµè¯?""

    def test_method_name(self):
        """æµè¯æ¹æ³è¯´æ"""
        # åå¤
        obj = ClassName()
        
        # æ§è¡
        result = obj.method()
        
        # æ­è¨
        assert result is not None
        assert result.expected_attribute == expected_value

    @pytest.mark.asyncio
    async def test_async_method(self, tmp_path):
        """æµè¯å¼æ­¥æ¹æ³"""
        # ä½¿ç¨tmp_pathåå»ºä¸´æ¶ç®å½
        obj = ClassName(data_dir=str(tmp_path / "test"))
        
        # æ§è¡å¼æ­¥æä½
        result = await obj.async_method()
        
        # æ­è¨
        assert result is not None
```

### æä½³å®è·?
1. **ä½¿ç¨tmp_path**: å¯¹äºéè¦æä»¶ç³»ç»çæµè¯ï¼ä½¿ç¨pytestæä¾çtmp_path fixture
2. **å¼æ­¥æµè¯**: ä½¿ç¨`@pytest.mark.asyncio`è£é¥°å¨æ è®°å¼æ­¥æµè¯?3. **æµè¯å½å**: ä½¿ç¨`test_`åç¼ï¼æ¹æ³åæ¸æ°æè¿°æµè¯åå®¹
4. **ç¬ç«æµè¯**: æ¯ä¸ªæµè¯åºè¯¥ç¬ç«è¿è¡ï¼ä¸ä¾èµå¶ä»æµè¯
5. **å¿«éæµè¯?*: æµè¯åºè¯¥å¿«éæ§è¡ï¼é¿åé¿æ¶é´ç­å¾?
## æç»­éæ

### GitHub Actions éç½®ç¤ºä¾

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## æéæé¤

### å¸¸è§é®é¢

#### 1. å¯¼å¥éè¯¯

```
ModuleNotFoundError: No module named 'src'
```

**è§£å³**: ç¡®ä¿å¨é¡¹ç®æ ¹ç®å½è¿è¡æµè¯ï¼æè®¾ç½®PYTHONPATH

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest
```

#### 2. å¼æ­¥æµè¯å¤±è´¥

```
RuntimeError: no running event loop
```

**è§£å³**: ç¡®ä¿ä½¿ç¨`@pytest.mark.asyncio`è£é¥°å?
#### 3. æµè¯æ°æ®æ®ç

**è§£å³**: ä½¿ç¨tmp_path fixtureï¼pytestä¼èªå¨æ¸ç?
## æµè¯ç»è®¡

- **æ»æµè¯æ°**: 28ä¸?- **æäººåæµè¯?*: 14ä¸?- **Todoæµè¯**: 10ä¸?- **è®°å¿æµè¯**: 4ä¸?- **æµè¯è¦çç?*: å¾æµé?- **éè¿ç?*: 100%
