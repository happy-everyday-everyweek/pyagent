# 域系统文�?v0.8.0

本文档详细描述PyAgent v0.8.0域系统的设计和实现，支持多设备数据同步和分布式协作�?
## 概述

v0.7.0 引入域系统，实现多设备间的数据同步和协作�?- **域概�?*: 定义设备域，支持多设备协�?- **设备类型**: PC/MOBILE/SERVER/EDGE四种类型
- **数据同步**: 实时同步和定时同步两种模�?- **冲突解决**: 三方合并算法自动处理冲突
- **数据持久�?*: v0.8.0新增，域和设备数据自动保存到文件，服务重启后保留

## 架构设计

```
┌─────────────────────────────────────────────────────────────────�?�?                      域系统架�?                                �?├─────────────────────────────────────────────────────────────────�?�?                                                                �?�? ┌─────────�? ┌─────────�? ┌─────────�? ┌─────────�?          �?�? �? PC设备  �? �?Mobile  �? �?Server  �? �? Edge   �?          �?�? �?        �? �? 设备   �? �? 设备   �? �? 设备   �?          �?�? └────┬────�? └────┬────�? └────┬────�? └────┬────�?          �?�?      �?           �?           �?           �?                 �?�?      └────────────┴──────┬─────┴────────────�?                 �?�?                          �?                                    �?�?                   ┌──────┴──────�?                            �?�?                   �? Domain     �?                            �?�?                   �? Manager    �?                            �?�?                   �?            �?                            �?�?                   �?- 设备管理   �?                            �?�?                   �?- 数据同步   �?                            �?�?                   �?- 冲突解决   �?                            �?�?                   └──────┬──────�?                            �?�?                          �?                                    �?�?             ┌────────────┼────────────�?                      �?�?             �?           �?           �?                      �?�?       ┌─────────�? ┌─────────�? ┌─────────�?                 �?�?       �? Sync   �? �?Conflict�? �?Device  �?                 �?�?       �?Engine  �? │Resolver �? �?Registry�?                 �?�?       └─────────�? └─────────�? └─────────�?                 �?�?                                                                �?└─────────────────────────────────────────────────────────────────�?```

## 核心概念

### �?(Domain)

域是一组设备的逻辑集合，域内设备可以相互同步数据�?
```python
@dataclass
class Domain:
    """域定�?""
    id: str                    # 域ID
    name: str                  # 域名�?    owner_device_id: str       # 所有者设备ID
    created_at: datetime       # 创建时间
    devices: list[DeviceInfo]  # 域内设备列表
```

### 设备类型

```python
class DeviceType(Enum):
    """设备类型"""
    PC = "pc"                  # 个人电脑
    MOBILE = "mobile"          # 移动设备
    SERVER = "server"          # 服务�?    EDGE = "edge"              # 边缘设备
```

### 设备能力

```python
@dataclass
class DeviceCapabilities:
    """设备能力声明"""
    cpu_cores: int             # CPU核心�?    memory_gb: float           # 内存容量(GB)
    storage_gb: float          # 存储容量(GB)
    has_gpu: bool              # 是否有GPU
    gpu_model: str | None      # GPU型号
    network_type: str          # 网络类型
    supported_tasks: list[str] # 支持的任务类�?```

### 设备信息

```python
@dataclass
class DeviceInfo:
    """设备信息"""
    device_id: str             # 设备ID
    device_type: DeviceType    # 设备类型
    device_name: str           # 设备名称
    capabilities: DeviceCapabilities  # 设备能力
    last_seen: datetime        # 最后在线时�?    is_online: bool            # 是否在线
    sync_mode: SyncMode        # 同步模式
```

## 数据同步

### 同步模式

```python
class SyncMode(Enum):
    """同步模式"""
    REALTIME = "realtime"      # 实时同步
    SCHEDULED = "scheduled"    # 定时同步
    MANUAL = "manual"          # 手动同步
```

### 同步引擎

```python
class SyncEngine:
    """数据同步引擎"""
    
    async def sync_to_domain(
        self,
        device_id: str,
        data_type: str,
        data: bytes
    ) -> SyncResult:
        """同步数据到域"""
        
    async def sync_from_domain(
        self,
        device_id: str,
        data_type: str
    ) -> bytes:
        """从域同步数据"""
        
    async def get_sync_status(
        self,
        device_id: str
    ) -> SyncStatus:
        """获取同步状�?""
```

### 类Git分支模型

每台设备相当于一个分支，数据变更形成提交历史�?
```
�?(Domain)
├── Device A (分支)
�?  ├── Commit 1: 添加任务
�?  ├── Commit 2: 修改配置
�?  └── Commit 3: 删除记忆
├── Device B (分支)
�?  ├── Commit 1: 添加任务
�?  └── Commit 2: 更新Todo
└── Merge: 自动合并到主分支
```

## 冲突解决

### 冲突检�?
```python
class ConflictResolver:
    """冲突解决�?""
    
    def detect_conflicts(
        self,
        local_data: dict,
        remote_data: dict,
        base_data: dict | None = None
    ) -> list[Conflict]:
        """检测冲�?""
        
    def resolve_conflicts(
        self,
        conflicts: list[Conflict],
        strategy: ConflictStrategy = ConflictStrategy.AUTO
    ) -> ResolutionResult:
        """解决冲突"""
```

### 解决策略

```python
class ConflictStrategy(Enum):
    """冲突解决策略"""
    AUTO = "auto"              # 自动解决
    LOCAL_WINS = "local"       # 本地优先
    REMOTE_WINS = "remote"     # 远程优先
    MANUAL = "manual"          # 手动解决
```

### 三方合并算法

```python
def three_way_merge(
    base: dict,      # 共同祖先
    local: dict,     # 本地版本
    remote: dict     # 远程版本
) -> MergeResult:
    """
    三方合并算法
    
    1. 比较base和local，找出本地修�?    2. 比较base和remote，找出远程修�?    3. 判断修改是否冲突
    4. 无冲突则合并，有冲突则标�?    """
```

## API接口

### 域管�?
```http
POST /api/domains/create
Content-Type: application/json

{
  "name": "我的�?
}
```

```http
GET /api/domains/{domain_id}
```

```http
DELETE /api/domains/{domain_id}
```

### 设备管理

```http
POST /api/domains/{domain_id}/devices/join
Content-Type: application/json

{
  "device_type": "pc",
  "device_name": "我的工作电脑",
  "capabilities": {
    "cpu_cores": 8,
    "memory_gb": 16,
    "storage_gb": 512,
    "has_gpu": true
  }
}
```

```http
DELETE /api/domains/{domain_id}/devices/{device_id}
```

```http
GET /api/domains/{domain_id}/devices
```

### 数据同步

```http
POST /api/domains/{domain_id}/sync
Content-Type: application/json

{
  "data_type": "memory",
  "sync_mode": "realtime"
}
```

```http
GET /api/domains/{domain_id}/sync/status
```

```http
POST /api/domains/{domain_id}/sync/resolve
Content-Type: application/json

{
  "conflict_id": "conflict_123",
  "resolution": "local"
}
```

## 配置文件

### 域系统配�?
```yaml
# config/domain.yaml

domain:
  # 当前设备信息
  device:
    name: "我的工作电脑"
    type: "pc"
    capabilities:
      cpu_cores: 8
      memory_gb: 16
      storage_gb: 512
      has_gpu: true
      gpu_model: "RTX 3060"
      network_type: "wifi"
      supported_tasks:
        - "llm_inference"
        - "video_processing"
        - "document_editing"
  
  # 同步配置
  sync:
    # 默认同步模式
    default_mode: "realtime"
    
    # 实时同步配置
    realtime:
      enabled: true
      debounce_ms: 500
      
    # 定时同步配置
    scheduled:
      enabled: false
      interval_minutes: 30
      
  # 冲突解决配置
  conflict_resolution:
    default_strategy: "auto"
    
    # 自动解决规则
    auto_rules:
      - data_type: "memory"
        strategy: "newer_wins"
      - data_type: "todo"
        strategy: "merge"
      - data_type: "config"
        strategy: "manual"
```

## 使用示例

### 创建�?
```python
from src.device.domain_manager import DomainManager

domain_manager = DomainManager()

# 创建�?domain = await domain_manager.create_domain(
    name="我的�?
)

print(f"域ID: {domain.id}")
print(f"域名�? {domain.name}")
```

### 加入�?
```python
from src.device import DeviceType, DeviceCapabilities

# 声明设备能力
capabilities = DeviceCapabilities(
    cpu_cores=8,
    memory_gb=16,
    storage_gb=512,
    has_gpu=True,
    gpu_model="RTX 3060",
    network_type="wifi",
    supported_tasks=["llm_inference", "video_processing"]
)

# 加入�?device = await domain_manager.join_domain(
    domain_id="domain_123",
    device_type=DeviceType.PC,
    device_name="我的工作电脑",
    capabilities=capabilities
)

print(f"设备ID: {device.device_id}")
```

### 数据同步

```python
from src.device.sync_engine import SyncEngine

sync_engine = SyncEngine()

# 同步记忆数据
result = await sync_engine.sync_to_domain(
    device_id="device_123",
    data_type="memory",
    data=memory_data
)

if result.success:
    print("同步成功")
else:
    print(f"同步失败: {result.error}")
```

### 处理冲突

```python
from src.device.conflict_resolver import ConflictResolver, ConflictStrategy

resolver = ConflictResolver()

# 检测冲�?conflicts = resolver.detect_conflicts(
    local_data=local_memory,
    remote_data=remote_memory,
    base_data=base_memory
)

if conflicts:
    print(f"发现 {len(conflicts)} 个冲�?)
    
    # 自动解决冲突
    result = resolver.resolve_conflicts(
        conflicts=conflicts,
        strategy=ConflictStrategy.AUTO
    )
    
    if result.resolved:
        print("冲突已解�?)
    else:
        print(f"需要手动解决的冲突: {result.manual_conflicts}")
```

## 故障排除

### 设备无法加入�?
**现象**: 加入域时失败

**解决**:
1. 检查域ID是否正确
2. 验证网络连接
3. 检查设备ID是否已存�?
### 同步失败

**现象**: 数据同步失败

**解决**:
1. 检查目标设备是否在�?2. 验证网络连接
3. 检查存储空�?4. 查看同步日志

### 冲突无法解决

**现象**: 自动冲突解决失败

**解决**:
1. 手动选择解决策略
2. 检查数据格�?3. 联系域管理员

## 最佳实�?
1. **合理命名**: 为设备和域使用有意义的名�?2. **能力声明**: 准确声明设备能力，便于任务分�?3. **同步策略**: 根据网络环境选择合适的同步模式
4. **冲突监控**: 定期检查冲突日�?5. **备份重要数据**: 重要数据建议本地备份
