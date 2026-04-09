"""
PyAgent 表达学习系统

参考MaiBot的设计，实现自我学习功能：
- 表达学习：学习用户的表达方式和语言风格
- 黑话学习：识别和学习黑话/俚语/网络用语
"""

from .expression_learner import Expression, ExpressionLearner, expression_learner
from .self_learning import (
    JargonEntry,
    SelfLearningSystem,
    self_learning_system,
)

__all__ = [
    "Expression",
    "ExpressionLearner",
    "JargonEntry",
    "SelfLearningSystem",
    "expression_learner",
    "self_learning_system",
]
