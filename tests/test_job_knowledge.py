"""
Job Knowledge Base API tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models import Job, User, Tenant, JobKnowledgeBase, KnowledgeQuestionVariant
from app.services.job_knowledge_service import JobKnowledgeService


@pytest.mark.asyncio
class TestJobKnowledge:
    """知识库接口测试"""

    # ==============================================
    # CRUD 操作测试
    # ==============================================

    async def test_create_knowledge(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试创建知识库条目"""
        response = await client.post(
            "/api/v1/knowledge",
            headers=auth_headers,
            json={
                "scopeType": "job",
                "scopeId": str(test_job.id),
                "categories": ["薪资福利", "工作内容"],
                "question": "这个职位的薪资范围是多少？",
                "answer": "薪资范围是25000-40000元/月，具体根据能力和经验确定。",
                "keywords": "薪资,工资,待遇"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["question"] == "这个职位的薪资范围是多少？"
        assert data["data"]["scopeType"] == "job"
        assert "薪资福利" in data["data"]["categories"]

    async def test_create_knowledge_company_scope(self, client: AsyncClient, auth_headers: dict, test_tenant: Tenant):
        """测试创建公司级知识库"""
        response = await client.post(
            "/api/v1/knowledge",
            headers=auth_headers,
            json={
                "scopeType": "company",
                "scopeId": str(test_tenant.id),
                "categories": ["公司文化"],
                "question": "公司的工作氛围怎么样？",
                "answer": "公司提倡开放包容的工作氛围，鼓励创新。",
                "keywords": "文化,氛围,环境"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["scopeType"] == "company"

    async def test_list_knowledge(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试查询知识库列表"""
        # 先创建测试数据
        knowledge_service = JobKnowledgeService(db_session)
        await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围是多少？",
                "answer": "25000-40000元/月",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        response = await client.get(
            "/api/v1/knowledge",
            headers=auth_headers,
            params={
                "scopeType": "job",
                "scopeId": str(test_job.id),
                "page": 1,
                "pageSize": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
        assert len(data["data"]["list"]) >= 1

    async def test_list_knowledge_with_category_filter(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试按分类过滤知识库"""
        # 创建两个不同分类的知识库
        knowledge_service = JobKnowledgeService(db_session)

        await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["工作内容"],
                "question": "主要工作内容？",
                "answer": "前端开发",
                "keywords": "工作"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        response = await client.get(
            "/api/v1/knowledge",
            headers=auth_headers,
            params={
                "scopeType": "job",
                "scopeId": str(test_job.id),
                "category": "薪资福利",
                "page": 1,
                "pageSize": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        # 应该只返回薪资福利分类的知识库
        for item in data["data"]["list"]:
            assert "薪资福利" in item["categories"]

    async def test_get_knowledge_detail(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试获取知识库详情"""
        # 创建知识库
        knowledge_service = JobKnowledgeService(db_session)
        knowledge = await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        response = await client.get(
            f"/api/v1/knowledge/{knowledge.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["question"] == "薪资范围？"
        assert data["data"]["answer"] == "25000-40000"

    async def test_get_knowledge_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试获取不存在的知识库"""
        response = await client.get(
            f"/api/v1/knowledge/{uuid4()}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_update_knowledge(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试更新知识库"""
        # 创建知识库
        knowledge_service = JobKnowledgeService(db_session)
        knowledge = await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        response = await client.put(
            f"/api/v1/knowledge/{knowledge.id}",
            headers=auth_headers,
            json={
                "answer": "薪资范围是30000-50000元/月，具体面议。",
                "categories": ["薪资福利", "待遇"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "30000-50000" in data["data"]["answer"]
        assert "待遇" in data["data"]["categories"]

    async def test_update_knowledge_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试更新不存在的知识库"""
        response = await client.put(
            f"/api/v1/knowledge/{uuid4()}",
            headers=auth_headers,
            json={
                "answer": "更新的答案"
            }
        )

        assert response.status_code == 404

    async def test_delete_knowledge(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试删除知识库"""
        # 创建知识库
        knowledge_service = JobKnowledgeService(db_session)
        knowledge = await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        response = await client.delete(
            f"/api/v1/knowledge/{knowledge.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "删除成功"

        # 验证已被软删除
        deleted_knowledge = await knowledge_service.get_knowledge_by_id(
            knowledge_id=knowledge.id,
            tenant_id=test_job.tenant_id,
            is_admin=True
        )
        assert deleted_knowledge is None

    async def test_delete_knowledge_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试删除不存在的知识库"""
        response = await client.delete(
            f"/api/v1/knowledge/{uuid4()}",
            headers=auth_headers
        )

        assert response.status_code == 404

    # ==============================================
    # 批量操作测试
    # ==============================================

    async def test_batch_create_knowledge(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试批量创建知识库"""
        response = await client.post(
            "/api/v1/knowledge/batch",
            headers=auth_headers,
            json={
                "scopeType": "job",
                "scopeId": str(test_job.id),
                "items": [
                    {
                        "categories": ["薪资福利"],
                        "question": "薪资范围？",
                        "answer": "25000-40000",
                        "keywords": "薪资"
                    },
                    {
                        "categories": ["工作时间"],
                        "question": "工作时间安排？",
                        "answer": "弹性工作制，核心工作时间10:00-16:00",
                        "keywords": "工作时间"
                    },
                    {
                        "categories": ["福利待遇"],
                        "question": "有什么福利？",
                        "answer": "五险一金，年度体检，带薪年假",
                        "keywords": "福利"
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 3
        assert data["data"]["success"] == 3
        assert data["data"]["failed"] == 0
        assert len(data["data"]["items"]) == 3

    # ==============================================
    # 问题变体管理测试
    # ==============================================

    async def test_add_variant(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试手动添加问题变体"""
        # 创建知识库
        knowledge_service = JobKnowledgeService(db_session)
        knowledge = await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围是多少？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        response = await client.post(
            f"/api/v1/knowledge/{knowledge.id}/variants",
            headers=auth_headers,
            json={
                "variantQuestion": "工资待遇怎么样？"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["variantQuestion"] == "工资待遇怎么样？"
        assert data["data"]["source"] == "manual"

    async def test_add_variant_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试为不存在的知识库添加变体"""
        response = await client.post(
            f"/api/v1/knowledge/{uuid4()}/variants",
            headers=auth_headers,
            json={
                "variantQuestion": "工资待遇怎么样？"
            }
        )

        assert response.status_code == 404

    async def test_list_variants(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试获取变体列表"""
        # 创建知识库和变体
        knowledge_service = JobKnowledgeService(db_session)
        knowledge = await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围是多少？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        # 添加两个变体
        await knowledge_service.add_variant(
            knowledge_id=knowledge.id,
            variant_question="工资待遇怎么样？",
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            is_admin=True,
            source="manual"
        )

        await knowledge_service.add_variant(
            knowledge_id=knowledge.id,
            variant_question="月薪多少？",
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            is_admin=True,
            source="manual"
        )

        response = await client.get(
            f"/api/v1/knowledge/{knowledge.id}/variants",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["variants"]) == 2

    async def test_delete_variant(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试删除变体"""
        # 创建知识库和变体
        knowledge_service = JobKnowledgeService(db_session)
        knowledge = await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围是多少？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        variant = await knowledge_service.add_variant(
            knowledge_id=knowledge.id,
            variant_question="工资待遇怎么样？",
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            is_admin=True,
            source="manual"
        )

        response = await client.delete(
            f"/api/v1/variants/{variant.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "删除成功"

    async def test_delete_variant_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试删除不存在的变体"""
        response = await client.delete(
            f"/api/v1/variants/{uuid4()}",
            headers=auth_headers
        )

        assert response.status_code == 404

    # AI生成变体测试（需要mock LLM服务）
    async def test_ai_generate_variants(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession, monkeypatch):
        """测试AI生成问题变体（使用mock）"""
        # 创建知识库
        knowledge_service = JobKnowledgeService(db_session)
        knowledge = await knowledge_service.create_knowledge(
            data={
                "scope_type": "job",
                "scope_id": test_job.id,
                "categories": ["薪资福利"],
                "question": "薪资范围是多少？",
                "answer": "25000-40000",
                "keywords": "薪资"
            },
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by
        )

        # Mock LLM响应
        async def mock_ai_generate_variants(self, knowledge_id, tenant_id, user_id=None, is_admin=False, max_variants=5):
            return [
                {"variant": "工资大概多少钱？", "confidence": 0.9},
                {"variant": "月薪范围是什么？", "confidence": 0.85},
                {"variant": "薪酬待遇如何？", "confidence": 0.8}
            ]

        # 打补丁
        monkeypatch.setattr(JobKnowledgeService, "ai_generate_variants", mock_ai_generate_variants)

        response = await client.post(
            f"/api/v1/knowledge/{knowledge.id}/variants/ai-generate",
            headers=auth_headers,
            json={
                "maxVariants": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["suggestions"]) == 3
        assert data["data"]["suggestions"][0]["variant"] == "工资大概多少钱？"
        assert data["data"]["suggestions"][0]["confidence"] == 0.9

    # ==============================================
    # 数据分析测试
    # ==============================================

    async def test_get_coverage_stats(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试获取覆盖率统计"""
        # 创建一些知识库
        knowledge_service = JobKnowledgeService(db_session)
        for i in range(3):
            await knowledge_service.create_knowledge(
                data={
                    "scope_type": "job",
                    "scope_id": test_job.id,
                    "categories": ["测试"],
                    "question": f"测试问题{i}？",
                    "answer": f"测试答案{i}",
                    "keywords": "测试"
                },
                tenant_id=test_job.tenant_id,
                user_id=test_job.created_by
            )

        response = await client.get(
            "/api/v1/knowledge/analytics/coverage",
            headers=auth_headers,
            params={
                "scopeId": str(test_job.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["totalKnowledge"] >= 3
        # embedding是异步生成的，所以可能还未完成
        assert "withEmbedding" in data["data"]
        assert "embeddingCoverage" in data["data"]

    async def test_get_hot_questions(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试获取热门问题（需要有命中日志数据）"""
        response = await client.get(
            "/api/v1/knowledge/analytics/hot-questions",
            headers=auth_headers,
            params={
                "scopeId": str(test_job.id),
                "days": 30,
                "limit": 20
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        # 没有命中日志时应该返回空列表
        assert isinstance(data["data"]["items"], list)

    async def test_get_missed_questions(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试获取未命中问题"""
        response = await client.get(
            "/api/v1/knowledge/analytics/missed-questions",
            headers=auth_headers,
            params={
                "scopeId": str(test_job.id),
                "days": 7,
                "minOccurrences": 3,
                "limit": 20
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        # 没有未命中记录时应该返回空列表
        assert isinstance(data["data"]["items"], list)
