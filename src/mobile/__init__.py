"""
PyAgent 移动端模块

提供移动设备上的后端服务、屏幕操作、通知读取和短信功能。
v0.8.0: 新增移动端支持
- 新增MNN本地推理支持
- 新增包管理功能
- 新增工作流自动化
- 新增工具注册表
v0.9.8: 移植 OpenKiwi 核心功能
- 新增验证码提取器
- 新增通知分类器
- 新增自动回复管理器
- 新增代码执行沙箱
- 新增手势执行器
"""

from src.mobile.auto_reply import (
    AutoReplyManager,
    RateLimiter,
    ReplyRecord,
    ReplyStatus,
    ReplyTemplate,
    ReplyWhitelist,
    auto_reply_manager,
)
from src.mobile.backend import MobileBackend
from src.mobile.code_sandbox import (
    CodeSandbox,
    DangerCommandDetector,
    ExecutionResult,
    SandboxConfig,
    SandboxStatus,
    code_sandbox,
)
from src.mobile.gesture_executor import (
    GestureExecutor,
    GestureResult,
    GestureSpec,
    GestureType,
    NodeCache,
    gesture_executor,
)
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
from src.mobile.notification_classifier import (
    ClassifiedNotification,
    NotificationClassifier,
    NotificationImportance,
    notification_classifier,
)
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
from src.mobile.verification_code import (
    VerificationCode,
    VerificationCodeExtractor,
    VerificationCodeType,
    verification_code_extractor,
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
    "AutoReplyManager",
    "ClassifiedNotification",
    "CodeSandbox",
    "DangerCommandDetector",
    "ExecutionResult",
    "GestureExecutor",
    "GestureResult",
    "GestureSpec",
    "GestureType",
    "LinuxEnv",
    "MNNBackend",
    "MNNInference",
    "MNNInferenceConfig",
    "MNNInferenceResult",
    "MNNMemory",
    "MNNModelInfo",
    "MNNModelStatus",
    "MNNPrecision",
    "MobileBackend",
    "MobileTool",
    "MobileToolRegistry",
    "NodeCache",
    "NotificationClassifier",
    "NotificationImportance",
    "NotificationListener",
    "NotificationReader",
    "PackageInfo",
    "PackageManager",
    "PackageManagerConfig",
    "PackageState",
    "PackageType",
    "RateLimiter",
    "ReplyRecord",
    "ReplyStatus",
    "ReplyTemplate",
    "ReplyWhitelist",
    "RunningPackage",
    "SMSTools",
    "SandboxConfig",
    "SandboxStatus",
    "ScreenTools",
    "ToolCategory",
    "ToolInfo",
    "ToolParameter",
    "ToolResult",
    "ToolState",
    "VerificationCode",
    "VerificationCodeExtractor",
    "VerificationCodeType",
    "Workflow",
    "WorkflowAutomation",
    "WorkflowConfig",
    "WorkflowConnection",
    "WorkflowExecution",
    "WorkflowNode",
    "WorkflowNodeType",
    "WorkflowStatus",
    "WorkflowStep",
    "WorkflowStepStatus",
    "WorkflowTrigger",
    "WorkflowTriggerType",
    "auto_reply_manager",
    "code_sandbox",
    "gesture_executor",
    "mnn_inference",
    "mobile_tool_registry",
    "notification_classifier",
    "package_manager",
    "verification_code_extractor",
    "workflow_automation",
]
