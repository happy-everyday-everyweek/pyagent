此次合并主要进行了版本号更新和代码组织优化，同时新增了文档编码修复工具。变更涉及多个模块的导入语句调整和文件结构优化，提升了代码的可维护性。
| 文件 | 变更 |
|------|---------|
| pyproject.toml | - 版本号从 0.9.10 升级到 0.9.11 |
| fix_doc_encoding.py | - 新增文档编码修复工具，支持自动检测文件编码并转换为 UTF-8 |
| src/core/__init__.py | - 调整导入语句，从 collections.abc 导入 Callable 替代 typing 模块 |
| src/browser/__init__.py | - 重新组织导入语句和 __all__ 列表顺序，提升代码结构清晰度 |
| src/execution/__init__.py | - 重新组织 __all__ 列表顺序，使其更加结构化 |