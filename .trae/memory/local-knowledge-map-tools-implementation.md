# 本地百科与地图工具实现记录

## 任务概述

为 PyAgent 增加本地百科工具和离线地图工具，参考 Project N.O.M.A.D. 项目实现。

## 完成路径

### 1. 数据搬运

从 Project N.O.M.A.D. 项目搬运以下数据文件：
- `collections/wikipedia.json` -> `data/knowledge/wikipedia.json`
- `collections/kiwix-categories.json` -> `data/knowledge/kiwix-categories.json`
- `collections/maps.json` -> `data/knowledge/maps.json`

### 2. 目录结构创建

```
src/execution/tools/
├── knowledge/
│   ├── __init__.py
│   ├── zim_parser.py      # ZIM文件解析器
│   └── knowledge_tool.py  # 百科知识检索工具
└── map/
    ├── __init__.py
    ├── geo_utils.py       # 地理计算工具
    └── offline_map_tool.py # 离线地图工具

data/
├── knowledge/
│   ├── zim/               # ZIM文件存储目录
│   ├── wikipedia.json     # Wikipedia选项配置
│   └── kiwix-categories.json # Kiwix分类数据
└── maps/
    ├── pmtiles/           # PMTiles地图文件目录
    └── assets/            # 地图资源目录

config/
├── knowledge.yaml         # 百科工具配置
└── map.yaml               # 地图工具配置
```

### 3. 核心实现

#### 百科工具 (KnowledgeTool)
- 支持操作：search, get, list, categories, wikipedia_options
- ZIM文件解析器支持文件头解析、文章索引读取、内容提取
- 集成 Kiwix 分类数据（医学、教育、DIY等6大分类）

#### 地图工具 (OfflineMapTool)
- 支持操作：search, nearby, reverse_geocode, distance, regions, collections
- 内置8个中国主要城市POI数据
- 地理计算工具支持Haversine距离、方位角、边界框计算

### 4. 工具注册

- 在 `ToolCategory` 枚举中新增 `KNOWLEDGE` 和 `MAP` 类别
- 在 `registry.py` 中自动注册新工具
- 工具目录自动支持新类别展示

### 5. 测试

- `tests/test_knowledge_tool.py` - 百科工具测试
- `tests/test_map_tool.py` - 地图工具测试

## 可优化点

1. **ZIM解析器优化**
   - 当前仅支持未压缩的blob，需要添加LZMA/ZSTD压缩支持
   - 需要优化大文件的内存映射处理
   - 可以添加增量索引构建

2. **地图工具增强**
   - 添加PMTiles格式解析器
   - 添加本地地图瓦片服务
   - 支持自定义POI数据导入

3. **数据同步**
   - 添加从Kiwix自动下载ZIM文件的功能
   - 添加地图数据自动更新机制

4. **性能优化**
   - 添加搜索结果缓存
   - 优化大文件读取性能
   - 支持异步并发搜索

## 参考项目

- [Project N.O.M.A.D.](https://github.com/Crosstalk-Solutions/project-nomad) - 离线百科和地图服务
- [Kiwix](https://kiwix.org/) - 离线内容阅读器
- [Protomaps](https://protomaps.com/) - 离线地图格式
