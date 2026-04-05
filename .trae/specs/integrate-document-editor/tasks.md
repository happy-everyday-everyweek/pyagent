# Tasks

## Phase 1: 基础设施搭建

- [x] Task 1: 创建 OOXML 工具模块
  - [x] SubTask 1.1: 创建 `src/document/ooxml/` 目录结构
  - [x] SubTask 1.2: 迁移 XML 编辑器 (`xml_editor.py`)
  - [x] SubTask 1.3: 迁移打包工具 (`pack.py`)
  - [x] SubTask 1.4: 迁移解包工具 (`unpack.py`)
  - [x] SubTask 1.5: 迁移验证工具 (`validate.py`)
  - [ ] SubTask 1.6: 迁移 OOXML 模式文件 (`schemas/`)

- [x] Task 2: 更新项目依赖
  - [x] SubTask 2.1: 添加 Python 包依赖到 `requirements.txt`
  - [x] SubTask 2.2: 创建外部工具检测和配置模块

## Phase 2: DOCX 处理模块

- [x] Task 3: 创建 DOCX 处理模块基础结构
  - [x] SubTask 3.1: 创建 `src/document/docx/` 目录结构
  - [x] SubTask 3.2: 创建模块初始化文件和类型定义
  - [x] SubTask 3.3: 迁移模板文件 (`templates/`)

- [x] Task 4: 实现 DOCX 文档创建功能
  - [x] SubTask 4.1: 创建文档创建器 (`creator.py`)
  - [x] SubTask 4.2: 实现页面设置功能（大小、边距、方向）
  - [x] SubTask 4.3: 实现样式管理（标题、正文、列表）
  - [x] SubTask 4.4: 实现内容添加（段落、表格、图片）

- [x] Task 5: 实现 DOCX 文档编辑功能
  - [x] SubTask 5.1: 创建文档编辑器 (`editor.py`)
  - [x] SubTask 5.2: 实现文档解包和打包流程
  - [x] SubTask 5.3: 实现 XML 节点查找和修改
  - [x] SubTask 5.4: 实现内容替换和插入

- [x] Task 6: 实现 DOCX 批注管理功能
  - [x] SubTask 6.1: 创建批注管理器 (`comment.py`)
  - [x] SubTask 6.2: 实现添加批注功能
  - [x] SubTask 6.3: 实现回复批注功能
  - [x] SubTask 6.4: 实现删除批注功能

- [x] Task 7: 实现 DOCX 修订跟踪功能
  - [x] SubTask 7.1: 创建修订跟踪器 (`revision.py`)
  - [x] SubTask 7.2: 实现插入标记功能
  - [x] SubTask 7.3: 实现删除标记功能
  - [x] SubTask 7.4: 实现接受/拒绝修订功能

- [x] Task 8: 实现 DOCX 格式转换功能
  - [x] SubTask 8.1: 创建格式转换器 (`converter.py`)
  - [x] SubTask 8.2: 实现 DOCX 转 PDF
  - [x] SubTask 8.3: 实现 DOCX 转图片
  - [x] SubTask 8.4: 实现 DOC 转 DOCX

## Phase 3: PPTX 处理模块

- [x] Task 9: 创建 PPTX 处理模块基础结构
  - [x] SubTask 9.1: 创建 `src/document/pptx/` 目录结构
  - [x] SubTask 9.2: 创建模块初始化文件和类型定义
  - [ ] SubTask 9.3: 迁移设计模板 (`templates/`)

- [x] Task 10: 实现 PPTX 演示文稿创建功能
  - [x] SubTask 10.1: 创建演示文稿创建器 (`creator.py`)
  - [x] SubTask 10.2: 实现幻灯片布局设置
  - [x] SubTask 10.3: 实现主题颜色配置
  - [x] SubTask 10.4: 实现内容添加（文本、形状、图片、图表）

- [x] Task 11: 实现 PPTX 演示文稿编辑功能
  - [x] SubTask 11.1: 创建演示文稿编辑器 (`editor.py`)
  - [x] SubTask 11.2: 实现幻灯片添加/删除
  - [x] SubTask 11.3: 实现幻灯片重排
  - [x] SubTask 11.4: 实现内容修改

- [x] Task 12: 实现 PPTX 缩略图生成功能
  - [x] SubTask 12.1: 创建缩略图生成器 (`thumbnail.py`)
  - [x] SubTask 12.2: 实现幻灯片转图片
  - [x] SubTask 12.3: 实现缩略图网格生成

## Phase 4: PDF 处理模块

- [x] Task 13: 创建 PDF 处理模块基础结构
  - [x] SubTask 13.1: 创建 `src/document/pdf/` 目录结构
  - [x] SubTask 13.2: 创建模块初始化文件和类型定义

- [x] Task 14: 实现 PDF 文本和表格提取功能
  - [x] SubTask 14.1: 创建提取器 (`extractor.py`)
  - [x] SubTask 14.2: 实现文本提取
  - [x] SubTask 14.3: 实现表格提取
  - [x] SubTask 14.4: 实现元数据提取

- [x] Task 15: 实现 PDF 合并和拆分功能
  - [x] SubTask 15.1: 创建合并器 (`merger.py`)
  - [x] SubTask 15.2: 实现 PDF 合并
  - [x] SubTask 15.3: 实现 PDF 拆分
  - [x] SubTask 15.4: 实现页面旋转

- [x] Task 16: 实现 PDF 表单填写功能
  - [x] SubTask 16.1: 创建表单处理器 (`form.py`)
  - [x] SubTask 16.2: 实现表单字段识别
  - [x] SubTask 16.3: 实现表单填写
  - [x] SubTask 16.4: 实现表单导出

- [x] Task 17: 实现 PDF OCR 支持功能
  - [x] SubTask 17.1: 创建 OCR 处理器 (`ocr.py`)
  - [x] SubTask 17.2: 实现扫描 PDF 文字识别
  - [x] SubTask 17.3: 实现可搜索 PDF 生成

## Phase 4.5: XLSX 处理模块

- [x] Task 23: 创建 XLSX 处理模块基础结构
  - [x] SubTask 23.1: 创建 `src/document/xlsx/` 目录结构
  - [x] SubTask 23.2: 创建模块初始化文件和类型定义

- [x] Task 24: 实现 XLSX 工作簿创建功能
  - [x] SubTask 24.1: 创建工作簿创建器 (`creator.py`)
  - [x] SubTask 24.2: 实现工作表添加功能
  - [x] SubTask 24.3: 实现单元格数据写入

- [x] Task 25: 实现 XLSX 工作簿编辑功能
  - [x] SubTask 25.1: 创建工作簿编辑器 (`editor.py`)
  - [x] SubTask 25.2: 实现单元格读取和修改
  - [x] SubTask 25.3: 实现范围数据读取

- [x] Task 26: 实现 XLSX 工作表管理功能
  - [x] SubTask 26.1: 创建工作表管理器 (`sheet.py`)
  - [x] SubTask 26.2: 实现工作表添加/删除/重命名
  - [x] SubTask 26.3: 实现工作表移动和复制

- [x] Task 27: 实现 XLSX 图表管理功能
  - [x] SubTask 27.1: 创建图表管理器 (`chart.py`)
  - [x] SubTask 27.2: 实现图表添加功能
  - [x] SubTask 27.3: 支持多种图表类型

## Phase 5: 集成和增强

- [x] Task 18: 增强文档管理器
  - [x] SubTask 18.1: 添加格式转换接口
  - [x] SubTask 18.2: 添加批注管理接口
  - [x] SubTask 18.3: 添加修订跟踪接口
  - [x] SubTask 18.4: 添加版本管理功能

- [x] Task 19: 增强文档工具
  - [x] SubTask 19.1: 添加 DOCX 操作支持
  - [x] SubTask 19.2: 添加 PPTX 操作支持
  - [x] SubTask 19.3: 添加 PDF 操作支持
  - [x] SubTask 19.4: 集成 AI 辅助功能

- [x] Task 20: 更新 Web API 路由
  - [x] SubTask 20.1: 添加 DOCX API 端点
  - [x] SubTask 20.2: 添加 PPTX API 端点
  - [x] SubTask 20.3: 添加 PDF API 端点
  - [x] SubTask 20.4: 添加文件上传/下载支持

## Phase 6: 测试和文档

- [x] Task 21: 编写单元测试
  - [x] SubTask 21.1: DOCX 模块测试
  - [x] SubTask 21.2: PPTX 模块测试
  - [x] SubTask 21.3: PDF 模块测试
  - [x] SubTask 21.4: OOXML 工具测试

- [x] Task 22: 更新文档
  - [x] SubTask 22.1: 更新 `docs/modules/document-editor.md`
  - [x] SubTask 22.2: 更新 `CHANGELOG.md`
  - [x] SubTask 22.3: 更新 `AGENTS.md`

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3-8 依赖 Task 1, Task 2
- Task 9-12 依赖 Task 1, Task 2
- Task 13-17 依赖 Task 2
- Task 18-20 依赖 Task 3-17
- Task 21-22 依赖 Task 18-20

# Parallelizable Work

以下任务可以并行执行：
- Task 3-8 (DOCX 模块) 和 Task 9-12 (PPTX 模块) 和 Task 13-17 (PDF 模块)
- Task 21 和 Task 22 可以在各自模块完成后并行进行
