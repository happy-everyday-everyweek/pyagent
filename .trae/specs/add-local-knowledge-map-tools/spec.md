# 本地百科与地图工具 Spec

## Why

PyAgent 需要支持离线环境下的知识检索和地理位置查询功能。参考 Project N.O.M.A.D. 项目，增加本地百科工具（支持 ZIM 格式）和离线地图工具，使系统能够在无网络环境下提供百科知识搜索和地图查询服务。

## What Changes

- 新增本地百科工具模块，支持 ZIM 格式文件解析和知识检索
- 新增离线地图工具模块，支持本地地图数据存储和查询
- 新增配置文件支持百科和地图数据路径配置
- 新增数据目录结构支持百科和地图数据存储

## Impact

- Affected specs: 执行模块工具系统
- Affected code: 
  - `src/execution/tools/base.py` - 新增工具类别
  - `src/execution/tools/registry.py` - 工具注册
  - `src/execution/tools/catalog.py` - 工具目录生成

## ADDED Requirements

### Requirement: 本地百科工具

系统应提供本地百科工具，支持离线知识检索功能。

#### Scenario: 知识搜索
- **WHEN** 用户提供搜索关键词
- **THEN** 系统从本地 ZIM 文件中搜索匹配的知识条目

#### Scenario: 文章获取
- **WHEN** 用户请求获取特定文章内容
- **THEN** 系统从 ZIM 文件中提取并返回文章完整内容

#### Scenario: 百科库管理
- **WHEN** 用户查询可用的百科库
- **THEN** 系统返回已安装的百科数据集列表

#### Scenario: 无匹配结果
- **WHEN** 搜索词在本地知识库中无匹配
- **THEN** 系统返回提示信息，建议用户扩展知识库

### Requirement: 离线地图工具

系统应提供离线地图工具，支持本地地图数据查询。

#### Scenario: POI搜索
- **WHEN** 用户提供关键词和可选的区域范围
- **THEN** 系统从本地地图数据中搜索匹配的 POI（兴趣点）

#### Scenario: 逆地理编码
- **WHEN** 用户提供经纬度坐标
- **THEN** 系统返回对应的地址信息

#### Scenario: 区域查询
- **WHEN** 用户指定一个地理区域范围
- **THEN** 系统返回该区域内的 POI 列表

#### Scenario: 距离计算
- **WHEN** 用户提供两个地理坐标
- **THEN** 系统返回两点之间的距离

## MODIFIED Requirements

### Requirement: 工具注册系统

现有工具注册系统需要支持新的百科和地图工具类别。

- 在 `ToolCategory` 枚举中新增 `KNOWLEDGE` 和 `MAP` 类别
- 工具目录生成时支持新类别的展示

## REMOVED Requirements

无移除的需求。
