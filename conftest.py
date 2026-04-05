"""
PyAgent 测试配置 - 根目录

添加src路径到sys.path
"""

import sys
from pathlib import Path

src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
