"""
Intent classification for conversation management
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.ai.base import BaseAIClient
from app.shared.constants.enums import TaskType


class IntentClassificationResult(BaseModel):
    """意图识别结果"""
    intent: str = Field(..., description="识别出的意图类型")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    task_context: Dict[str, Any] = Field(default_factory=dict, description="任务上下文")


class IntentClassifier:
    """意图识别器"""
    
    def __init__(self, ai_client: BaseAIClient):
        self.ai_client = ai_client
    
    async def classify(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_task: Optional[Dict] = None
    ) -> IntentClassificationResult:
        """
        识别用户意图
        
        Args:
            user_message: 用户消息
            conversation_history: 会话历史
            current_task: 当前任务信息
        
        Returns:
            意图识别结果
        """
        system_prompt = self._build_intent_prompt(current_task)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-5:],  # 最近5条历史
            {"role": "user", "content": user_message}
        ]
        
        try:
            result = await self.ai_client.structured_output(
                messages=messages,
                response_model=IntentClassificationResult
            )
            return result
        except Exception:
            # 如果结构化输出失败，返回默认意图
            return IntentClassificationResult(
                intent=TaskType.GENERAL_QUESTION,
                confidence=0.5,
                task_context={}
            )
    
    def _build_intent_prompt(self, current_task: Optional[Dict]) -> str:
        """构建意图识别Prompt"""
        prompt = f"""You are an intent classifier for an HR recruitment system.

Available intents:
- {TaskType.JOB_DISCUSSION}: User discussing job requirements, posting new jobs
- {TaskType.PROGRESS_INQUIRY}: User asking about recruitment progress
- {TaskType.CANDIDATE_REVIEW}: User wanting to review candidates  
- {TaskType.RESUME_ANALYSIS}: User asking about specific resumes
- {TaskType.GENERAL_QUESTION}: General recruitment-related questions
- {TaskType.OTHER}: Other intents

Current task context: {current_task if current_task else "No active task"}

Classify the user's intent and extract relevant context.
Return JSON with:
- intent: one of the available intents
- confidence: 0-1 score
- task_context: dict with relevant extracted information (e.g., job_id, candidate_name)
"""
        return prompt

