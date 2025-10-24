"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1 import auth, conversations, jobs, users

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

