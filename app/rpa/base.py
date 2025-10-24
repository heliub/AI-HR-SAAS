"""
RPA base client
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page


class BaseRPAClient(ABC):
    """RPA客户端抽象基类"""
    
    def __init__(self, platform: str, headless: bool = True):
        self.platform = platform
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    @abstractmethod
    async def initialize(self):
        """初始化浏览器"""
        pass
    
    @abstractmethod
    async def login(self, credentials: Dict[str, str]):
        """登录平台"""
        pass
    
    @abstractmethod
    async def post_job(self, job_data: Dict[str, Any]) -> str:
        """发布职位"""
        pass
    
    @abstractmethod
    async def search_candidates(
        self, 
        search_criteria: Dict[str, Any]
    ) -> List[Dict]:
        """搜索候选人"""
        pass
    
    @abstractmethod
    async def send_message(
        self, 
        candidate_id: str, 
        message: str
    ) -> bool:
        """发送消息"""
        pass
    
    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    
    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """随机延迟"""
        import random
        import asyncio
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

