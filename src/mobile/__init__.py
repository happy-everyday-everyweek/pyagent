"""
PyAgent 移动端模块

提供移动设备上的后端服务、屏幕操作、通知读取和短信功能。
v0.8.0: 新增移动端支持
- 新增MNN本地推理支持
- 新增包管理功能
- 新增工作流自动化
- 新增工具注册表
"""

from src.mobile.backend import MobileBackend
from src.mobile.linux_env import LinuxEnv
from src.mobile.mnn_inference import (
    MNNBackend,
    MNNInference,
    MNNInferenceConfig,
    MNNInferenceResult,
    MNNMemory,
    MNNModelInfo,
    MNNModelStatus,
    MNNPrecision,
    mnn_inference,
)
from src.mobile.notification import NotificationListener, NotificationReader
from src.mobile.package_manager import (
    PackageInfo,
    PackageManager,
    PackageManagerConfig,
    PackageState,
    PackageType,
    RunningPackage,
    package_manager,
)
from src.mobile.screen_tools import ScreenTools
from src.mobile.sms import SMSTools
from src.mobile.tool_registry import (
    MobileTool,
    MobileToolRegistry,
    ToolCategory,
    ToolInfo,
    ToolParameter,
    ToolResult,
    ToolState,
    mobile_tool_registry,
)
from src.mobile.workflow import (
    Workflow,
    WorkflowAutomation,
    WorkflowConfig,
    WorkflowConnection,
    WorkflowExecution,
    WorkflowNode,
    WorkflowNodeType,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowTrigger,
    WorkflowTriggerType,
    workflow_automation,
)

__all__ = [
    "LinuxEnv",
    "MobileBackend",
    "ScreenTools",
    "NotificationReader",
    "NotificationListener",
    "SMSTools",
    "MNNInference",
    "MNNInferenceConfig",
    "MNNInferenceResult",
    "MNNModelInfo",
    "MNNModelStatus",
    "MNNBackend",
    "MNNPrecision",
    "MNNMemory",
    "mnn_inference",
    "PackageManager",
    "PackageManagerConfig",
    "PackageInfo",
    "PackageState",
    "PackageType",
    "RunningPackage",
    "package_manager",
    "WorkflowAutomation",
    "WorkflowConfig",
    "Workflow",
    "WorkflowNode",
    "WorkflowNodeType",
    "WorkflowConnection",
    "WorkflowTrigger",
    "WorkflowTriggerType",
    "WorkflowExecution",
    "WorkflowStep",
    "WorkflowStepStatus",
    "WorkflowStatus",
    "workflow_automation",
    "MobileToolRegistry",
    "MobileTool",
    "ToolInfo",
    "ToolParameter",
    "ToolResult",
    "ToolCategory",
    "ToolState",
    "mobile_tool_registry",
]
