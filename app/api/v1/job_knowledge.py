"""
Job Knowledge Base endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.job_knowledge import (
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse,
    KnowledgeListResponse, KnowledgeBatchCreate, KnowledgeBatchCreateResponse,
    VariantCreate, VariantResponse, VariantAIGenerateRequest, VariantAIGenerateResponse,
    VariantAISuggestion, HotQuestionsResponse, HotQuestionItem,
    MissedQuestionsResponse, MissedQuestionItem, CoverageStats,
    ScopeType
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.job_knowledge_service import JobKnowledgeService
from app.models.user import User

router = APIRouter()


# ==============================================
# CRUD 操作
# ==============================================

@router.get("/knowledge", response_model=APIResponse)
async def list_knowledge(
    scopeType: Optional[str] = Query(None, description="作用域类型: company | job"),
    scopeId: Optional[UUID] = Query(None, description="作用域ID"),
    category: Optional[str] = Query(None, description="分类标签"),
    status: str = Query("active", description="状态"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询知识库列表"""
    knowledge_service = JobKnowledgeService(db)

    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    # 查询列表
    items, total = await knowledge_service.list_knowledge(
        tenant_id=current_user.tenant_id,
        scope_type=scopeType,
        scope_id=scopeId,
        category=category,
        status=status,
        user_id=current_user.id,
        is_admin=is_admin,
        page=page,
        page_size=pageSize
    )

    # 转换为响应模型
    knowledge_responses = []
    for item in items:
        item_dict = item.__dict__.copy()
        # 添加计算字段
        item_dict["has_embedding"] = item.question_embedding is not None
        item_dict["variants_count"] = 0  # TODO: 可以通过关联查询获取
        knowledge_responses.append(KnowledgeResponse.model_validate(item_dict))

    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=knowledge_responses
    )

    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.get("/knowledge/{knowledge_id}", response_model=APIResponse)
async def get_knowledge(
    knowledge_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库详情"""
    knowledge_service = JobKnowledgeService(db)

    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    # 获取详情
    knowledge = await knowledge_service.get_knowledge_by_id(
        knowledge_id=knowledge_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库条目不存在")

    # 转换为响应模型
    item_dict = knowledge.__dict__.copy()
    item_dict["has_embedding"] = knowledge.question_embedding is not None
    item_dict["variants_count"] = 0  # TODO: 可以通过关联查询获取
    knowledge_response = KnowledgeResponse.model_validate(item_dict)

    return APIResponse(
        code=200,
        message="成功",
        data=knowledge_response.model_dump()
    )


@router.post("/knowledge", response_model=APIResponse)
async def create_knowledge(
    knowledge_data: KnowledgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建知识库条目"""
    knowledge_service = JobKnowledgeService(db)

    # 创建知识库
    knowledge = await knowledge_service.create_knowledge(
        data=knowledge_data.model_dump(by_alias=True),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    # 转换为响应模型
    item_dict = knowledge.__dict__.copy()
    item_dict["has_embedding"] = knowledge.question_embedding is not None
    item_dict["variants_count"] = 0
    knowledge_response = KnowledgeResponse.model_validate(item_dict)

    return APIResponse(
        code=200,
        message="创建成功",
        data=knowledge_response.model_dump()
    )


@router.put("/knowledge/{knowledge_id}", response_model=APIResponse)
async def update_knowledge(
    knowledge_id: UUID,
    knowledge_data: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新知识库条目"""
    knowledge_service = JobKnowledgeService(db)

    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    # 更新知识库
    knowledge = await knowledge_service.update_knowledge(
        knowledge_id=knowledge_id,
        data=knowledge_data.model_dump(by_alias=True, exclude_unset=True),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库条目不存在")

    # 转换为响应模型
    item_dict = knowledge.__dict__.copy()
    item_dict["has_embedding"] = knowledge.question_embedding is not None
    item_dict["variants_count"] = 0
    knowledge_response = KnowledgeResponse.model_validate(item_dict)

    return APIResponse(
        code=200,
        message="更新成功",
        data=knowledge_response.model_dump()
    )


@router.delete("/knowledge/{knowledge_id}", response_model=APIResponse)
async def delete_knowledge(
    knowledge_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识库条目（软删除）"""
    knowledge_service = JobKnowledgeService(db)

    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    # 删除知识库
    success = await knowledge_service.delete_knowledge(
        knowledge_id=knowledge_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    if not success:
        raise HTTPException(status_code=404, detail="知识库条目不存在")

    return APIResponse(
        code=200,
        message="删除成功",
        data=None
    )


@router.post("/knowledge/batch", response_model=APIResponse)
async def batch_create_knowledge(
    batch_data: KnowledgeBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建知识库"""
    knowledge_service = JobKnowledgeService(db)

    # 批量创建
    success_items, error_items = await knowledge_service.batch_create_knowledge(
        items=batch_data.items,
        scope_type=batch_data.scopeType.value,
        scope_id=batch_data.scopeId,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    # 转换为响应模型
    knowledge_responses = []
    for item in success_items:
        item_dict = item.__dict__.copy()
        item_dict["has_embedding"] = item.question_embedding is not None
        item_dict["variants_count"] = 0
        knowledge_responses.append(KnowledgeResponse.model_validate(item_dict))

    batch_response = KnowledgeBatchCreateResponse(
        total=len(batch_data.items),
        success=len(success_items),
        failed=len(error_items),
        items=knowledge_responses,
        errors=error_items
    )

    return APIResponse(
        code=200,
        message=f"批量创建完成，成功{len(success_items)}条，失败{len(error_items)}条",
        data=batch_response.model_dump()
    )


# ==============================================
# 问题变体管理
# ==============================================

@router.get("/knowledge/{knowledge_id}/variants", response_model=APIResponse)
async def list_variants(
    knowledge_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取问题变体列表"""
    knowledge_service = JobKnowledgeService(db)

    # 验证知识库存在
    knowledge = await knowledge_service.get_knowledge_by_id(
        knowledge_id=knowledge_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=current_user.role == "admin"
    )
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库条目不存在")

    # 获取变体列表
    variants = await knowledge_service.list_variants(
        knowledge_id=knowledge_id,
        tenant_id=current_user.tenant_id
    )

    # 转换为响应模型
    variant_responses = []
    for variant in variants:
        item_dict = variant.__dict__.copy()
        item_dict["has_embedding"] = variant.variant_embedding is not None
        variant_responses.append(VariantResponse.model_validate(item_dict))

    return APIResponse(
        code=200,
        message="成功",
        data={"variants": variant_responses}
    )


@router.post("/knowledge/{knowledge_id}/variants", response_model=APIResponse)
async def add_variant(
    knowledge_id: UUID,
    variant_data: VariantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动添加问题变体"""
    knowledge_service = JobKnowledgeService(db)

    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    # 添加变体
    variant = await knowledge_service.add_variant(
        knowledge_id=knowledge_id,
        variant_question=variant_data.variantQuestion,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=is_admin,
        source="manual"
    )

    if not variant:
        raise HTTPException(status_code=404, detail="知识库条目不存在")

    # 转换为响应模型
    item_dict = variant.__dict__.copy()
    item_dict["has_embedding"] = variant.variant_embedding is not None
    variant_response = VariantResponse.model_validate(item_dict)

    return APIResponse(
        code=200,
        message="添加成功",
        data=variant_response.model_dump()
    )


@router.post("/knowledge/{knowledge_id}/variants/ai-generate", response_model=APIResponse)
async def ai_generate_variants(
    knowledge_id: UUID,
    generate_request: VariantAIGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI生成问题变体建议"""
    knowledge_service = JobKnowledgeService(db)

    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    try:
        # 调用AI生成变体
        variants_data = await knowledge_service.ai_generate_variants(
            knowledge_id=knowledge_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            is_admin=is_admin,
            max_variants=generate_request.maxVariants
        )

        # 转换为响应模型
        suggestions = [
            VariantAISuggestion(
                variant=item["variant"],
                confidence=item["confidence"]
            )
            for item in variants_data
        ]

        response_data = VariantAIGenerateResponse(suggestions=suggestions)

        return APIResponse(
            code=200,
            message="生成成功",
            data=response_data.model_dump()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")


@router.delete("/variants/{variant_id}", response_model=APIResponse)
async def delete_variant(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除问题变体（软删除）"""
    knowledge_service = JobKnowledgeService(db)

    # 删除变体
    success = await knowledge_service.delete_variant(
        variant_id=variant_id,
        tenant_id=current_user.tenant_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="变体不存在")

    return APIResponse(
        code=200,
        message="删除成功",
        data=None
    )


# ==============================================
# 数据分析
# ==============================================

@router.get("/knowledge/analytics/hot-questions", response_model=APIResponse)
async def get_hot_questions(
    scopeId: UUID = Query(..., description="作用域ID（职位ID或公司ID）"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取热门问题分析"""
    knowledge_service = JobKnowledgeService(db)

    # 查询热门问题
    items = await knowledge_service.get_hot_questions(
        scope_id=scopeId,
        tenant_id=current_user.tenant_id,
        days=days,
        limit=limit
    )

    # 转换为响应模型
    hot_items = [
        HotQuestionItem(
            knowledgeId=item["knowledge_id"],
            question=item["question"],
            answer=item["answer"],
            hitCount=item["hit_count"],
            lastHitAt=item["last_hit_at"]
        )
        for item in items
    ]

    response_data = HotQuestionsResponse(items=hot_items)

    return APIResponse(
        code=200,
        message="成功",
        data=response_data.model_dump()
    )


@router.get("/knowledge/analytics/missed-questions", response_model=APIResponse)
async def get_missed_questions(
    scopeId: UUID = Query(..., description="作用域ID（职位ID或公司ID）"),
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    minOccurrences: int = Query(3, ge=1, le=100, description="最小出现次数"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取未命中问题分析"""
    knowledge_service = JobKnowledgeService(db)

    # 查询未命中问题
    items = await knowledge_service.get_missed_questions(
        scope_id=scopeId,
        tenant_id=current_user.tenant_id,
        days=days,
        min_occurrences=minOccurrences,
        limit=limit
    )

    # 转换为响应模型
    missed_items = [
        MissedQuestionItem(
            question=item["question"],
            count=item["count"],
            suggestedCategories=[]  # 可以后续通过AI分析添加
        )
        for item in items
    ]

    response_data = MissedQuestionsResponse(items=missed_items)

    return APIResponse(
        code=200,
        message="成功",
        data=response_data.model_dump()
    )


@router.get("/knowledge/analytics/coverage", response_model=APIResponse)
async def get_coverage_stats(
    scopeId: UUID = Query(..., description="作用域ID（职位ID或公司ID）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库覆盖率统计"""
    knowledge_service = JobKnowledgeService(db)

    # 查询覆盖率统计
    stats = await knowledge_service.get_coverage_stats(
        scope_id=scopeId,
        tenant_id=current_user.tenant_id
    )

    # 转换为响应模型
    coverage_stats = CoverageStats(
        totalKnowledge=stats["total_knowledge"],
        withEmbedding=stats["with_embedding"],
        withVariants=stats["with_variants"],
        avgHitScore=stats["avg_hit_score"],
        embeddingCoverage=stats["embedding_coverage"]
    )

    return APIResponse(
        code=200,
        message="成功",
        data=coverage_stats.model_dump()
    )
