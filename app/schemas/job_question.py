"""
Job Question schemas
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class JobQuestionBase(BaseModel):
    """职位问题基础Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    question: str = Field(..., min_length=1, description="问题内容")
    questionType: str = Field(..., alias="question_type", description="问题类型: information-信息采集, assessment-考察评估")
    isRequired: bool = Field(False, alias="is_required", description="是否必须满足该要求")
    evaluationCriteria: Optional[str] = Field(None, alias="evaluation_criteria", description="判断标准（考察类问题使用）")
    sortOrder: int = Field(0, alias="sort_order", description="显示排序（越小越靠前）")


class JobQuestionCreate(JobQuestionBase):
    """创建职位问题Schema"""
    jobId: UUID = Field(..., alias="job_id", description="关联职位ID")


class JobQuestionUpdate(BaseModel):
    """更新职位问题Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    question: Optional[str] = Field(None, min_length=1, description="问题内容")
    questionType: Optional[str] = Field(None, alias="question_type", description="问题类型: information-信息采集, assessment-考察评估")
    isRequired: Optional[bool] = Field(None, alias="is_required", description="是否必须满足该要求")
    evaluationCriteria: Optional[str] = Field(None, alias="evaluation_criteria", description="判断标准（考察类问题使用）")
    sortOrder: Optional[int] = Field(None, alias="sort_order", description="显示排序（越小越靠前）")


class JobQuestionResponse(JobQuestionBase, IDSchema, TimestampSchema):
    """职位问题响应Schema"""
    jobId: UUID = Field(..., alias="job_id", description="关联职位ID")
    userId: UUID = Field(..., alias="user_id", description="创建问题的HR用户ID")
    status: str = Field(..., description="状态: active-启用, deleted-已删除")


class JobQuestionReorder(BaseModel):
    """职位问题排序Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    questionId: UUID = Field(..., alias="question_id", description="问题ID")
    sortOrder: int = Field(..., alias="sort_order", description="显示排序（越小越靠前）")


class JobQuestionReorderRequest(BaseModel):
    """职位问题批量排序请求Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    questions: List[JobQuestionReorder] = Field(..., description="问题排序列表")
