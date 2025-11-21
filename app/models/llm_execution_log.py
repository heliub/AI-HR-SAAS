"""
LLM Execution Log model
"""
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, Index
from app.models.base import Base


class LLMExecutionLog(Base):
    """LLM执行日志模型"""
    
    __tablename__ = "llm_execution_logs"
    
    tenant_id = Column(String(36), comment="租户ID")
    
    trace_id = Column(String(36), comment="流程追踪ID")
    
    template_id = Column(String(36), comment="关联的Prompt模板ID")
    scene_name = Column(String(100), comment="场景名称")
    
    provider = Column(String(50), comment="LLM提供商")
    model = Column(String(100), comment="模型名称")
    temperature = Column(Float, comment="温度参数")
    top_p = Column(Float, comment="top_p参数")
    max_completion_tokens = Column(Integer, comment="最大完成token数")
    
    template_variables = Column(Text, comment="模板变量值（JSON字符串）")
    
    response_content = Column(Text, comment="响应内容")
    
    prompt_tokens = Column(Integer, comment="Prompt token数")
    completion_tokens = Column(Integer, comment="完成token数")
    total_tokens = Column(Integer, comment="总token数")
    
    started_at = Column(DateTime(timezone=True), comment="LLM调用开始时间")
    completed_at = Column(DateTime(timezone=True), comment="LLM调用完成时间")
    execution_time_ms = Column(Float, comment="执行耗时（毫秒）")
    
    is_success = Column(Boolean, default=True, comment="是否成功")
    error_type = Column(String(100), comment="错误类型")
    error_message = Column(Text, comment="错误信息")

    
    def __repr__(self) -> str:
        return f"<LLMExecutionLog(id={self.id}, scene_name={self.scene_name}, model={self.model})>"

