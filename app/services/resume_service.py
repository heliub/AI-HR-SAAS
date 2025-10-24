"""
Resume service
"""
from typing import Optional, BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Resume, Candidate
from app.services.base import BaseService
from app.infrastructure.storage.minio import get_storage_client


class ResumeService(BaseService[Resume]):
    """简历服务"""
    
    def __init__(self):
        super().__init__(Resume)
        self.storage_client = get_storage_client()
    
    async def upload_resume(
        self,
        db: AsyncSession,
        tenant_id: int,
        candidate_id: int,
        file: BinaryIO,
        file_name: str,
        file_type: str,
        file_size: int,
        job_id: Optional[int] = None
    ) -> Resume:
        """上传简历"""
        # 生成存储key
        object_name = f"resumes/{tenant_id}/{candidate_id}/{file_name}"
        
        # 上传到对象存储
        file_key = await self.storage_client.upload(
            file=file,
            object_name=object_name,
            content_type="application/pdf" if file_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # 创建简历记录
        resume_data = {
            "tenant_id": tenant_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "file_key": file_key,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "parse_status": "pending",
            "source": "manual"
        }
        
        resume = await self.repository.create(db, resume_data)
        await db.commit()
        await db.refresh(resume)
        
        return resume

