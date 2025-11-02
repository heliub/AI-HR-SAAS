"""
对话回复组节点

包含：
- N3: 候选人是否愿意沟通
- N4: 候选人是否发问
- N9: 基于知识库回复
- N10: 无知识库兜底回复
- N11: 陪候选人闲聊
"""
from .n3_continue_conversation import N3ContinueConversationNode
from .n4_ask_question import N4AskQuestionNode
from .n9_knowledge_answer import N9KnowledgeAnswerNode
from .n10_fallback_answer import N10FallbackAnswerNode
from .n11_casual_chat import N11CasualChatNode

__all__ = [
    "N3ContinueConversationNode",
    "N4AskQuestionNode",
    "N9KnowledgeAnswerNode",
    "N10FallbackAnswerNode",
    "N11CasualChatNode",
]
