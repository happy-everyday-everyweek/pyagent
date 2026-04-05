# Tasks

## Phase 1: 基础设施

- [x] Task 1.1: 创建百科工具模块目录结构
  - 创建 `src/execution/tools/knowledge/` 目录
  - 创建 `__init__.py` 文件
  - 创建 `zim_parser.py` ZIM文件解析器
  - 创建 `knowledge_tool.py` 百科工具实现

- [x] Task 1.2: 创建地图工具模块目录结构
  - 创建 `src/execution/tools/map/` 目录
  - 创建 `__init__.py` 文件
  - 创建 `offline_map_tool.py` 离线地图工具实现
  - 创建 `geo_utils.py` 地理计算工具

- [x] Task 1.3: 更新工具类别枚举
  - 在 `src/execution/tools/base.py` 的 `ToolCategory` 中添加 `KNOWLEDGE` 和 `MAP` 类别

## Phase 2: 百科工具实现

- [x] Task 2.1: 实现 ZIM 文件解析器
  - 解析 ZIM 文件头信息
  - 实现文章索引读取
  - 实现文章内容提取
  - 支持全文搜索

- [x] Task 2.2: 实现百科知识检索工具
  - 继承 BaseTool 基类
  - 实现知识搜索功能
  - 实现文章获取功能
  - 实现百科库管理功能

- [x] Task 2.3: 创建百科数据存储目录
  - 在 `data/knowledge/` 创建数据目录
  - 创建配置文件 `config/knowledge.yaml`

## Phase 3: 地图工具实现

- [x] Task 3.1: 实现离线地图数据结构
  - 定义 POI 数据模型
  - 定义地理区域数据模型
  - 定义地址数据模型

- [x] Task 3.2: 实现离线地图工具
  - 继承 BaseTool 基类
  - 实现 POI 搜索功能
  - 实现逆地理编码功能
  - 实现区域查询功能

- [x] Task 3.3: 创建地图数据存储目录
  - 在 `data/maps/` 创建数据目录
  - 创建配置文件 `config/map.yaml`
  - 创建示例地图数据文件

## Phase 4: 工具注册与集成

- [x] Task 4.1: 注册百科工具到工具注册中心
  - 在 `src/execution/tools/__init__.py` 中导入并注册百科工具

- [x] Task 4.2: 注册地图工具到工具注册中心
  - 在 `src/execution/tools/__init__.py` 中导入并注册地图工具

- [x] Task 4.3: 更新工具目录生成
  - 更新 `catalog.py` 支持新工具类别

## Phase 5: 测试与文档

- [x] Task 5.1: 编写百科工具测试
  - 创建 `tests/test_knowledge_tool.py`
  - 测试 ZIM 解析功能
  - 测试知识检索功能

- [x] Task 5.2: 编写地图工具测试
  - 创建 `tests/test_map_tool.py`
  - 测试 POI 搜索功能
  - 测试地理计算功能

# Task Dependencies

- Task 1.3 依赖 Task 1.1 和 Task 1.2
- Task 2.2 依赖 Task 1.1 和 Task 2.1
- Task 3.2 依赖 Task 1.2 和 Task 3.1
- Task 4.1 依赖 Task 2.2
- Task 4.2 依赖 Task 3.2
- Task 4.3 依赖 Task 4.1 和 Task 4.2
- Task 5.1 依赖 Task 4.1
- Task 5.2 依赖 Task 4.2
