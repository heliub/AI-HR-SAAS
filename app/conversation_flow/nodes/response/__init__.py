"""
对话回复组节点

包含：
- N3: 候选人是否愿意沟通
- N4: 候选人是否发问
- N9: 基于知识库回复
- N10: 无知识库兜底回复
- N11: 陪候选人闲聊
"""
from .continue_conversation import ContinueConversationNode
from .ask_question import AskQuestionNode
from .knowledge_answer import KnowledgeAnswerNode
from .fallback_answer import FallbackAnswerNode
from .casual_chat import CasualChatNode

__all__ = [
    "ContinueConversationNode",
    "AskQuestionNode",
    "KnowledgeAnswerNode",
    "FallbackAnswerNode",
    "CasualChatNode",
]
