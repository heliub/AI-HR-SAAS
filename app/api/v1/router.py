"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth, jobs, resumes, channels, 
    tasks, interviews, chat, account, stats, job_questions
)

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["职位管理"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["简历管理"])
api_router.include_router(channels.router, prefix="/channels", tags=["招聘渠道"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["AI招聘任务"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["面试管理"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI聊天"])
api_router.include_router(account.router, prefix="/account", tags=["账户设置"])
api_router.include_router(stats.router, prefix="/stats", tags=["统计数据"])
api_router.include_router(job_questions.router, tags=["职位问题管理"])

