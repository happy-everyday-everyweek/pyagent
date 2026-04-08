import asyncio
from src.browser.controller import BrowserController

async def test_web_interface():
    print("Testing web interface...")
    controller = BrowserController()
    try:
        # 启动浏览器
        await controller.launch(headless=False)
        print(f"Browser launched: {controller.session.browser_type}")
        
        # 测试导航到主页
        await controller.navigate('http://localhost:5173/')
        title = await controller.get_page_title()
        print(f'Page loaded: {title}')
        
        # 测试导航到不同路由
        routes = ['/', '/tasks', '/config']
        for route in routes:
            await controller.navigate(f'http://localhost:5173{route}')
            current_url = await controller.get_current_url()
            print(f'Navigated to: {current_url}')
            
        # 测试页面内容
        content = await controller.get_page_content()
        print(f'Page content length: {len(content)} characters')
        
    finally:
        # 关闭浏览器
        await controller.close()

if __name__ == "__main__":
    asyncio.run(test_web_interface())
