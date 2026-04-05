"""
PyAgent 测试配置
"""

import asyncio
import sys
from collections.abc import Generator
from pathlib import Path

import pytest


def pytest_configure(config):
    """配置pytest，添加src路径"""
    src_path = str(Path(__file__).parent.parent / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
