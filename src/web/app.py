"""
PyAgent Web服务 - FastAPI应用

提供REST API和WebSocket接口，使用统一后端核心。
"""

import logging

from src.core import create_app
from src.core.platform import PlatformConfig

logger = logging.getLogger(__name__)

web_config = PlatformConfig(
    api_host="0.0.0.0",
    api_port=8000,
    enable_cors=True,
    cors_origins=["*"],
    debug=False,
    log_level="info",
    data_dir="data",
    config_dir="config",
    enable_hot_reload=True,
    enable_screen_tools=False,
    enable_notification=False,
    enable_sms=False,
)

app = create_app(
    config=web_config,
    title="PyAgent Web API",
    description="Python Agent Web API - Unified Backend",
    version="0.9.8"
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
