"""
会话流程数据模型

定义节点执行结果、流程结果、上下文等核心数据结构
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime


class ConversationStage(str, Enum):
    """会话阶段枚举"""
    GREETING = "greeting"  # Stage1: 开场白阶段
    QUESTIONING = "questioning"  # Stage2: 问题询问阶段
    INTENTION = "intention"  # Stage3: 职位意向询问阶段
    MATCHED = "matched"  # Stage4: 撮合完成


class ConversationStatus(str, Enum):
    """会话状态枚举"""
    OPENED = "opened"  # 会话开启
    ONGOING = "ongoing"  # 沟通中
    INTERRUPTED = "interrupted"  # 中断
    ENDED = "ended"  # 会话结束
    DELETED = "deleted"  # 已删除


class QuestionStatus(str, Enum):
    """问题状态枚举"""
    PENDING = "pending"  # 待处理
    ONGOING = "ongoing"  # 进行中
    COMPLETED = "completed"  # 已完成
    SKIPPED = "skipped"  # 已跳过
    DELETED = "deleted"  # 已删除


class NodeAction(str, Enum):
    """节点动作类型枚举"""
    NONE = "NONE"  # 不做任何处理
    SUSPEND = "SUSPEND"  # 中断流程执行
    TERMINATE = "TERMINATE"  # 终止会话
    NEXT_NODE = "NEXT_NODE"  # 执行下一个节点
    SEND_MESSAGE = "SEND_MESSAGE"  # 发送返回的消息
    CONTINUE = "CONTINUE"  # 继续执行（内部使用）


@dataclass
class Message:
    """消息模型"""
    sender: str  # ai 或 candidate
    content: str
    message_type: str = "text"
    created_at: Optional[datetime] = None

    @classmethod
    def from_chat_history(cls, chat_history) -> "Message":
        """从聊天历史记录创建消息对象"""
        return cls(
            sender=chat_history.sender,
            content=chat_history.message,
            message_type=chat_history.message_type,
            created_at=chat_history.created_at
        )


@dataclass
class NodeResult:
    """节点执行结果"""
    node_name: str  # 节点名称
    action: NodeAction  # 执行动作
    message: Optional[str] = None  # 要发送的消息
    next_node: Optional[List[str]] = None  # 下一个节点列表
    reason: Optional[str] = None  # 原因说明
    data: Dict[str, Any] = field(default_factory=dict)  # 额外数据
    execution_time_ms: Optional[float] = None  # 执行耗时（毫秒）

    def __post_init__(self):
        """确保枚举类型正确"""
        if isinstance(self.action, str):
            self.action = NodeAction(self.action)


@dataclass
class FlowResult:
    """流程执行结果"""
    action: NodeAction  # 最终动作
    message: Optional[str] = None  # 要发送的消息
    reason: Optional[str] = None  # 原因说明
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    execution_path: List[str] = field(default_factory=list)  # 执行路径（节点名称列表）
    total_time_ms: Optional[float] = None  # 总耗时（毫秒）

    def __post_init__(self):
        """确保枚举类型正确"""
        if isinstance(self.action, str):
            self.action = NodeAction(self.action)

    @classmethod
    def from_node_result(cls, node_result: NodeResult) -> "FlowResult":
        """从节点结果创建流程结果"""
        return cls(
            action=node_result.action,
            message=node_result.message,
            reason=node_result.reason,
            metadata={
                "source_node": node_result.node_name,
                "node_data": node_result.data
            },
            execution_path=[node_result.node_name],
            total_time_ms=node_result.execution_time_ms
        )


@dataclass
class PositionInfo:
    """职位信息"""
    id: UUID
    name: str
    description: Optional[str] = None
    requirements: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description or "",
            "requirements": self.requirements or ""
        }


@dataclass
class ConversationContext:
    """会话上下文"""
    # 核心实体
    conversation_id: UUID
    tenant_id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID

    # 会话状态
    conversation_status: ConversationStatus
    conversation_stage: ConversationStage

    # 消息相关
    last_candidate_message: str  # 候选人最后一条消息
    history: List[Message]  # 历史对话

    # 职位信息
    position_info: PositionInfo

    # 可选字段
    knowledge_base_results: Optional[List[Dict[str, Any]]] = None  # 知识库检索结果
    current_question_id: Optional[UUID] = None  # 当前正在询问的问题ID
    current_question_content: Optional[str] = None  # 当前问题内容

    def __post_init__(self):
        """验证必填字段"""
        # 验证UUID字段不能为None
        if not self.conversation_id:
            raise ValueError("conversation_id不能为空")
        if not self.tenant_id:
            raise ValueError("tenant_id不能为空")
        if not self.user_id:
            raise ValueError("user_id不能为空")
        if not self.job_id:
            raise ValueError("job_id不能为空")
        if not self.resume_id:
            raise ValueError("resume_id不能为空")

        # 验证枚举字段
        if not isinstance(self.conversation_status, ConversationStatus):
            raise ValueError(f"conversation_status必须是ConversationStatus枚举类型，当前类型: {type(self.conversation_status)}")
        if not isinstance(self.conversation_stage, ConversationStage):
            raise ValueError(f"conversation_stage必须是ConversationStage枚举类型，当前类型: {type(self.conversation_stage)}")

        # 验证last_candidate_message不能为空
        if not self.last_candidate_message or not self.last_candidate_message.strip():
            raise ValueError("last_candidate_message不能为空")

        # 验证history必须是列表
        if not isinstance(self.history, list):
            raise ValueError(f"history必须是列表类型，当前类型: {type(self.history)}")

        # 验证position_info不能为None
        if not self.position_info:
            raise ValueError("position_info不能为空")

    def get_template_vars(self) -> Dict[str, Any]:
        """获取Prompt模板变量"""
        return {
            # 原有变量（保持向后兼容）
            "候选人最后一条消息": self.last_candidate_message,
            "历史对话": self.format_history(),
            "职位信息": self.position_info.to_dict(),
            "职位名称": self.position_info.name,
            "知识库信息": self.format_knowledge_base(),
            "HR最后一句话": self.get_last_hr_message(),
            "HR（AI）设定当前正在沟通的问题": self.current_question_content or "",
            
            # 统一变量名（驼峰命名法）
            "lastCandidateMessage": self.last_candidate_message,
            "chatHistory": self.format_history(),
            "jobInfo": self.position_info.to_dict(),
            "jobTitle": self.position_info.name,
            "knowledgeBase": self.format_knowledge_base(),
            "lastHRMessage": self.get_last_hr_message(),
            "currentQuestion": self.current_question_content or "",
            
            # 职位相关详细信息
            "jobDescription": self.position_info.description or "",
            "jobRequirement": self.position_info.requirements or "",
            
            # 兼容旧变量名
            "content": self.last_candidate_message,  # 候选人最后一条消息
            "chatMessage": self.format_history(),  # 历史对话
            "lastReply": self.get_last_hr_message(),  # HR最后一句话
            "jd_desc": self.position_info.description or "",  # 岗位JD
            "requirement": self.position_info.requirements or "",  # 用人条件
            "knowledge": self.format_knowledge_base(),  # 知识库内容
            "question": self.current_question_content or "",  # 当前问题
        }

    def format_history(self, max_messages: int = 10) -> str:
        """格式化历史对话"""
        recent_messages = self.history[-max_messages:] if len(self.history) > max_messages else self.history
        formatted = []
        for msg in recent_messages:
            role = "候选人" if msg.sender == "candidate" else "HR"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)

    def get_last_hr_message(self) -> str:
        """获取HR最后一句话"""
        for msg in reversed(self.history):
            if msg.sender == "ai":
                return msg.content
        return ""

    def format_knowledge_base(self) -> str:
        """格式化知识库信息"""
        if not self.knowledge_base_results:
            return ""

        formatted = []
        for idx, kb in enumerate(self.knowledge_base_results, 1):
            formatted.append(f"知识{idx}:")
            formatted.append(f"问题: {kb.get('question', '')}")
            formatted.append(f"答案: {kb.get('answer', '')}")
            formatted.append("")

        return "\n".join(formatted)

    @property
    def is_greeting_stage(self) -> bool:
        """是否为开场白阶段"""
        return self.conversation_stage == ConversationStage.GREETING

    @property
    def is_questioning_stage(self) -> bool:
        """是否为问题询问阶段"""
        return self.conversation_stage == ConversationStage.QUESTIONING

    @property
    def is_intention_stage(self) -> bool:
        """是否为职位意向阶段"""
        return self.conversation_stage == ConversationStage.INTENTION

    @property
    def is_matched_stage(self) -> bool:
        """是否为撮合完成阶段"""
        return self.conversation_stage == ConversationStage.MATCHED
