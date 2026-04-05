# PyAgent 分布式存储系统

**版本**: v0.8.0  
**模块路径**: `src/storage/`  
**最后更新**: 2025-04-03

---

## 概述

分布式存储系统是 PyAgent v0.8.0 引入的全新模块，提供跨设备的文件存储和同步功能。基于域系统实现，支持文件上传、下载、同步、版本管理和冲突解决，实现多设备间的无缝数据共享。

### 核心特性

- **跨设备同步**: 文件自动同步到域内所有设备
- **元数据管理**: 完整的文件元数据和位置追踪
- **冲突解决**: 智能处理多设备同时修改的冲突
- **增量同步**: 只传输变更部分，节省带宽
- **本地缓存**: 智能缓存策略，加速文件访问
- **版本历史**: 支持文件版本回溯

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                 Distributed Storage System                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │DistributedStorage│   │   SyncProtocol  │                 │
│  │   (存储核心)     │◄──►│   (同步协议)     │                 │
│  └────────┬────────┘    └─────────────────┘                 │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  FileTracker    │    │  FileMetadata   │                 │
│  │  (文件追踪器)    │    │   (文件元数据)   │                 │
│  └─────────────────┘    └─────────────────┘                 │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Storage Layers                         │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │  Local   │  │  Cache   │  │  Remote  │          │    │
│  │  │ Storage  │  │  Layer   │  │  Sync    │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 分布式存储 (DistributedStorage)

**位置**: `src/storage/distributed.py`

```python
from src.storage.distributed import DistributedStorage, get_distributed_storage

# 使用全局实例
storage = get_distributed_storage()

# 或创建新实例
storage = DistributedStorage(
    data_dir="data/storage",
    local_storage_dir="data/storage/files"
)
storage.initialize()
```

#### 主要方法

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `upload_file()` | 上传文件 | `FileMetadata \| None` |
| `get_file()` | 获取文件内容 | `tuple[bytes \| None, FileMetadata \| None]` |
| `get_file_path()` | 获取文件路径 | `Path \| None` |
| `list_files()` | 列出文件 | `list[FileMetadata]` |
| `delete_file()` | 删除文件 | `bool` |
| `search_files()` | 搜索文件 | `list[FileMetadata]` |
| `get_recent_files()` | 获取最近文件 | `list[FileMetadata]` |
| `get_storage_stats()` | 获取统计信息 | `dict` |
| `export_metadata()` | 导出元数据 | `bool` |
| `import_metadata()` | 导入元数据 | `int` |

---

### 2. 文件元数据 (FileMetadata)

```python
@dataclass
class FileMetadata:
    file_id: str            # 文件唯一ID
    file_name: str          # 文件名
    file_path: str          # 文件路径
    file_size: int          # 文件大小
    file_type: str          # 文件类型
    checksum: str           # 校验和
    device_id: str          # 所属设备ID
    created_at: datetime    # 创建时间
    modified_at: datetime   # 修改时间
    tags: list[str]         # 标签
    status: FileStatus      # 文件状态
```

#### 文件状态 (FileStatus)

```python
class FileStatus(Enum):
    LOCAL_ONLY = "local_only"       # 仅本地
    SYNCED = "synced"               # 已同步
    SYNCING = "syncing"             # 同步中
    CONFLICT = "conflict"           # 冲突
    ERROR = "error"                 # 错误
```

---

## 使用示例

### 文件上传

```python
from src.storage.distributed import get_distributed_storage

storage = get_distributed_storage()

# 上传文件
metadata = storage.upload_file("/path/to/document.pdf")
if metadata:
    print(f"文件上传成功: {metadata.file_id}")
    print(f"文件名: {metadata.file_name}")
    print(f"大小: {metadata.file_size} bytes")
    print(f"校验和: {metadata.checksum}")

# 上传但不广播
metadata = storage.upload_file("/path/to/local.txt", broadcast=False)
```

### 文件下载

```python
from src.storage.distributed import get_distributed_storage

storage = get_distributed_storage()

# 获取文件内容
content, metadata = storage.get_file("file_abc123")
if content:
    with open("downloaded.pdf", "wb") as f:
        f.write(content)
    print(f"文件下载成功: {metadata.file_name}")
else:
    print("文件不存在或无法获取")

# 获取文件路径
file_path = storage.get_file_path("file_abc123")
if file_path:
    print(f"文件路径: {file_path}")
```

### 文件管理

```python
from src.storage.distributed import get_distributed_storage

storage = get_distributed_storage()

# 列出所有文件
all_files = storage.list_files()
print(f"共有 {len(all_files)} 个文件")

# 列出指定设备的文件
device_files = storage.list_files(device_id="device_xyz")

# 搜索文件
results = storage.search_files("report")
for file in results:
    print(f"找到: {file.file_name}")

# 获取最近访问的文件
recent = storage.get_recent_files(limit=5)

# 删除文件
success = storage.delete_file("file_abc123")
if success:
    print("文件已删除")

# 更新文件标签
storage.update_file_tags("file_abc123", ["重要", "工作"])
```

### 统计信息

```python
from src.storage.distributed import get_distributed_storage

storage = get_distributed_storage()

stats = storage.get_storage_stats()
print(f"""
存储统计
========
设备ID: {stats['device_id']}

本地存储:
  文件数: {stats['local_storage']['file_count']}
  总大小: {stats['local_storage']['total_size']} bytes

追踪器统计:
  总文件数: {stats['tracker']['total_files']}
  已同步: {stats['tracker']['synced_files']}
  待同步: {stats['tracker']['pending_files']}

同步统计:
  上传: {stats['sync']['uploads']}
  下载: {stats['sync']['downloads']}
  冲突: {stats['sync']['conflicts']}
""")
```

### 元数据导入导出

```python
from src.storage.distributed import get_distributed_storage

storage = get_distributed_storage()

# 导出元数据
success = storage.export_metadata("backup/metadata.json")
if success:
    print("元数据已导出")

# 导入元数据
count = storage.import_metadata("backup/metadata.json")
print(f"成功导入 {count} 个文件元数据")
```

---

## API 接口

### REST API

#### 上传文件
```http
POST /api/storage/upload
Content-Type: multipart/form-data

file: <document.pdf>
broadcast: true
```

#### 下载文件
```http
GET /api/storage/files/{file_id}
```

#### 列出文件
```http
GET /api/storage/files?device_id={device_id}
```

#### 删除文件
```http
DELETE /api/storage/files/{file_id}
```

#### 搜索文件
```http
GET /api/storage/search?query=report
```

#### 获取统计信息
```http
GET /api/storage/statistics
```

---

## 配置选项

```yaml
# config/storage.yaml
storage:
  distributed:
    data_dir: "data/storage"
    local_storage_dir: "data/storage/files"
    cache_dir: "data/storage/cache"
    max_cache_size: 1073741824  # 1GB
    
  sync:
    enabled: true
    auto_sync: true
    sync_interval: 300  # 5分钟
    conflict_resolution: "newest"  # newest, largest, manual
    
  file_tracker:
    max_file_size: 104857600  # 100MB
    allowed_types: ["*"]
    excluded_types: [".tmp", ".cache"]
```

---

## 同步协议

### 文件同步流程

```
┌──────────┐                    ┌──────────┐
│ Device A │                    │ Device B │
└────┬─────┘                    └────┬─────┘
     │                               │
     │  1. 上传文件                   │
     │  2. 广播元数据                  │
     ├──────────────────────────────►│
     │                               │
     │                               │  3. 接收元数据
     │                               │  4. 请求文件
     │◄──────────────────────────────┤
     │  5. 传输文件                   │
     │                               │
     │                               │  6. 保存文件
```

### 冲突解决策略

```python
# 最新版本优先
conflict_resolution: "newest"

# 最大文件优先
conflict_resolution: "largest"

# 手动解决
conflict_resolution: "manual"
```

---

## 最佳实践

### 1. 大文件处理

```python
from src.storage.distributed import get_distributed_storage

storage = get_distributed_storage()

# 检查文件大小
import os
file_size = os.path.getsize("large_file.zip")

if file_size > 100 * 1024 * 1024:  # 100MB
    print("文件过大，建议使用分片上传")
else:
    metadata = storage.upload_file("large_file.zip")
```

### 2. 批量操作

```python
from src.storage.distributed import get_distributed_storage
import os

storage = get_distributed_storage()

# 批量上传
for filename in os.listdir("uploads"):
    filepath = os.path.join("uploads", filename)
    if os.path.isfile(filepath):
        metadata = storage.upload_file(filepath)
        print(f"已上传: {filename}")
```

### 3. 定期同步检查

```python
import asyncio
from src.storage.distributed import get_distributed_storage

async def sync_check():
    storage = get_distributed_storage()
    
    while True:
        stats = storage.get_storage_stats()
        
        if stats['tracker']['pending_files'] > 0:
            print(f"有 {stats['tracker']['pending_files']} 个文件待同步")
        
        if stats['sync']['conflicts'] > 0:
            print(f"有 {stats['sync']['conflicts']} 个冲突需要解决")
        
        await asyncio.sleep(300)  # 5分钟

asyncio.run(sync_check())
```

---

## 故障排除

### 常见问题

**Q: 文件同步失败？**  
A: 检查网络连接和域系统状态，确保设备在同一域内。

**Q: 文件冲突频繁？**  
A: 调整冲突解决策略，或增加同步频率。

**Q: 存储空间不足？**  
A: 清理缓存目录，或调整 `max_cache_size` 配置。

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持文件上传下载
- 支持跨设备同步
- 支持冲突解决
- 支持元数据管理

---

## 相关文档

- [域系统](./domain-system.md) - 多设备管理
- [设备 ID](./device-id.md) - 设备标识
- [API 文档](../api.md) - 完整 API 参考
