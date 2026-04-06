"""
PyAgent 移动端模块 - 移动端后端

使用统一后端核心，提供移动设备特定的配置和功能。
v0.9.8: 重构为使用统一后端核心
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from src.core import create_app
from src.core.platform import PlatformConfig, get_platform_adapter

logger = logging.getLogger(__name__)


class MobileBackend:
    """移动端后端管理器

    负责初始化和管理移动端后端服务，使用统一后端核心。
    """

    _instance: Optional["MobileBackend"] = None

    def __new__(cls, config: Optional[PlatformConfig] = None) -> "MobileBackend":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[PlatformConfig] = None):
        if self._initialized:
            return

        self._config = config or PlatformConfig(
            api_host="127.0.0.1",
            api_port=8080,
            enable_cors=True,
            debug=False,
            log_level="info",
            data_dir="data/mobile",
            config_dir="config",
            enable_hot_reload=False,
            enable_screen_tools=True,
            enable_notification=True,
            enable_sms=True,
        )
        self._app = None
        self._server = None
        self._logger = logging.getLogger(__name__)
        self._initialized = True

    @property
    def config(self) -> PlatformConfig:
        return self._config

    @property
    def api_endpoint(self) -> str:
        return f"http://{self._config.api_host}:{self._config.api_port}"

    def initialize(self) -> bool:
        """初始化移动端后端"""
        self._logger.info("Initializing mobile backend...")

        try:
            data_dir = Path(self._config.data_dir)
            data_dir.mkdir(parents=True, exist_ok=True)

            self._app = create_app(
                config=self._config,
                title="PyAgent Mobile API",
                description="Python Agent Mobile API - Unified Backend",
                version="0.9.8"
            )

            self._logger.info("Mobile backend initialized successfully")
            return True

        except Exception as e:
            self._logger.error(f"Failed to initialize mobile backend: {e}")
            return False

    def get_app(self):
        """获取FastAPI应用实例"""
        if self._app is None:
            self.initialize()
        return self._app

    async def start_async(self) -> bool:
        """异步启动移动端后端"""
        if self._app is None:
            if not self.initialize():
                return False

        try:
            import uvicorn
            config = uvicorn.Config(
                app=self._app,
                host=self._config.api_host,
                port=self._config.api_port,
                log_level=self._config.log_level,
            )
            self._server = uvicorn.Server(config)
            self._logger.info(f"Mobile backend started on {self.api_endpoint}")
            await self._server.serve()
            return True

        except Exception as e:
            self._logger.error(f"Failed to start mobile backend: {e}")
            return False

    def start(self) -> bool:
        """启动移动端后端（同步）"""
        try:
            asyncio.run(self.start_async())
            return True
        except Exception as e:
            self._logger.error(f"Failed to start mobile backend: {e}")
            return False

    def stop(self) -> bool:
        """停止移动端后端"""
        if self._server:
            self._server.should_exit = True
            self._logger.info("Mobile backend stopped")
        return True

    def get_status_info(self) -> dict[str, Any]:
        """获取状态信息"""
        adapter = get_platform_adapter()
        return {
            "status": "running" if self._server else "stopped",
            "api_endpoint": self.api_endpoint,
            "config": self._config.to_dict(),
            "platform": adapter.get_status_info(),
        }

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例（仅用于测试）"""
        cls._instance = None


mobile_backend = MobileBackend()
