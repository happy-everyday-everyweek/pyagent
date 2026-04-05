# PyAgent 浏览器自动化

**版本**: v0.8.0  
**模块路径**: `src/browser/`  
**最后更新**: 2025-04-03

---

## 概述

浏览器自动化是 PyAgent v0.8.0 引入的全新模块，基于 Playwright 提供强大的浏览器控制能力。支持页面导航、元素操作、截图、执行 JavaScript、Cookie 管理等完整浏览器自动化功能。

### 核心特性

- **多浏览器支持**: Chromium、Firefox、WebKit
- **页面操作**: 导航、刷新、前进、后退
- **元素交互**: 点击、输入、等待、截图
- **JavaScript 执行**: 在页面上下文中执行脚本
- **数据提取**: 页面内容、Cookie、LocalStorage
- **会话管理**: Cookie 持久化、多页面管理

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                  Browser Automation System                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              BrowserController                      │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  Playwright  │  │   Browser    │                │   │
│  │  │   (驱动)      │  │   (实例)      │                │   │
│  │  └──────────────┘  └──────┬───────┘                │   │
│  │                           │                        │   │
│  │                    ┌──────┴───────┐                │   │
│  │                    ▼              ▼                │   │
│  │              ┌─────────┐    ┌─────────┐           │   │
│  │              │ Context │    │  Page   │           │   │
│  │              │(上下文) │    │ (页面)  │           │   │
│  │              └─────────┘    └─────────┘           │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              BrowserSession                         │   │
│  │         (会话数据: Cookies, LocalStorage)            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 浏览器控制器 (BrowserController)

**位置**: `src/browser/controller.py`

```python
from src.browser.controller import BrowserController, BrowserConfig, BrowserType

# 使用默认配置
controller = BrowserController()

# 或自定义配置
config = BrowserConfig(
    browser_type=BrowserType.CHROMIUM,
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    timeout=30000,
)
controller = BrowserController(config)
```

#### BrowserConfig 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `browser_type` | BrowserType | CHROMIUM | 浏览器类型 |
| `headless` | bool | True | 无头模式 |
| `viewport_width` | int | 1920 | 视口宽度 |
| `viewport_height` | int | 1080 | 视口高度 |
| `timeout` | int | 30000 | 超时时间（毫秒） |
| `slow_mo` | int | 0 | 慢动作延迟（毫秒） |
| `proxy` | dict | {} | 代理配置 |
| `ignore_https_errors` | bool | False | 忽略 HTTPS 错误 |

#### 主要方法

```python
# 启动浏览器
session = await controller.launch(headless=True)

# 关闭浏览器
success = await controller.close()

# 页面导航
url = await controller.navigate("https://example.com", wait_until="load")

# 获取当前URL
current_url = await controller.get_current_url()

# 截图
screenshot = await controller.take_screenshot(
    full_page=False,
    save_path="screenshot.png",
    return_base64=True
)

# 执行 JavaScript
result = await controller.execute_script("document.title")

# 等待元素
found = await controller.wait_for_selector("#submit", timeout=5000)

# 获取页面内容
html = await controller.get_page_content()
title = await controller.get_page_title()

# 页面操作
await controller.reload()
await controller.go_back()
await controller.go_forward()

# Cookie 管理
await controller.set_cookies([{"name": "session", "value": "xxx"}])
cookies = await controller.get_cookies()

# LocalStorage
await controller.set_local_storage("key", "value")
value = await controller.get_local_storage("key")
all_storage = await controller.get_local_storage()
```

---

### 2. 浏览器类型

```python
class BrowserType(Enum):
    CHROMIUM = "chromium"   # Chrome/Edge
    FIREFOX = "firefox"     # Firefox
    WEBKIT = "webkit"       # Safari
```

---

## 使用示例

### 基础页面操作

```python
import asyncio
from src.browser.controller import BrowserController

async def basic_example():
    controller = BrowserController()
    
    # 启动浏览器
    await controller.launch()
    
    # 导航到页面
    await controller.navigate("https://example.com")
    
    # 获取标题
    title = await controller.get_page_title()
    print(f"页面标题: {title}")
    
    # 截图
    screenshot = await controller.take_screenshot(
        save_path="example.png",
        full_page=True
    )
    
    # 关闭浏览器
    await controller.close()

asyncio.run(basic_example())
```

### 使用上下文管理器

```python
import asyncio
from src.browser.controller import BrowserController

async def context_example():
    async with BrowserController() as controller:
        await controller.navigate("https://example.com")
        
        # 执行 JavaScript
        result = await controller.execute_script("""
            return {
                title: document.title,
                url: window.location.href,
                width: window.innerWidth,
                height: window.innerHeight
            }
        """)
        print(result)

asyncio.run(context_example())
```

### 表单填写示例

```python
import asyncio
from src.browser.controller import BrowserController

async def form_example():
    controller = BrowserController(headless=False)
    await controller.launch()
    
    # 导航到登录页
    await controller.navigate("https://example.com/login")
    
    # 等待表单元素
    await controller.wait_for_selector("#username")
    await controller.wait_for_selector("#password")
    
    # 填写表单（使用 Playwright 的 page 对象）
    await controller.page.fill("#username", "myuser")
    await controller.page.fill("#password", "mypassword")
    
    # 点击登录按钮
    await controller.page.click("#login-button")
    
    # 等待页面跳转
    await controller.page.wait_for_load_state("networkidle")
    
    # 验证登录成功
    welcome = await controller.page.text_content(".welcome-message")
    print(f"欢迎消息: {welcome}")
    
    await controller.close()

asyncio.run(form_example())
```

### 数据抓取示例

```python
import asyncio
from src.browser.controller import BrowserController

async def scraping_example():
    controller = BrowserController()
    await controller.launch()
    
    # 导航到目标页面
    await controller.navigate("https://news.example.com")
    
    # 等待内容加载
    await controller.wait_for_selector(".article")
    
    # 提取数据
    articles = await controller.page.eval_on_selector_all(".article", """
        elements => elements.map(el => ({
            title: el.querySelector('h2').textContent,
            summary: el.querySelector('.summary').textContent,
            link: el.querySelector('a').href
        }))
    """)
    
    for article in articles:
        print(f"标题: {article['title']}")
        print(f"摘要: {article['summary']}")
        print(f"链接: {article['link']}")
        print("-" * 40)
    
    await controller.close()

asyncio.run(scraping_example())
```

### Cookie 和会话管理

```python
import asyncio
from src.browser.controller import BrowserController

async def session_example():
    controller = BrowserController()
    await controller.launch()
    
    # 设置登录 Cookie
    await controller.set_cookies([
        {
            "name": "session_id",
            "value": "abc123",
            "domain": ".example.com",
            "path": "/"
        },
        {
            "name": "user_id",
            "value": "12345",
            "domain": ".example.com",
            "path": "/"
        }
    ])
    
    # 导航到需要登录的页面
    await controller.navigate("https://example.com/dashboard")
    
    # 获取当前 Cookie
    cookies = await controller.get_cookies()
    print(f"当前 Cookie: {cookies}")
    
    # 使用 LocalStorage
    await controller.set_local_storage("user_pref", "dark_mode")
    pref = await controller.get_local_storage("user_pref")
    print(f"用户偏好: {pref}")
    
    await controller.close()

asyncio.run(session_example())
```

---

## API 接口

### REST API

#### 启动浏览器
```http
POST /api/browser/launch
Content-Type: application/json

{
  "headless": true,
  "browser_type": "chromium"
}
```

#### 导航到页面
```http
POST /api/browser/navigate
Content-Type: application/json

{
  "url": "https://example.com",
  "wait_until": "load"
}
```

#### 截图
```http
POST /api/browser/screenshot
Content-Type: application/json

{
  "full_page": true,
  "save_path": "screenshot.png"
}
```

#### 执行脚本
```http
POST /api/browser/execute
Content-Type: application/json

{
  "script": "document.title"
}
```

#### 关闭浏览器
```http
POST /api/browser/close
```

---

## 配置选项

```yaml
# config/browser.yaml
browser:
  default:
    browser_type: "chromium"
    headless: true
    viewport:
      width: 1920
      height: 1080
    timeout: 30000
    slow_mo: 0
    downloads_path: "data/downloads"
    ignore_https_errors: false
  
  proxy:
    server: "http://proxy.example.com:8080"
    username: "${PROXY_USER}"
    password: "${PROXY_PASS}"
```

---

## 最佳实践

### 1. 错误处理

```python
import asyncio
from src.browser.controller import BrowserController

async def safe_browser_operation():
    controller = BrowserController()
    try:
        await controller.launch()
        await controller.navigate("https://example.com")
        # ... 操作
    except Exception as e:
        print(f"浏览器操作失败: {e}")
    finally:
        await controller.close()
```

### 2. 等待策略

```python
# 等待元素可见
await controller.wait_for_selector("#submit", state="visible")

# 等待元素隐藏
await controller.wait_for_selector("#loading", state="hidden")

# 等待网络空闲
await controller.page.wait_for_load_state("networkidle")
```

### 3. 性能优化

```python
# 使用无头模式提高性能
config = BrowserConfig(headless=True)

# 禁用图片加载加快页面加载
config.args = ["--blink-settings=imagesEnabled=false"]

# 复用浏览器实例
controller = BrowserController()
await controller.launch()

# 在多个页面间切换
page1 = await controller.context.new_page()
page2 = await controller.context.new_page()
```

---

## 故障排除

### 常见问题

**Q: Playwright 未安装？**  
A: 运行 `pip install playwright && playwright install`

**Q: 浏览器启动失败？**  
A: 检查系统依赖，Linux 可能需要安装额外的库。

**Q: 页面加载超时？**  
A: 增加 `timeout` 配置，或检查网络连接。

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 基于 Playwright 实现
- 支持多浏览器
- 支持完整页面操作

---

## 相关文档

- [Playwright 官方文档](https://playwright.dev/python/)
- [API 文档](../api.md) - 完整 API 参考
