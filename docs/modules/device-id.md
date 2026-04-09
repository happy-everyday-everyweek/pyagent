# è®¾å¤IDç³»ç»ææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»æè¿°PyAgent v0.8.0è®¾å¤IDç³»ç»çè®¾è®¡åå®ç°ã?
## æ¦è¿°

è®¾å¤IDç³»ç»ä¸ºæ¯ä¸ªPyAgentå®ä¾çæå¯ä¸çè®¾å¤æ è¯ç¬¦ï¼ç¨äºï¼
- è®¾å¤è¯å«åè¿½è¸?- å·¥å·è°ç¨æ¶çè®¾å¤ä¿¡æ¯ä¼ é?- å¤è®¾å¤ç¯å¢ä¸çåºå?
## è®¾å¤IDçæè§å

è®¾å¤IDçæéç¨ä»¥ä¸ç®æ³ï¼?
1. **è·åå½åæ¥æ**: `YYYYMMDD` æ ¼å¼
2. **çæéæºæ?*: 10ä½éæºæ°å­?3. **æ¼æ¥å­ç¬¦ä¸?*: `æ¥æ + éæºæ°`
4. **SHA256åå¸**: å¯¹æ¼æ¥å­ç¬¦ä¸²è¿è¡åå¸è®¡ç®
5. **æªåå?6ä½?*: ååå¸å¼çå?6ä½ä½ä¸ºè®¾å¤ID

### ç¤ºä¾

```
æ¥æ: 20250329
éæºæ? 1234567890
æ¼æ¥: 202503291234567890
SHA256: a1b2c3d4e5f6... (64ä½åå­è¿å?
è®¾å¤ID: a1b2c3d4e5f67890 (å?6ä½?
```

## æ ¸å¿ç»ä»¶

### DeviceIDGenerator

è®¾å¤IDçæå¨ï¼è´è´£çæå¯ä¸çè®¾å¤IDï¼?
```python
class DeviceIDGenerator:
    @staticmethod
    def generate() -> str:
        """çæ16ä½è®¾å¤ID"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_digits = "".join([str(random.randint(0, 9)) for _ in range(10)])
        combined = f"{date_str}{random_digits}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()
        return hash_value[:16]
```

### DeviceIDManager

è®¾å¤IDç®¡çå¨ï¼åä¾æ¨¡å¼ï¼ï¼è´è´£è®¾å¤IDçæä¹åç®¡çï¼?
```python
class DeviceIDManager:
    def get_device_id(self) -> str:
        """è·åæåå»ºè®¾å¤ID"""
        
    def get_device_info(self) -> DeviceIDInfo | None:
        """è·åè®¾å¤IDå®æ´ä¿¡æ¯"""
        
    def regenerate_device_id(self) -> str:
        """éæ°çæè®¾å¤ID"""
        
    def update_metadata(self, key: str, value: Any) -> None:
        """æ´æ°è®¾å¤åæ°æ?""
        
    def clear_device_id(self) -> bool:
        """æ¸é¤è®¾å¤ID"""
```

### DeviceIDInfo

è®¾å¤IDä¿¡æ¯æ°æ®ç±»ï¼

```python
@dataclass
class DeviceIDInfo:
    device_id: str           # è®¾å¤ID
    created_at: str          # åå»ºæ¶é´
    metadata: dict           # åæ°æ?```

## å­å¨ä½ç½®

è®¾å¤IDå­å¨å¨ä»¥ä¸ä½ç½®ï¼

```
data/
âââ device/
    âââ device_id.json      # è®¾å¤IDæä»¶
```

### æä»¶æ ¼å¼

```json
{
  "device_id": "a1b2c3d4e5f67890",
  "created_at": "2025-03-29T10:30:00",
  "metadata": {}
}
```

## ä½¿ç¨ç¤ºä¾

### è·åè®¾å¤ID

```python
from src.device import device_id_manager

# è·åè®¾å¤IDï¼å¦æä¸å­å¨åèªå¨åå»ºï¼
device_id = device_id_manager.get_device_id()
print(f"è®¾å¤ID: {device_id}")  # è¾åº: a1b2c3d4e5f67890
```

### è·åè®¾å¤ä¿¡æ¯

```python
from src.device import device_id_manager

device_info = device_id_manager.get_device_info()
if device_info:
    print(f"è®¾å¤ID: {device_info.device_id}")
    print(f"åå»ºæ¶é´: {device_info.created_at}")
    print(f"åæ°æ? {device_info.metadata}")
```

### éæ°çæè®¾å¤ID

```python
from src.device import device_id_manager

# å¼ºå¶çææ°çè®¾å¤IDï¼è¦çåæIDï¼?new_device_id = device_id_manager.regenerate_device_id()
print(f"æ°è®¾å¤ID: {new_device_id}")
```

### ç®¡çåæ°æ?
```python
from src.device import device_id_manager

# æ´æ°åæ°æ?device_id_manager.update_metadata("os", "Windows")
device_id_manager.update_metadata("version", "0.6.0")

# è·ååæ°æ?os_info = device_id_manager.get_metadata("os", "Unknown")
print(f"æä½ç³»ç»: {os_info}")
```

### æ¸é¤è®¾å¤ID

```python
from src.device import device_id_manager

# æ¸é¤è®¾å¤IDï¼å é¤å­å¨æä»¶ï¼
success = device_id_manager.clear_device_id()
if success:
    print("è®¾å¤IDå·²æ¸é?)
```

## å¨å·¥å·è°ç¨ä¸­ä½¿ç¨

è®¾å¤IDä¼åå«å¨å·¥å·åè¡¨ä¸­ï¼ä¾å¤é¨æå¡è¯å«ï¼

```python
# å·¥å·åè¡¨ç¤ºä¾
tools = [
    {
        "name": "example_tool",
        "description": "ç¤ºä¾å·¥å·",
        "parameters": {...}
    }
]

# åå«è®¾å¤IDçå·¥å·ä¿¡æ?tool_info = {
    "tools": tools,
    "device_id": device_id_manager.get_device_id()
}
```

## APIæ¥å£

### è·åè®¾å¤ID

```http
GET /api/device/id
```

**ååº**:
```json
{
  "device_id": "a1b2c3d4e5f67890"
}
```

### è·åè®¾å¤ä¿¡æ¯

```http
GET /api/device/info
```

**ååº**:
```json
{
  "device_id": "a1b2c3d4e5f67890",
  "created_at": "2025-03-29T10:30:00",
  "metadata": {}
}
```

### éæ°çæè®¾å¤ID

```http
POST /api/device/regenerate
```

**ååº**:
```json
{
  "success": true,
  "device_id": "b2c3d4e5f6g78901"
}
```

## æ³¨æäºé¡¹

### 1. åä¾æ¨¡å¼

DeviceIDManager ä½¿ç¨åä¾æ¨¡å¼ï¼ç¡®ä¿æ´ä¸ªåºç¨åªæä¸ä¸ªè®¾å¤IDå®ä¾ï¼?
```python
# å¤æ¬¡è·åçæ¯åä¸ä¸ªå®ä¾?manager1 = DeviceIDManager()
manager2 = DeviceIDManager()
assert manager1 is manager2  # True
```

### 2. æä¹åå­å?
è®¾å¤IDä¼èªå¨æä¹åå°æä»¶ï¼åºç¨éå¯åä»ç¶ææï¼

```python
# ç¬¬ä¸æ¬¡è¿è¡?device_id = device_id_manager.get_device_id()
# è®¾å¤IDä¿å­å?data/device/device_id.json

# éå¯åºç¨å?same_device_id = device_id_manager.get_device_id()
# è¿åç¸åçè®¾å¤ID
```

### 3. çº¿ç¨å®å¨

è®¾å¤IDç®¡çå¨æ¯çº¿ç¨å®å¨çï¼å¯ä»¥å¨å¤çº¿ç¨ç¯å¢ä¸­ä½¿ç¨ï¼

```python
import threading

def get_id():
    return device_id_manager.get_device_id()

# å¤çº¿ç¨è·åç¸åçè®¾å¤ID
threads = [threading.Thread(target=get_id) for _ in range(10)]
```

### 4. æµè¯éç½®

æµè¯æ¶éè¦éç½®åä¾å®ä¾ï¼

```python
# æµè¯ä»£ç 
DeviceIDManager.reset_instance()
manager = DeviceIDManager(data_dir="test_data/device")
```

## æéæé¤

### è®¾å¤IDä¸ºç©º

**ç°è±¡**: `get_device_id()` è¿åç©ºå­ç¬¦ä¸²

**åå **:
- å­å¨æä»¶æå
- æéä¸è¶³æ æ³åå¥æä»¶

**è§£å³**:
```python
# éæ°çæè®¾å¤ID
device_id = device_id_manager.regenerate_device_id()
```

### æ æ³è¯»åè®¾å¤ID

**ç°è±¡**: æç¤ºæä»¶è¯»åéè¯¯

**åå **:
- æä»¶æéé®é¢
- æä»¶è¢«å¶ä»è¿ç¨å ç?
**è§£å³**:
1. æ£æ¥æä»¶æé?2. å³é­å¶ä»å ç¨è¯¥æä»¶çè¿ç¨
3. æå¨å é¤ `data/device/device_id.json` åéæ°çæ?
### è®¾å¤IDå²çª

**ç°è±¡**: å¤å°è®¾å¤çæç¸åçè®¾å¤ID

**åå **:
- æå°æ¦ççåå¸ç¢°æ?- æå¨å¤å¶äºè®¾å¤IDæä»¶

**è§£å³**:
```python
# éæ°çæå¯ä¸çè®¾å¤ID
device_id = device_id_manager.regenerate_device_id()
```

## æä½³å®è·?
1. **ä¸è¦é¢ç¹éæ°çæ**: è®¾å¤IDåºè¯¥ä¿æç¨³å®ï¼ä¾¿äºè¿½è¸?2. **å¤ä»½è®¾å¤ID**: éè¦åºæ¯ä¸å¤ä»?`device_id.json` æä»¶
3. **ä¿æ¤éç§**: è®¾å¤IDå¯è½åå«æ¶é´ä¿¡æ¯ï¼æ³¨æéç§ä¿æ?4. **åæ°æ®ç®¡ç?*: åçä½¿ç¨åæ°æ®å­å¨è®¾å¤ç¸å³ä¿¡æ?
