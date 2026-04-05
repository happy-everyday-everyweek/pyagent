import time

import pytest


@pytest.mark.asyncio
async def test_tool_parallel_execution_is_faster():
    """
    验证：当同一轮返回多个工具调用时，启用并行能显著降低总耗时。

    约束：
    - 不依赖任何 LLM API Key
    - 不依赖 Playwright/MCP
    - 使用 run_shell 执行两个独立的 sleep 命令
    """

    from openakita.config import settings
    from openakita.core.agent import Agent

    cmd_a = 'python -c "import time; time.sleep(2); print(\'A\')"'
    cmd_b = 'python -c "import time; time.sleep(2); print(\'B\')"'

    tool_calls = [
        {"id": "t1", "name": "run_shell", "input": {"command": cmd_a, "timeout": 20}},
        {"id": "t2", "name": "run_shell", "input": {"command": cmd_b, "timeout": 20}},
    ]

    # === 串行 ===
    settings.tool_max_parallel = 1
    agent_serial = Agent(api_key="")
    agent_serial.set_interrupt_enabled(False)

    t0 = time.time()
    results_serial, _, _ = await agent_serial._execute_tool_calls_batch(  # noqa: SLF001
        tool_calls,
        allow_interrupt_checks=False,
    )
    serial_s = time.time() - t0

    assert len(results_serial) == 2

    # === 并行 ===
    settings.tool_max_parallel = 4
    agent_parallel = Agent(api_key="")
    agent_parallel.set_interrupt_enabled(False)

    t0 = time.time()
    results_parallel, _, _ = await agent_parallel._execute_tool_calls_batch(  # noqa: SLF001
        tool_calls,
        allow_interrupt_checks=False,
    )
    parallel_s = time.time() - t0

    assert len(results_parallel) == 2

    # 断言：并行明显更快。给 CI 充足抖动空间。
    # 串行约 4s；并行约 2s；在慢机器上也应有明显差距。
    assert parallel_s <= serial_s * 0.75, (serial_s, parallel_s)

