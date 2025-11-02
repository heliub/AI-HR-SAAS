"""
Job Knowledge Base schemas
"""
from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from app.utils.datetime_formatter import format_datetime

from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class ScopeType(str, Enum):
    """作用域类型枚举"""
    COMPANY = "company"
    JOB = "job"


class SearchMethod(str, Enum):
    """检索方法枚举"""
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"
    SIMPLE = "simple"


class VariantSource(str, Enum):
    """变体来源枚举"""
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"
    USER_FEEDBACK = "user_feedback"


# ==============================================
# 知识库主表 Schemas
# ==============================================

class KnowledgeBase(BaseModel):
    """知识库基础Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    scopeType: ScopeType = Field(..., alias="scope_type", description="作用域类型")
    scopeId: UUID = Field(..., alias="scope_id", description="作用域ID")
    categories: Optional[str] = Field(default="", description="分类标签，逗号分隔的字符串")
    question: str = Field(..., min_length=1, description="标准问题")
    answer: str = Field(..., min_length=1, description="标准答案")
    keywords: Optional[str] = Field(None, description="BM25关键词（逗号分隔）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")


class KnowledgeCreate(KnowledgeBase):
    """创建知识库Schema"""
    pass


class KnowledgeUpdate(BaseModel):
    """更新知识库Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    categories: Optional[str] = Field(None, description="分类标签，逗号分隔的字符串")
    question: Optional[str] = Field(None, min_length=1, description="标准问题")
    answer: Optional[str] = Field(None, min_length=1, description="标准答案")
    keywords: Optional[str] = Field(None, description="BM25关键词")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    status: Optional[str] = Field(None, description="状态")


class KnowledgeResponse(BaseModel):
    """知识库响应Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    # ID字段
    id: UUID
    
    # 时间戳字段
    createdAt: Optional[datetime] = Field(alias="created_at")
    updatedAt: Optional[datetime] = Field(alias="updated_at")
    
    # 基础字段
    scopeType: ScopeType = Field(..., alias="scope_type", description="作用域类型")
    scopeId: UUID = Field(..., alias="scope_id", description="作用域ID")
    categories: Optional[str] = Field(default="", description="分类标签，逗号分隔的字符串")
    question: str = Field(..., min_length=1, description="标准问题")
    answer: str = Field(..., min_length=1, description="标准答案")
    keywords: Optional[str] = Field(None, description="BM25关键词（逗号分隔）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    tenantId: UUID = Field(..., alias="tenant_id", description="租户ID")
    userId: Optional[UUID] = Field(None, alias="user_id", description="创建者HR用户ID")
    status: str = Field(..., description="状态")
    hasEmbedding: bool = Field(..., alias="has_embedding", description="是否已生成embedding")
    variantsCount: int = Field(0, alias="variants_count", description="变体数量")
    createdBy: Optional[UUID] = Field(None, alias="created_by", description="创建人用户ID")
    updatedBy: Optional[UUID] = Field(None, alias="updated_by", description="最后更新人用户ID")
    
    # 时间戳序列化
    @field_serializer('createdAt', 'updatedAt', when_used='always')
    def serialize_timestamps(self, value: Optional[datetime]) -> Optional[str]:
        """序列化时间戳"""
        if value is None:
            return None
        return format_datetime(value)


class KnowledgeListResponse(BaseModel):
    """知识库列表响应Schema"""
    total: int = Field(..., description="总数")
    items: List[KnowledgeResponse] = Field(..., description="知识库列表")


# ==============================================
# 问题变体 Schemas
# ==============================================

class VariantBase(BaseModel):
    """问题变体基础Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    variantQuestion: str = Field(..., alias="variant_question", min_length=1, description="变体问题")


class VariantCreate(VariantBase):
    """创建问题变体Schema"""
    pass


class VariantResponse(VariantBase, IDSchema, TimestampSchema):
    """问题变体响应Schema"""
    knowledgeId: UUID = Field(..., alias="knowledge_id", description="关联的知识库条目ID")
    source: VariantSource = Field(..., description="来源")
    confidenceScore: Optional[Decimal] = Field(None, alias="confidence_score", description="置信度")
    hasEmbedding: bool = Field(..., alias="has_embedding", description="是否已生成embedding")
    status: str = Field(..., description="状态")


class VariantAIGenerateRequest(BaseModel):
    """AI生成问题变体请求Schema"""
    maxVariants: int = Field(5, alias="max_variants", ge=1, le=10, description="最大生成数量")


class VariantAISuggestion(BaseModel):
    """AI生成的变体建议"""
    variant: str = Field(..., description="变体问题")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")


class VariantAIGenerateResponse(BaseModel):
    """AI生成问题变体响应Schema"""
    suggestions: List[VariantAISuggestion] = Field(..., description="变体建议列表")


# ==============================================
# 批量操作 Schemas
# ==============================================

class KnowledgeBatchCreate(BaseModel):
    """批量创建知识库Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    scopeType: ScopeType = Field(..., alias="scope_type", description="作用域类型")
    scopeId: UUID = Field(..., alias="scope_id", description="作用域ID")
    items: List[Dict[str, Any]] = Field(..., min_length=1, description="知识库条目列表，categories字段为逗号分隔的字符串")


class KnowledgeBatchCreateResponse(BaseModel):
    """批量创建响应Schema"""
    total: int = Field(..., description="总数")
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    items: List[KnowledgeResponse] = Field(..., description="成功创建的知识库列表")
    errors: List[Dict[str, Any]] = Field(default=[], description="错误信息列表")


# ==============================================
# 检索 Schemas
# ==============================================

class KnowledgeSearchRequest(BaseModel):
    """知识库检索请求Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    query: str = Field(..., min_length=1, description="查询文本")
    scopeType: ScopeType = Field(..., alias="scope_type", description="作用域类型")
    scopeId: UUID = Field(..., alias="scope_id", description="作用域ID")
    includeCompany: bool = Field(True, alias="include_company", description="是否包含公司级知识")
    method: SearchMethod = Field(SearchMethod.HYBRID, description="检索方法")
    topK: int = Field(5, alias="top_k", ge=1, le=20, description="返回Top K结果")


class KnowledgeSearchResult(BaseModel):
    """知识库检索结果Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    knowledgeId: UUID = Field(..., alias="knowledge_id", description="知识库条目ID")
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")
    matchScore: float = Field(..., alias="match_score", description="匹配分数")
    matchMethod: str = Field(..., alias="match_method", description="匹配方法")
    matchedVia: str = Field(..., alias="matched_via", description="命中方式: main_question | variant")
    variantId: Optional[UUID] = Field(None, alias="variant_id", description="如果通过变体命中，记录变体ID")
    categories: List[str] = Field(default=[], description="分类标签")


class KnowledgeSearchResponse(BaseModel):
    """知识库检索响应Schema"""
    results: List[KnowledgeSearchResult] = Field(..., description="检索结果列表")


# ==============================================
# 数据分析 Schemas
# ==============================================

class HotQuestionItem(BaseModel):
    """热门问题条目Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    knowledgeId: UUID = Field(..., alias="knowledge_id", description="知识库条目ID")
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")
    hitCount: int = Field(..., alias="hit_count", description="命中次数")
    lastHitAt: datetime = Field(..., alias="last_hit_at", description="最后命中时间")


class HotQuestionsResponse(BaseModel):
    """热门问题响应Schema"""
    items: List[HotQuestionItem] = Field(..., description="热门问题列表")


class MissedQuestionItem(BaseModel):
    """未命中问题条目Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    question: str = Field(..., description="候选人原始问题")
    count: int = Field(..., description="出现次数")
    suggestedCategories: List[str] = Field(default=[], alias="suggested_categories", description="建议的分类")


class MissedQuestionsResponse(BaseModel):
    """未命中问题响应Schema"""
    items: List[MissedQuestionItem] = Field(..., description="未命中问题列表")


class CoverageStats(BaseModel):
    """知识库覆盖率统计Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    totalKnowledge: int = Field(..., alias="total_knowledge", description="知识库总数")
    withEmbedding: int = Field(..., alias="with_embedding", description="已生成embedding的数量")
    withVariants: int = Field(..., alias="with_variants", description="有变体的知识库数量")
    avgHitScore: float = Field(..., alias="avg_hit_score", description="平均命中分数")
    embeddingCoverage: float = Field(..., alias="embedding_coverage", description="embedding覆盖率")
