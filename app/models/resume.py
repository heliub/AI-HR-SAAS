"""
Resume model
"""
from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Resume(Base):
    """简历模型"""
    
    __tablename__ = "resumes"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    candidate_id = Column(
        BigInteger, 
        ForeignKey("candidates.id"), 
        nullable=False, 
        index=True
    )
    job_id = Column(BigInteger, ForeignKey("jobs.id"), nullable=True, index=True)
    file_key = Column(String(500), comment="对象存储的key")
    file_name = Column(String(500), comment="文件名")
    file_type = Column(String(20), comment="文件类型: pdf, docx")
    file_size = Column(BigInteger, comment="文件大小（字节）")
    structured_data = Column(JSONB, comment="解析后的结构化数据")
    parse_status = Column(
        String(20), 
        default="pending",
        index=True,
        comment="解析状态: pending, parsing, completed, failed"
    )
    source = Column(
        String(50),
        comment="来源: email, platform, manual"
    )
    
    # 关系
    candidate = relationship("Candidate", back_populates="resumes")
    job = relationship("Job", back_populates="resumes")
    matching_results = relationship("MatchingResult", back_populates="resume", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, file_name={self.file_name}, parse_status={self.parse_status})>"

