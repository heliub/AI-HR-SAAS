"""
结束语组节点

包含：
- N12: 高情商回复（结束语）
- N13: 复聊语
"""
from .n12_high_eq import N12HighEQResponseNode
from .n13_resume import N13ResumeConversationNode

__all__ = [
    "N12HighEQResponseNode",
    "N13ResumeConversationNode",
]
