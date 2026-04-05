"""
PyAgent - Python Agent智能体系统

主入口文件。
"""

import asyncio
import logging
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_data_directories() -> None:
    """初始化数据目录"""
    directories = [
        Path("data"),
        Path("data/memory"),
        Path("data/logs"),
        Path("skills"),
        Path("config"),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    logger.info("Data directories initialized")


async def init_services() -> None:
    """初始化服务"""
    from src.llm import create_client_from_env
    from src.mcp import mcp_manager
    from src.skills import skill_loader

    logger.info("Initializing LLM client...")
    try:
        create_client_from_env()
        logger.info("LLM client initialized")
    except Exception as e:
        logger.warning(f"LLM client initialization failed: {e}")

    logger.info("Loading MCP servers...")
    config_path = Path("config/mcp.json")
    if config_path.exists():
        count = await mcp_manager.reload_config(config_path)
        logger.info(f"Loaded {count} MCP server configurations")

    logger.info("Loading skills...")
    count = skill_loader.load_all()
    logger.info(f"Loaded {count} skills")

    logger.info("Services initialized")


async def run_im_mode() -> None:
    """运行IM模式"""
    from src.im import message_router
    from src.im.dingtalk import DingTalkAdapter
    from src.im.feishu import FeishuAdapter
    from src.im.onebot import OneBotAdapter
    from src.im.wecom import WeComAdapter

    ws_url = os.getenv("ONEBOT_WS_URL", "")
    if ws_url:
        adapter = OneBotAdapter(
            ws_url=ws_url,
            access_token=os.getenv("ONEBOT_ACCESS_TOKEN", ""),
            platform_name=os.getenv("ONEBOT_PLATFORM", "qq")
        )
        message_router.register_adapter(adapter)

    dingtalk_webhook = os.getenv("DINGTALK_WEBHOOK", "")
    if dingtalk_webhook:
        adapter = DingTalkAdapter(
            webhook_url=dingtalk_webhook,
            secret=os.getenv("DINGTALK_SECRET", "")
        )
        message_router.register_adapter(adapter)

    feishu_app_id = os.getenv("FEISHU_APP_ID", "")
    if feishu_app_id:
        adapter = FeishuAdapter(
            app_id=feishu_app_id,
            app_secret=os.getenv("FEISHU_APP_SECRET", "")
        )
        message_router.register_adapter(adapter)

    wecom_corp_id = os.getenv("WECOM_CORP_ID", "")
    if wecom_corp_id:
        adapter = WeComAdapter(
            corp_id=wecom_corp_id,
            agent_id=os.getenv("WECOM_AGENT_ID", ""),
            secret=os.getenv("WECOM_SECRET", "")
        )
        message_router.register_adapter(adapter)

    results = await message_router.connect_all()
    logger.info(f"IM adapters connected: {results}")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down IM mode...")
        await message_router.disconnect_all()


def run_web_mode(host: str = "0.0.0.0", port: int = 8000) -> None:
    """运行Web模式"""
    logger.info(f"Starting web server on {host}:{port}")
    uvicorn.run(
        "src.web.app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="PyAgent - Python Agent智能体系统")
    parser.add_argument(
        "--mode",
        choices=["web", "im", "both"],
        default="web",
        help="运行模式: web, im, both"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Web服务器主机"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Web服务器端口"
    )

    args = parser.parse_args()

    init_data_directories()

    if args.mode == "web":
        run_web_mode(args.host, args.port)

    elif args.mode == "im":
        asyncio.run(init_services())
        asyncio.run(run_im_mode())

    elif args.mode == "both":
        asyncio.run(init_services())

        import threading
        web_thread = threading.Thread(
            target=run_web_mode,
            args=(args.host, args.port)
        )
        web_thread.daemon = True
        web_thread.start()

        asyncio.run(run_im_mode())


if __name__ == "__main__":
    main()
