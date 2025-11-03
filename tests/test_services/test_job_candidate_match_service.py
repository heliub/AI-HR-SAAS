"""
测试人岗匹配服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.job_candidate_match_service import JobCandidateMatchService
from app.models.job import Job
from app.models.resume import Resume
from app.models.ai_match_result import AIMatchResult


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def job_candidate_match_service(mock_db):
    """创建人岗匹配服务实例"""
    return JobCandidateMatchService(mock_db)


@pytest.fixture
def sample_job():
    """示例职位数据"""
    return Job(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        title="高级软件工程师",
        company="测试公司",
        location="北京",
        type="full-time",
        category="技术/开发",
        description="负责后端系统开发",
        requirements="3年以上Python开发经验，熟悉Django框架"
    )


@pytest.fixture
def sample_resume():
    """示例简历数据"""
    return Resume(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        candidate_name="张三",
        position="软件工程师",
        experience_years="5年",
        education_level="本科",
        skills="Python, Django, MySQL"
    )


@pytest.fixture
def sample_resume_details():
    """示例简历详情数据"""
    return {
        "resume": Resume(
            id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            candidate_name="张三",
            position="软件工程师",
            experience_years="5年",
            education_level="本科",
            skills="Python, Django, MySQL"
        ),
        "work_experiences": [],
        "project_experiences": [],
        "education_histories": []
    }


@pytest.mark.asyncio
async def test_select_match_strategy_sales(job_candidate_match_service):
    """测试销售类职位匹配策略选择"""
    # 销售类职位
    sales_job = Job(
        id=uuid4(),
        tenant_id=uuid4(),
        title="销售经理",
        category="销售/商务"
    )
    
    strategy = await job_candidate_match_service._select_match_strategy(sales_job)
    assert "job_candidate_match_for_sales" in strategy


@pytest.mark.asyncio
async def test_select_match_strategy_tech(job_candidate_match_service):
    """测试技术类职位匹配策略选择"""
    # 技术类职位
    tech_job = Job(
        id=uuid4(),
        tenant_id=uuid4(),
        title="软件工程师",
        category="技术/开发"
    )
    
    strategy = await job_candidate_match_service._select_match_strategy(tech_job)
    assert "job_candidate_match_for_strong_skills" in strategy


def test_prepare_job_description(job_candidate_match_service, sample_job):
    """测试职位描述准备"""
    description = job_candidate_match_service._prepare_job_description(sample_job)
    
    assert "高级软件工程师" in description
    assert "负责后端系统开发" in description
    assert "3年以上Python开发经验" in description


@pytest.mark.asyncio
async def test_prepare_resume_description(job_candidate_match_service, sample_resume_details):
    """测试简历描述准备"""
    # 模拟resume_service.get_resume_full_details返回值
    job_candidate_match_service.resume_service.get_resume_full_details = AsyncMock(return_value=sample_resume_details)
    
    description = await job_candidate_match_service._prepare_resume_description(
        resume_id=sample_resume_details["resume"].id,
        tenant_id=sample_resume_details["resume"].tenant_id
    )
    
    assert "5年" in description
    assert "本科" in description
    assert "Python, Django, MySQL" in description


@pytest.mark.asyncio
async def test_match_job_candidate_success(job_candidate_match_service, sample_job, sample_resume, sample_resume_details):
    """测试人岗匹配成功场景"""
    # 直接模拟llm_caller属性
    mock_llm_caller = AsyncMock()
    job_candidate_match_service.llm_caller = mock_llm_caller
    
    # 模拟AI返回结果 - 对于技术类匹配，返回非JSON格式的内容
    mock_llm_caller.call_with_scene.return_value = {
        "content": '"判断结果":"是","判断依据":"候选人技能匹配职位要求"'
    }
    
    # 模拟服务方法
    job_candidate_match_service.job_service.get_by_id = AsyncMock(side_effect=[sample_job, sample_resume])
    job_candidate_match_service.resume_service.get_resume_full_details = AsyncMock(return_value=sample_resume_details)
    job_candidate_match_service._select_match_strategy = AsyncMock(return_value="job_candidate_match.job_candidate_match_for_strong_skills")
    job_candidate_match_service._prepare_job_description = MagicMock(return_value="job description")
    job_candidate_match_service._prepare_resume_description = AsyncMock(return_value="resume description")
    job_candidate_match_service._save_match_result = AsyncMock()
    job_candidate_match_service._update_resume_match_info = AsyncMock()
    
    # 执行匹配
    result = await job_candidate_match_service.match_job_candidate(
        job_id=sample_job.id,
        resume_id=sample_resume.id,
        tenant_id=sample_job.tenant_id,
        user_id=sample_job.user_id
    )
    
    # 验证结果
    assert result is not None
    mock_llm_caller.call_with_scene.assert_called_once()


@pytest.mark.asyncio
async def test_match_job_candidate_not_found(job_candidate_match_service):
    """测试职位或简历不存在场景"""
    # 模拟服务方法返回None
    job_candidate_match_service.job_service.get_by_id = AsyncMock(return_value=None)
    
    # 执行匹配
    result = await job_candidate_match_service.match_job_candidate(
        job_id=uuid4(),
        resume_id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4()
    )
    
    # 验证结果
    assert result is None
