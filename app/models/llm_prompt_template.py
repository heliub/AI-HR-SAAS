"""
LLM Prompt Template model
"""
from sqlalchemy import Column, String, Text, Integer, Float, Index

from app.models.base import Base


class LLMPromptTemplate(Base):
    """LLM Prompt模板模型"""
    
    __tablename__ = "llm_prompt_templates"
    
    tenant_id = Column(String(36), comment="租户ID")
    
    scene_name = Column(String(100), comment="场景名称")
    version = Column(Integer, default=1, comment="模板版本号")
    template_hash = Column(String(64), comment="SHA256哈希")
    
    template_content = Column(Text, comment="Prompt模板内容")
    system_prompt = Column(Text, comment="系统提示词")
    
    provider = Column(String(50), comment="LLM提供商")
    model = Column(String(100), comment="模型名称")
    temperature = Column(Float, comment="温度参数")
    top_p = Column(Float, comment="top_p参数")
    

    def __repr__(self) -> str:
        return f"<LLMPromptTemplate(id={self.id}, scene_name={self.scene_name}, version={self.version})>"

