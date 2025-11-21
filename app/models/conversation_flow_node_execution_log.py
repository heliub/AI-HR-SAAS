"""
Conversation Flow Node Execution Log model
"""
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, Index

from app.models.base import Base


class ConversationFlowNodeExecutionLog(Base):
    """对话流程节点执行轨迹模型"""
    
    __tablename__ = "conversation_flow_node_execution_logs"
    
    tenant_id = Column(String(36), comment="租户ID")
    
    trace_id = Column(String(36), comment="流程追踪ID")
    
    conversation_id = Column(String(36), comment="会话ID")
    trigger_message_id = Column(String(36), comment="触发的用户消息ID")
    
    node_name = Column(String(50), comment="节点名称")
    
    node_result = Column(Text, comment="节点执行结果（JSON字符串）")
    
    llm_execution_id = Column(String(36), comment="关联的LLM执行日志ID")
    
    started_at = Column(DateTime(timezone=True), comment="节点开始执行时间")
    completed_at = Column(DateTime(timezone=True), comment="节点完成执行时间")
    execution_time_ms = Column(Float, comment="执行耗时（毫秒）")
    
    is_success = Column(Boolean, default=True, comment="是否成功执行")
    error_message = Column(Text, comment="程序异常信息")
    
    
    def __repr__(self) -> str:
        return f"<ConversationFlowNodeExecutionLog(id={self.id}, trace_id={self.trace_id}, node_name={self.node_name})>"

