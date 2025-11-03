"""
人岗匹配相关的Pydantic模型
"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Optional


class MatchRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    """人岗匹配请求模型"""
    jobId: UUID = Field(..., alias="job_id")
    resumeId: UUID = Field(..., alias="resume_id")


class MatchResponse(BaseModel):
    """人岗匹配响应模型"""
    matchId: UUID = Field(..., alias="id")
    isMatch: bool = Field(..., alias="is_match")
    matchScore: int = Field(..., alias="match_score")
    reason: str = Field(..., alias="reason")
    jobId: UUID = Field(..., alias="job_id")
    resumeId: UUID = Field(..., alias="resume_id")
