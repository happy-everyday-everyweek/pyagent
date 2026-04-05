"""
Browser 工具定义

包含浏览器自动化相关的工具（遵循 tool-definition-spec.md 规范）：
- browser_navigate: 导航到 URL（搜索类任务推荐直接拼 URL 参数）
- browser_task: 智能浏览器任务（适合复杂交互，不适合简单搜索）
- browser_open: 启动浏览器 + 状态查询
- browser_get_content: 获取页面内容
- browser_screenshot: 截取页面截图
- view_image: 查看/分析本地图片
- browser_close: 关闭浏览器
"""

from .base import build_detail

# ==================== 工具定义 ====================

BROWSER_TOOLS = [
    # ---------- browser_task ----------
    {
        "name": "browser_task",
        "category": "Browser",
        "description": "Intelligent browser task - delegates to browser-use Agent for complex multi-step interactions. Best for: (1) Complex workflows like login + fill form + submit, (2) Tasks requiring multiple clicks and interactions on the SAME page. **NOT recommended for search tasks** - use browser_navigate with URL params instead (e.g. https://www.baidu.com/s?wd=keyword). If browser_task fails once, switch to manual steps (browser_navigate + browser_get_content).",
        "related_tools": [
            {"name": "web_search", "relation": "仅需快速获取搜索结果（无需页面交互）时改用 web_search，更快更省资源"},
            {"name": "browser_navigate", "relation": "搜索类任务优先使用，拼 URL 参数直达"},
            {
                "name": "view_image",
                "relation": "browser_task 完成后务必截图+view_image 验证结果",
            },
        ],
        "detail": build_detail(
            summary="智能浏览器任务 - 委托 browser-use Agent 自动执行复杂交互。",
            scenarios=[
                "复杂网页交互（如：登录 → 填表 → 提交）",
                "需要多次点击、选择的操作（如：筛选 → 排序 → 翻页）",
                "不确定具体步骤的复杂任务",
            ],
            params_desc={
                "task": "要完成的任务描述，越详细越好。例如：'登录后填写表单并提交'",
                "max_steps": "最大执行步骤数，默认15步。复杂任务可以增加。",
            },
            workflow_steps=[
                "描述你想完成的任务",
                "browser-use Agent 自动分析任务",
                "自动规划执行步骤",
                "逐步执行并处理异常",
                "返回执行结果",
            ],
            notes=[
                "⚠️ 搜索类任务请不要用 browser_task！直接用 browser_navigate 拼 URL 参数更可靠",
                "⚠️ 如果 browser_task 失败 1 次，立即切换为手动分步操作",
                "适合需要多次 UI 交互的复杂场景（登录、填表、筛选等）",
                "通过 CDP 复用已启动的浏览器",
                "任务描述要清晰具体，避免歧义",
                "任务完成后用 browser_screenshot + view_image 验证结果",
            ],
        ),
        "triggers": [
            "When task involves complex multi-step UI interactions (login, form filling, etc.)",
            "When exact steps are unclear and the task requires intelligent planning",
            "When managing multiple tabs or complex page interactions",
        ],
        "prerequisites": [],
        "warnings": [
            "Do NOT use for search tasks - use browser_navigate with URL params instead",
            "If browser_task fails once, immediately switch to manual browser tools",
            "Always verify results with browser_screenshot + view_image after completion",
        ],
        "examples": [
            {
                "scenario": "淘宝筛选排序（复杂交互）",
                "params": {
                    "task": "在淘宝商品列表页筛选价格200-500元，按销量排序"
                },
                "expected": "Agent automatically: filters price → sorts by sales",
            },
            {
                "scenario": "表单填写",
                "params": {"task": "填写注册表单：用户名test，邮箱test@example.com，点击提交"},
                "expected": "Agent fills form fields and submits",
            },
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "要完成的任务描述，例如：'打开淘宝搜索机械键盘，筛选价格200-500元，按销量排序'",
                },
                "max_steps": {
                    "type": "integer",
                    "description": "最大执行步骤数，默认15。复杂任务可以增加。",
                    "default": 15,
                },
            },
            "required": ["task"],
        },
    },
    # ---------- browser_open ---------- (合并了 browser_status)
    {
        "name": "browser_open",
        "category": "Browser",
        "description": "Launch browser OR check browser status. Always returns current state (is_open, url, title, tab_count). If browser is already running, returns status without restarting. If not running, starts it. Call this before any browser operation to ensure browser is ready. Browser state resets on service restart.",
        "detail": build_detail(
            summary="启动浏览器或检查浏览器状态。始终返回当前状态（是否打开、URL、标题、tab 数）。",
            scenarios=[
                "开始 Web 自动化任务前确认浏览器状态",
                "启动浏览器",
                "检查浏览器是否正常运行",
            ],
            params_desc={
                "visible": "True=显示浏览器窗口（用户可见），False=后台运行（不可见）",
            },
            notes=[
                "⚠️ 每次浏览器任务前建议调用此工具确认状态",
                "如果浏览器已在运行，直接返回当前状态，不会重复启动",
                "服务重启后浏览器会关闭，不能假设已打开",
                "默认显示浏览器窗口",
            ],
        ),
        "triggers": [
            "Before any browser operation",
            "When starting web automation tasks",
            "When checking if browser is running",
        ],
        "prerequisites": [],
        "warnings": [
            "Browser state resets on service restart - never assume it's open from history",
        ],
        "examples": [
            {
                "scenario": "检查浏览器状态并启动",
                "params": {},
                "expected": "Returns {is_open: true/false, url: '...', title: '...', tab_count: N}. Starts browser if not running.",
            },
            {
                "scenario": "启动可见浏览器",
                "params": {"visible": True},
                "expected": "Browser window opens and is visible to user, returns status",
            },
            {
                "scenario": "后台模式启动",
                "params": {"visible": False},
                "expected": "Browser runs in background without visible window, returns status",
            },
        ],
        "related_tools": [
            {"name": "browser_navigate", "relation": "打开后导航到目标 URL（搜索任务推荐直接拼 URL 参数）"},
            {"name": "browser_task", "relation": "仅在需要复杂 UI 交互时使用"},
            {"name": "browser_close", "relation": "使用完毕后关闭"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "visible": {
                    "type": "boolean",
                    "description": "True=显示浏览器窗口, False=后台运行。默认 True",
                    "default": True,
                },
            },
            "required": [],
        },
    },
    # ---------- browser_navigate ----------
    {
        "name": "browser_navigate",
        "category": "Browser",
        "description": "Navigate browser to URL. **Recommended for search tasks** - directly use URL with query params (e.g. https://www.baidu.com/s?wd=keyword, https://image.baidu.com/search/index?tn=baiduimage&word=keyword, https://www.google.com/search?q=keyword). Much more reliable than browser_task for searches. Auto-starts browser if not running.",
        "detail": build_detail(
            summary="导航到指定 URL。搜索类任务推荐直接拼 URL 参数，比 browser_task 更可靠。",
            scenarios=[
                "搜索类任务：直接用 URL 参数（如 baidu.com/s?wd=关键词）",
                "打开网页查看内容",
                "Web 自动化任务的第一步",
                "切换到新页面",
            ],
            params_desc={
                "url": "要访问的完整 URL（必须包含协议，如 https://）",
            },
            workflow_steps=[
                "调用此工具导航到目标页面",
                "等待页面加载",
                "使用 browser_get_content 获取内容 或 browser_screenshot 截图",
            ],
            notes=[
                "⚠️ 搜索类任务优先用此工具，直接在 URL 中带搜索参数",
                "常用搜索 URL 模板：百度搜索 https://www.baidu.com/s?wd=关键词",
                "百度图片 https://image.baidu.com/search/index?tn=baiduimage&word=关键词",
                "Google https://www.google.com/search?q=keyword",
                "如果浏览器未启动会自动启动",
                "URL 必须包含协议（http:// 或 https://）",
            ],
        ),
        "triggers": [
            "When user asks to search for something on the web",
            "When user asks to open a webpage",
            "When starting web automation task with a known URL",
            "When browser_task has failed - use URL params as fallback",
        ],
        "prerequisites": [],
        "warnings": [],
        "examples": [
            {
                "scenario": "打开搜索引擎",
                "params": {"url": "https://www.google.com"},
                "expected": "Browser navigates to Google homepage",
            },
            {
                "scenario": "打开本地文件",
                "params": {"url": "file:///C:/Users/test.html"},
                "expected": "Browser opens local HTML file",
            },
        ],
        "related_tools": [
            {"name": "browser_get_content", "relation": "导航后获取页面文本内容"},
            {"name": "browser_screenshot", "relation": "导航后截图"},
            {"name": "view_image", "relation": "截图后查看图片内容，验证页面状态"},
            {"name": "browser_task", "relation": "仅在需要复杂 UI 交互（登录、填表）时使用"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "要访问的 URL（必须包含协议）。搜索类任务直接在 URL 中带参数"},
            },
            "required": ["url"],
        },
    },
    # ---------- browser_get_content ----------
    {
        "name": "browser_get_content",
        "category": "Browser",
        "description": "Extract page content and element text from current webpage. When you need to: (1) Read page information, (2) Get element values, (3) Scrape data, (4) Verify page content.",
        "detail": build_detail(
            summary="获取页面内容（文本或 HTML）。",
            scenarios=[
                "读取页面信息",
                "获取元素值",
                "抓取数据",
                "验证页面内容",
            ],
            params_desc={
                "selector": "元素选择器（可选，不填则获取整个页面）",
                "format": "返回格式：text（纯文本，默认）或 html（HTML 源码）",
            },
            notes=[
                "不指定 selector：获取整个页面文本",
                "指定 selector：获取特定元素的文本",
                "format 默认为 text，如需 HTML 源码请指定为 html",
            ],
        ),
        "triggers": [
            "When reading page information",
            "When extracting data from webpage",
            "When verifying page content after navigation",
        ],
        "prerequisites": [
            "Page must be loaded (browser_navigate called or browser_task completed)",
        ],
        "warnings": [],
        "examples": [
            {
                "scenario": "获取整个页面内容",
                "params": {},
                "expected": "Returns full page text content",
            },
            {
                "scenario": "获取特定元素内容",
                "params": {"selector": ".article-body"},
                "expected": "Returns text content of article body",
            },
            {
                "scenario": "获取页面 HTML 源码",
                "params": {"format": "html"},
                "expected": "Returns full page HTML content",
            },
        ],
        "related_tools": [
            {"name": "browser_navigate", "relation": "load page before getting content"},
            {"name": "browser_screenshot", "relation": "alternative - visual capture"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "元素选择器（可选，不填则获取整个页面）",
                },
                "format": {
                    "type": "string",
                    "enum": ["text", "html"],
                    "description": "返回格式：text（纯文本，默认）或 html（HTML 源码）",
                    "default": "text",
                },
                "max_length": {
                    "type": "integer",
                    "description": "最大返回字符数，默认 12000。超出部分保存到溢出文件，可用 read_file 分页读取",
                    "default": 12000,
                },
            },
            "required": [],
        },
    },
    # ---------- browser_screenshot ----------
    {
        "name": "browser_screenshot",
        "category": "Browser",
        "description": "Capture browser page screenshot (webpage content only, not desktop). When you need to: (1) Show page state to user, (2) Document web results, (3) Debug page issues. For desktop/application screenshots, use desktop_screenshot instead.",
        "detail": build_detail(
            summary="截取当前页面截图。",
            scenarios=[
                "向用户展示页面状态",
                "记录网页操作结果",
                "调试页面问题",
            ],
            params_desc={
                "full_page": "是否截取整个页面（包含滚动区域），默认 False 只截取可视区域",
                "path": "保存路径（可选，不填自动生成）",
            },
            notes=[
                "仅截取浏览器页面内容",
                "如需截取桌面或其他应用，请使用 desktop_screenshot",
                "full_page=True 会截取页面的完整内容（包含需要滚动才能看到的部分）",
            ],
        ),
        "triggers": [
            "When user asks to see the webpage",
            "When documenting web automation results",
            "When debugging page display issues",
        ],
        "prerequisites": [
            "Page must be loaded (browser_navigate called or browser_task completed)",
        ],
        "warnings": [],
        "examples": [
            {
                "scenario": "截取当前页面",
                "params": {},
                "expected": "Saves screenshot with auto-generated filename",
            },
            {
                "scenario": "截取完整页面",
                "params": {"full_page": True},
                "expected": "Saves full-page screenshot including scrollable content",
            },
            {
                "scenario": "保存到指定路径",
                "params": {"path": "C:/screenshots/result.png"},
                "expected": "Saves screenshot to specified path",
            },
        ],
        "related_tools": [
            {"name": "desktop_screenshot", "relation": "alternative for desktop apps"},
            {
                "name": "deliver_artifacts",
                "relation": "deliver the screenshot as an attachment (with receipts)",
            },
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "full_page": {
                    "type": "boolean",
                    "description": "是否截取整个页面（包含滚动区域），默认只截取可视区域",
                    "default": False,
                },
                "path": {"type": "string", "description": "保存路径（可选，不填自动生成）"},
            },
            "required": [],
        },
    },
    # ---------- view_image ----------
    {
        "name": "view_image",
        "category": "Browser",
        "description": "View/analyze a local image file. Load the image and send it to the LLM for visual understanding. Use this when you need to: (1) Verify browser screenshots show the expected content, (2) Analyze any local image file, (3) Understand what's in an image before deciding next steps. The image content will be embedded in the tool result so the LLM can SEE it directly.",
        "detail": build_detail(
            summary="查看/分析本地图片文件。将图片加载并嵌入到工具结果中，让 LLM 能直接看到图片内容。",
            scenarios=[
                "截图验证：截图后查看截图内容，确认页面状态是否符合预期",
                "分析任意本地图片文件",
                "在决策前理解图片内容",
            ],
            params_desc={
                "path": "图片文件路径（支持 png/jpg/jpeg/gif/webp）",
                "question": "可选，关于图片的具体问题（如'搜索结果有多少条？'）",
            },
            notes=[
                "⚠️ 重要：browser_screenshot 截图后，如果需要确认页面内容，一定要用此工具查看截图",
                "支持格式: PNG, JPEG, GIF, WebP",
                "图片会被自动缩放以适配 LLM 上下文限制",
                "如果当前模型不支持视觉，将使用 VL 模型生成文字描述",
            ],
        ),
        "triggers": [
            "When you need to verify what a screenshot actually shows",
            "After browser_screenshot, to check if the page state matches expectations",
            "When analyzing any local image file",
            "When user asks to look at or describe an image",
        ],
        "prerequisites": [],
        "warnings": [],
        "examples": [
            {
                "scenario": "验证浏览器截图",
                "params": {"path": "data/screenshots/screenshot_20260224_015625.png"},
                "expected": "Returns the image embedded in tool result, LLM can see and analyze the page content",
            },
            {
                "scenario": "带问题的图片分析",
                "params": {
                    "path": "data/screenshots/screenshot.png",
                    "question": "页面是否显示了搜索结果？搜索关键词是什么？",
                },
                "expected": "LLM sees the image and can answer the specific question",
            },
        ],
        "related_tools": [
            {"name": "browser_screenshot", "relation": "take screenshot first, then view_image to analyze"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "图片文件路径（支持 png/jpg/jpeg/gif/webp/bmp）",
                },
                "question": {
                    "type": "string",
                    "description": "关于图片的具体问题（可选，留空则返回图片让 LLM 自行分析）",
                },
            },
            "required": ["path"],
        },
    },
    # ---------- browser_click ----------
    {
        "name": "browser_click",
        "category": "Browser",
        "description": "Click an element on the current page by CSS selector or visible text. Use when you need precise control over page interactions — e.g. clicking buttons, links, menu items. Prefer this over browser_task for simple single-click actions.",
        "detail": build_detail(
            summary="点击页面上的元素。通过 CSS 选择器或可见文本定位元素并点击。",
            scenarios=[
                "点击按钮、链接、菜单项",
                "browser_task 失败后的手动降级操作",
                "精确的单步交互",
            ],
            params_desc={
                "selector": "CSS 选择器（如 'button.submit', '#login-btn', 'a[href=\"/about\"]'）",
                "text": "可见文本（如 '登录', 'Submit'），会转换为 text= 选择器",
            },
            notes=[
                "selector 和 text 至少提供一个",
                "优先使用 selector，text 作为便捷方式",
                "点击前建议先用 browser_screenshot 确认页面状态",
            ],
        ),
        "triggers": [
            "When clicking a specific button or link on the page",
            "When browser_task has failed and manual step-by-step interaction is needed",
        ],
        "prerequisites": ["Page must be loaded"],
        "warnings": [],
        "examples": [
            {"scenario": "点击登录按钮", "params": {"selector": "#login-btn"}, "expected": "Button clicked"},
            {"scenario": "点击文本链接", "params": {"text": "下一页"}, "expected": "Link clicked"},
        ],
        "related_tools": [
            {"name": "browser_type", "relation": "点击输入框后输入文本"},
            {"name": "browser_screenshot", "relation": "点击后截图验证"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS 选择器（如 '#submit-btn', '.nav-link'）"},
                "text": {"type": "string", "description": "要点击的元素的可见文本"},
            },
            "required": [],
        },
    },
    # ---------- browser_type ----------
    {
        "name": "browser_type",
        "category": "Browser",
        "description": "Type text into an input field identified by CSS selector. Clears existing content by default. Use for filling forms, search boxes, text areas. Includes smart retry with overlay dismissal.",
        "detail": build_detail(
            summary="在输入框中输入文本。默认先清空再输入。",
            scenarios=[
                "填写表单字段",
                "在搜索框中输入关键词",
                "编辑文本区域",
            ],
            params_desc={
                "selector": "输入框的 CSS 选择器",
                "text": "要输入的文本",
                "clear": "是否先清空输入框（默认 True）",
            },
            notes=[
                "默认清空再输入；设 clear=False 可追加",
                "内置智能重试：遇到遮挡元素会自动尝试关闭弹窗",
            ],
        ),
        "triggers": [
            "When filling form fields",
            "When typing into search boxes",
            "When entering text into any input element",
        ],
        "prerequisites": ["Page must be loaded", "Target input element must be visible"],
        "warnings": [],
        "examples": [
            {"scenario": "填写搜索框", "params": {"selector": "input[name='q']", "text": "OpenAkita"}, "expected": "Text typed"},
            {"scenario": "追加文本", "params": {"selector": "#editor", "text": " more text", "clear": False}, "expected": "Text appended"},
        ],
        "related_tools": [
            {"name": "browser_click", "relation": "先点击输入框再输入"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "输入框的 CSS 选择器"},
                "text": {"type": "string", "description": "要输入的文本"},
                "clear": {"type": "boolean", "description": "是否先清空（默认 True）", "default": True},
            },
            "required": ["selector", "text"],
        },
    },
    # ---------- browser_scroll ----------
    {
        "name": "browser_scroll",
        "category": "Browser",
        "description": "Scroll the current page up or down by a specified pixel amount. Use to reveal content below the fold, load lazy-loaded elements, or navigate long pages.",
        "detail": build_detail(
            summary="滚动页面。",
            scenarios=["查看页面下方内容", "触发懒加载", "浏览长页面"],
            params_desc={
                "direction": "滚动方向：'down'（默认）或 'up'",
                "amount": "滚动像素数（默认 500）",
            },
        ),
        "triggers": [
            "When page content extends below the visible area",
            "When loading more items on infinite-scroll pages",
        ],
        "prerequisites": ["Page must be loaded"],
        "warnings": [],
        "examples": [
            {"scenario": "向下滚动", "params": {"direction": "down", "amount": 800}, "expected": "Page scrolled down"},
            {"scenario": "向上滚动", "params": {"direction": "up", "amount": 300}, "expected": "Page scrolled up"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["down", "up"], "description": "滚动方向", "default": "down"},
                "amount": {"type": "integer", "description": "滚动像素数", "default": 500},
            },
            "required": [],
        },
    },
    # ---------- browser_wait ----------
    {
        "name": "browser_wait",
        "category": "Browser",
        "description": "Wait for a CSS selector to appear on the page, or wait for a specified duration. Use after navigation or clicks when content loads asynchronously.",
        "detail": build_detail(
            summary="等待元素出现或等待指定时间。",
            scenarios=["等待异步加载的内容", "等待动画完成", "等待 AJAX 请求返回"],
            params_desc={
                "selector": "等待出现的 CSS 选择器（可选）",
                "timeout": "超时时间（毫秒），默认 30000",
            },
            notes=[
                "提供 selector：等待该元素出现",
                "不提供 selector：等待 timeout 毫秒",
            ],
        ),
        "triggers": [
            "When waiting for dynamically loaded content",
            "When page needs time to load after an action",
        ],
        "prerequisites": ["Page must be loaded"],
        "warnings": [],
        "examples": [
            {"scenario": "等待搜索结果", "params": {"selector": ".search-results", "timeout": 10000}, "expected": "Element appeared"},
            {"scenario": "等待 2 秒", "params": {"timeout": 2000}, "expected": "Waited 2000ms"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "等待出现的 CSS 选择器"},
                "timeout": {"type": "integer", "description": "超时毫秒数", "default": 30000},
            },
            "required": [],
        },
    },
    # ---------- browser_execute_js ----------
    {
        "name": "browser_execute_js",
        "category": "Browser",
        "description": "Execute arbitrary JavaScript in the current page context. Returns the evaluation result. Use for extracting structured data, manipulating DOM, or calling page APIs that no other tool covers.",
        "detail": build_detail(
            summary="在当前页面执行 JavaScript 代码并返回结果。",
            scenarios=["提取页面结构化数据", "操作 DOM", "调用页面 API"],
            params_desc={"script": "要执行的 JavaScript 代码"},
            notes=[
                "返回值会被序列化为 JSON",
                "可使用 async/await（Playwright 支持）",
            ],
        ),
        "triggers": [
            "When extracting specific data from the page that get_content cannot provide",
            "When needing to interact with page JavaScript APIs",
        ],
        "prerequisites": ["Page must be loaded"],
        "warnings": ["Script runs in page context — avoid destructive operations unless intended"],
        "examples": [
            {"scenario": "获取页面标题", "params": {"script": "document.title"}, "expected": "Returns page title string"},
            {"scenario": "获取所有链接", "params": {"script": "Array.from(document.querySelectorAll('a')).map(a => ({text: a.textContent, href: a.href}))"}, "expected": "Returns array of link objects"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {"type": "string", "description": "要执行的 JavaScript 代码"},
            },
            "required": ["script"],
        },
    },
    # ---------- browser_list_tabs ----------
    {
        "name": "browser_list_tabs",
        "category": "Browser",
        "description": "List all open browser tabs with their index, URL, and title. Use to understand the current browser state or find a specific tab to switch to.",
        "detail": build_detail(
            summary="列出所有已打开的浏览器标签页。",
            scenarios=["查看当前打开了哪些页面", "确认某个标签页是否存在"],
        ),
        "triggers": ["When managing multiple tabs", "When checking browser state"],
        "prerequisites": ["Browser must be running"],
        "warnings": [],
        "examples": [
            {"scenario": "列出标签页", "params": {}, "expected": "Returns list of tabs with index, url, title"},
        ],
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    # ---------- browser_switch_tab ----------
    {
        "name": "browser_switch_tab",
        "category": "Browser",
        "description": "Switch to a browser tab by its index (0-based). Use browser_list_tabs first to see available tabs and their indices.",
        "detail": build_detail(
            summary="切换到指定索引的标签页。",
            scenarios=["在多个页面间切换", "返回之前的标签页"],
            params_desc={"index": "标签页索引（0-based），先用 browser_list_tabs 查看"},
        ),
        "triggers": ["When switching between multiple open pages"],
        "prerequisites": ["Browser must be running with multiple tabs"],
        "warnings": [],
        "examples": [
            {"scenario": "切换到第二个标签", "params": {"index": 1}, "expected": "Switched to tab 1"},
        ],
        "related_tools": [
            {"name": "browser_list_tabs", "relation": "先列出标签页再切换"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "标签页索引（0-based）"},
            },
            "required": ["index"],
        },
    },
    # ---------- browser_new_tab ----------
    {
        "name": "browser_new_tab",
        "category": "Browser",
        "description": "Open a URL in a new browser tab. The new tab becomes the active tab. Use when you want to keep the current page open while opening another.",
        "detail": build_detail(
            summary="在新标签页中打开 URL。",
            scenarios=["保留当前页面的同时打开新页面", "并行浏览多个页面"],
            params_desc={"url": "要在新标签页中打开的 URL"},
        ),
        "triggers": [
            "When opening a new page while keeping the current one",
        ],
        "prerequisites": ["Browser must be running"],
        "warnings": [],
        "examples": [
            {"scenario": "新标签页打开文档", "params": {"url": "https://docs.example.com"}, "expected": "New tab opened"},
        ],
        "related_tools": [
            {"name": "browser_switch_tab", "relation": "打开后可切回原标签页"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "要打开的 URL"},
            },
            "required": ["url"],
        },
    },
    # ---------- browser_close ----------
    {
        "name": "browser_close",
        "category": "Browser",
        "description": "Close the browser and release resources. Call when browser automation is complete and no longer needed. This frees memory and system resources.",
        "detail": build_detail(
            summary="关闭浏览器，释放资源。",
            scenarios=[
                "浏览器任务全部完成后",
                "需要释放系统资源",
                "需要重新启动浏览器（先关闭再打开）",
            ],
            notes=[
                "关闭后需要再次调用 browser_open 才能使用浏览器",
                "所有标签页都会关闭",
            ],
        ),
        "triggers": [
            "When browser automation tasks are completed",
            "When user explicitly asks to close browser",
            "When freeing system resources",
        ],
        "prerequisites": [],
        "warnings": [
            "All open tabs and pages will be closed",
        ],
        "examples": [
            {
                "scenario": "任务完成后关闭浏览器",
                "params": {},
                "expected": "Browser closes and resources are freed",
            },
        ],
        "related_tools": [
            {"name": "browser_open", "relation": "reopen browser after closing"},
        ],
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
