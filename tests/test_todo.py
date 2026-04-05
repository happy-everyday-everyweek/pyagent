"""
PyAgent Todo系统测试
"""

import pytest

from src.todo import (
    MateModeManager,
    TodoManager,
    TodoPriority,
    TodoStatus,
)


class TestTodoManager:
    """Todo管理器测试"""

    def test_create_manager(self, tmp_path):
        """测试创建管理器"""
        manager = TodoManager(data_dir=str(tmp_path / "todo"))
        assert manager is not None

    @pytest.mark.asyncio
    async def test_create_phase(self, tmp_path):
        """测试创建阶段"""
        manager = TodoManager(data_dir=str(tmp_path / "todo"))
        
        phase = await manager.create_phase(
            title="测试阶段",
            description="测试阶段描述",
        )
        
        assert phase is not None
        assert phase.title == "测试阶段"

    @pytest.mark.asyncio
    async def test_create_task(self, tmp_path):
        """测试创建任务"""
        manager = TodoManager(data_dir=str(tmp_path / "todo"))
        
        phase = await manager.create_phase(title="测试阶段")
        task = await manager.create_task(
            phase_id=phase.id,
            title="测试任务",
            steps=["步骤1", "步骤2"],
        )
        
        assert task is not None
        assert task.title == "测试任务"
        assert len(task.steps) == 2

    @pytest.mark.asyncio
    async def test_complete_step(self, tmp_path):
        """测试完成步骤"""
        manager = TodoManager(data_dir=str(tmp_path / "todo"))
        
        phase = await manager.create_phase(title="测试阶段")
        task = await manager.create_task(
            phase_id=phase.id,
            title="测试任务",
            steps=["步骤1"],
        )
        
        step = task.steps[0]
        success = await manager.complete_step(step.id)
        
        assert success
        assert step.status == TodoStatus.COMPLETED

    def test_get_statistics(self, tmp_path):
        """测试获取统计"""
        manager = TodoManager(data_dir=str(tmp_path / "todo"))
        stats = manager.get_statistics()
        
        assert "total_phases" in stats
        assert "total_tasks" in stats
        assert "total_steps" in stats


class TestMateModeManager:
    """Mate模式管理器测试"""

    def test_create_manager(self, tmp_path):
        """测试创建管理器"""
        manager = MateModeManager(data_dir=str(tmp_path / "mate"))
        assert manager is not None

    def test_enable_disable(self, tmp_path):
        """测试启用/禁用"""
        manager = MateModeManager(data_dir=str(tmp_path / "mate"))
        
        manager.enable()
        assert manager.is_enabled()
        
        manager.disable()
        assert not manager.is_enabled()

    def test_toggle(self, tmp_path):
        """测试切换"""
        manager = MateModeManager(data_dir=str(tmp_path / "mate"))
        
        initial_state = manager.is_enabled()
        manager.toggle()
        assert manager.is_enabled() != initial_state

    def test_collaboration_mode(self, tmp_path):
        """测试协作模式"""
        manager = MateModeManager(data_dir=str(tmp_path / "mate"))

        manager.set_collaboration_mode(True)
        assert manager.is_collaboration_enabled()

        manager.set_collaboration_mode(False)
        assert not manager.is_collaboration_enabled()

    def test_to_dict(self, tmp_path):
        """测试状态导出"""
        manager = MateModeManager(data_dir=str(tmp_path / "mate"))

        manager.enable()
        manager.set_collaboration_mode(True)

        state = manager.to_dict()
        assert state["enabled"] is True
        assert state["collaboration_enabled"] is True
