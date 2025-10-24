"""
Base platform integration interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BasePlatformIntegration(ABC):
    """平台集成抽象基类"""
    
    @abstractmethod
    async def post_job(self, job_data: Dict[str, Any]) -> str:
        """
        发布职位
        
        Args:
            job_data: 职位数据
        
        Returns:
            平台上的职位ID
        """
        pass
    
    @abstractmethod
    async def search_candidates(
        self, 
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        搜索候选人
        
        Args:
            criteria: 搜索条件
        
        Returns:
            候选人列表
        """
        pass
    
    @abstractmethod
    async def send_message(
        self, 
        candidate_id: str, 
        message: str
    ) -> bool:
        """
        发送消息给候选人
        
        Args:
            candidate_id: 候选人ID
            message: 消息内容
        
        Returns:
            是否发送成功
        """
        pass

