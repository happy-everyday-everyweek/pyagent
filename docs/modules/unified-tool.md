# ç»ä¸å·¥å·æ¥å£ææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»æè¿°PyAgent v0.8.0ç»ä¸å·¥å·è°ç¨æ¥å£çè®¾è®¡åå®ç°ã?
## æ¦è¿°

v0.6.0 éæäºææå·¥å·è°ç¨æµç¨ï¼å¼å¥ç»ä¸çä¸é¶æ®µè°ç¨æ¨¡åï¼?*æ¿æ´?â?æ§è¡ â?ä¼ç **ãè¿ä¸ªæ¨¡åéç¨äºï¼
- Skillå·¥å·
- MCPå·¥å·
- èªå®ä¹å·¥å?
## ä¸é¶æ®µè°ç¨æ¨¡å?
```
âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?â?                    å·¥å·çå½å¨æ                                 â?âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?â?                                                                â?â?  âââââââââââ?   âââââââââââ?   âââââââââââ?                  â?â?  â? IDLE   â?â? â?ACTIVE  â?â? â?DORMANT â?                  â?â?  â?(ç©ºé²)  â?   â?(æ´»è·)  â?   â?(ä¼ç )  â?                  â?â?  âââââââââââ?   âââââââââââ?   âââââââââââ?                  â?â?       â?             â?             â?                        â?â?       â?activate     â?execute      â?dormant                â?â?       â?             â?             â?                        â?â?  åå§åèµæº?     æ§è¡ä¸å¡é»è¾      éæ¾èµæº                    â?â?                                                                â?âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?```

### é¶æ®µè¯´æ

1. **æ¿æ´?(Activate)**: åå§åå·¥å·èµæºï¼å»ºç«è¿æ¥
2. **æ§è¡ (Execute)**: æ§è¡ä¸å¡é»è¾ï¼è¿åç»æ?3. **ä¼ç  (Dormant)**: éæ¾èµæºï¼ä¿æç¶æå¯æ¢å¤

## æ ¸å¿ç»ä»¶

### UnifiedTool æ½è±¡åºç±»

ææå·¥å·å¿é¡»ç»§æ¿çæ½è±¡åºç±»ï¼?
```python
class UnifiedTool(ABC):
    """ç»ä¸å·¥å·æ½è±¡åºç±»"""
    
    name: str = "unified_tool"
    description: str = "ç»ä¸å·¥å·åºç±»"
    
    @abstractmethod
    async def activate(self, context: ToolContext) -> bool:
        """æ¿æ´»å·¥å?""
        pass
    
    @abstractmethod
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """æ§è¡å·¥å·"""
        pass
    
    @abstractmethod
    async def dormant(self, context: ToolContext) -> bool:
        """ä¼ç å·¥å·"""
        pass
    
    async def call(self, context: ToolContext | None = None, **kwargs) -> ToolResult:
        """ç»ä¸è°ç¨å¥å£"""
        # èªå¨å¤çä¸é¶æ®µè°ç¨æµç¨?```

### å·¥å·ç¶æ?
```python
class ToolState(Enum):
    """å·¥å·ç¶æ?""
    IDLE = "idle"           # ç©ºé²ç¶æ?    ACTIVE = "active"       # æ´»è·ç¶æï¼å¯æ§è¡ï¼
    DORMANT = "dormant"     # ä¼ç ç¶æ?    ERROR = "error"         # éè¯¯ç¶æ?```

### å·¥å·ä¸ä¸æ?
```python
@dataclass
class ToolContext:
    """å·¥å·æ§è¡ä¸ä¸æ?""
    device_id: str = ""     # è®¾å¤ID
    session_id: str = ""    # ä¼è¯ID
    user_id: str = ""       # ç¨æ·ID
    metadata: dict = {}     # åæ°æ?```

### å·¥å·ç»æ

```python
@dataclass
class ToolResult:
    """å·¥å·æ§è¡ç»æ"""
    success: bool           # æ¯å¦æå
    output: str = ""        # è¾åºåå®¹
    error: str = ""         # éè¯¯ä¿¡æ¯
    data: Any = None        # æ°æ®
    metadata: dict = {}     # åæ°æ?```

## ä½¿ç¨ç¤ºä¾

### åå»ºèªå®ä¹å·¥å?
```python
from src.tools import UnifiedTool, ToolContext, ToolResult

class MyCustomTool(UnifiedTool):
    """èªå®ä¹å·¥å·ç¤ºä¾?""
    
    name = "my_custom_tool"
    description = "æçèªå®ä¹å·¥å?
    
    async def activate(self, context: ToolContext) -> bool:
        """æ¿æ´»å·¥å?- åå§åèµæº?""
        print(f"æ¿æ´»å·¥å·ï¼è®¾å¤ID: {context.device_id}")
        # åå§åæ°æ®åºè¿æ¥ãAPIå®¢æ·ç«¯ç­
        self._state = ToolState.ACTIVE
        return True
    
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """æ§è¡å·¥å· - ä¸å¡é»è¾"""
        try:
            # æ§è¡ä¸å¡é»è¾
            result = f"å¤çå®æ: {kwargs.get('input', '')}"
            return ToolResult(
                success=True,
                output=result,
                data={"processed": True}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def dormant(self, context: ToolContext) -> bool:
        """ä¼ç å·¥å· - éæ¾èµæº"""
        print("ä¼ç å·¥å·ï¼éæ¾èµæº?)
        # å³é­è¿æ¥ãæ¸çç¼å­ç­
        self._state = ToolState.DORMANT
        return True
```

### è°ç¨å·¥å·

```python
# åå»ºå·¥å·å®ä¾
tool = MyCustomTool(device_id="a1b2c3d4e5f67890")

# ç»ä¸è°ç¨ï¼èªå¨å¤çä¸é¶æ®µï¼?result = await tool.call(input="æµè¯æ°æ®")

if result.success:
    print(f"è¾åº: {result.output}")
    print(f"æ°æ®: {result.data}")
else:
    print(f"éè¯¯: {result.error}")
```

### æå¨æ§å¶çå½å¨æ

```python
# åå»ºå·¥å·
tool = MyCustomTool()

# æå¨æ¿æ´?context = ToolContext(device_id="device_001")
success = await tool.activate(context)

if success:
    # å¤æ¬¡æ§è¡
    result1 = await tool.execute(context, input="æ°æ®1")
    result2 = await tool.execute(context, input="æ°æ®2")
    
    # ä¼ç 
    await tool.dormant(context)
    
    # å¤é
    await tool.wake(context)
    
    # åæ¬¡æ§è¡
    result3 = await tool.execute(context, input="æ°æ®3")
```

## å·¥å·æ³¨åä¸­å¿

### ToolRegistry

å·¥å·æ³¨åä¸­å¿ç®¡çææå¯ç¨å·¥å·ï¼

```python
from src.tools import ToolRegistry

# è·åæ³¨åä¸­å¿
registry = ToolRegistry()

# æ³¨åå·¥å·
registry.register(MyCustomTool())

# è·åå·¥å·
tool = registry.get("my_custom_tool")

# ååºææå·¥å?tools = registry.list_tools()

# è°ç¨å·¥å·
result = await registry.call("my_custom_tool", input="æµè¯")
```

## ç¶ææµè½?
```
IDLE â?ACTIVATE â?ACTIVE â?EXECUTE â?ACTIVE â?DORMANT â?DORMANT
              â?             â?           ERROR ââââââââââââ?              â?           ACTIVATE (éè¯)
```

### ç¶æè½¬æ¢è§å?
| å½åç¶æ?| æä½ | ç®æ ç¶æ?| è¯´æ |
|---------|------|---------|------|
| IDLE | activate | ACTIVE | åå§åæå?|
| IDLE | activate | ERROR | åå§åå¤±è´?|
| ACTIVE | execute | ACTIVE | æ§è¡æå |
| ACTIVE | execute | ERROR | æ§è¡å¤±è´¥ |
| ERROR | activate | ACTIVE | éè¯æå |
| ACTIVE | dormant | DORMANT | ä¼ç  |
| ERROR | dormant | DORMANT | å¼ºå¶ä¼ç  |
| DORMANT | wake | ACTIVE | å¤é |

## éè¯¯å¤ç

### æ¿æ´»å¤±è´?
```python
result = await tool.call()
if not result.success:
    # æ¿æ´»é¶æ®µå¤±è´?    print(f"æ¿æ´»å¤±è´? {result.error}")
```

### æ§è¡å¤±è´¥

```python
result = await tool.call(risky_operation=True)
if not result.success:
    # æ§è¡é¶æ®µå¤±è´¥ï¼å·¥å·è¿å¥ERRORç¶æ?    print(f"æ§è¡å¤±è´¥: {result.error}")
    
    # å¯ä»¥éè¯
    result = await tool.call()  # ä¼èªå¨å°è¯éæ°æ¿æ´?```

### å¼å¸¸æè·

```python
try:
    result = await tool.call()
except Exception as e:
    # æªæè·çå¼å¸¸
    print(f"å¼å¸¸: {e}")
```

## ä¸æ§çæ¬å¯¹æ¯

### æ§çæ¬ï¼ç´æ¥è°ç¨ï¼?
```python
# æ§æ¹å¼?- ç´æ¥æ§è¡ï¼æ çå½å¨æç®¡ç
tool = OldTool()
result = tool.execute(param="value")
```

### æ°çæ¬ï¼ä¸é¶æ®µè°ç¨ï¼

```python
# æ°æ¹å¼?- ç»ä¸è°ç¨å¥å£ï¼èªå¨çå½å¨æç®¡ç?tool = NewTool()
result = await tool.call(param="value")
```

### ä¼å¿

1. **èµæºç®¡ç**: èªå¨åå§ååéæ¾èµæº
2. **ç¶æè¿½è¸?*: æ¸æ°çç¶ææµè½?3. **éè¯¯æ¢å¤**: æ¯æå¤±è´¥éè¯
4. **æ§è½ä¼å**: æ¯æå·¥å·å¤ç¨åä¼ç?5. **ç»ä¸æ¥å£**: ææå·¥å·ä½¿ç¨ç¸åæ¥å?
## æä½³å®è·?
### 1. èµæºç®¡ç

```python
async def activate(self, context: ToolContext) -> bool:
    # åªåå§åå¿è¦èµæº
    self.client = APIClient()
    self.connection = await create_connection()
    return True

async def dormant(self, context: ToolContext) -> bool:
    # éæ¾ééçº§èµæºï¼ä¿çè½»éçº§ç¶æ?    await self.connection.close()
    self.connection = None
    # ä¿ç client ä»¥ä¾¿å¿«éæ¢å¤?    return True
```

### 2. éè¯¯å¤ç

```python
async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
    try:
        result = await self.do_work(**kwargs)
        return ToolResult(success=True, data=result)
    except NetworkError as e:
        # ç½ç»éè¯¯ - å¯éè¯?        return ToolResult(success=False, error=f"ç½ç»éè¯¯: {e}")
    except ValidationError as e:
        # åæ°éè¯¯ - ä¸å¯éè¯
        return ToolResult(success=False, error=f"åæ°éè¯¯: {e}")
```

### 3. ç¶ææ£æ?
```python
async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
    # æ£æ¥åç½®æ¡ä»?    if not self._connection:
        return ToolResult(
            success=False, 
            error="å·¥å·æªæ¿æ´?
        )
    
    # æ§è¡ä¸å¡é»è¾
    ...
```

## æéæé¤

### å·¥å·æ æ³æ¿æ´?
**ç°è±¡**: `call()` è¿åæ¿æ´»å¤±è´?
**åå **:
- èµæºåå§åå¤±è´?- ä¾èµæå¡ä¸å¯ç?- éç½®éè¯¯

**è§£å³**:
1. æ£æ?`activate()` å®ç°
2. éªè¯ä¾èµæå¡ç¶æ?3. æ£æ¥éç½®åæ?
### å·¥å·æ§è¡è¶æ¶

**ç°è±¡**: æ§è¡é¿æ¶é´æ ååº

**è§£å³**:
```python
# æ·»å è¶æ¶æ§å¶
import asyncio

try:
    result = await asyncio.wait_for(
        tool.call(),
        timeout=30.0
    )
except asyncio.TimeoutError:
    print("æ§è¡è¶æ¶")
```

### å·¥å·ç¶æå¼å¸?
**ç°è±¡**: å·¥å·å¤äº ERROR ç¶ææ æ³æ¢å¤?
**è§£å³**:
```python
# éç½®å·¥å·
tool.reset()

# æèå¼ºå¶ä¼ç åå¤é
await tool.sleep()
await tool.wake()
```
