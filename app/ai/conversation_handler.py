"""
Conversation handler for generating AI responses
"""
from typing import List, Dict, Any

from app.ai.base import BaseAIClient


class ConversationHandler:
    """对话处理器"""
    
    def __init__(self, ai_client: BaseAIClient):
        self.ai_client = ai_client
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        task_context: Dict[str, Any],
        intent: str,
        user_language: str = "en"
    ) -> str:
        """
        生成AI响应
        
        Args:
            user_message: 用户消息
            conversation_history: 会话历史
            task_context: 任务上下文
            intent: 识别出的意图
            user_language: 用户语言
        
        Returns:
            AI响应内容
        """
        system_prompt = self._build_system_prompt(intent, task_context, user_language)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-10:],  # 最近10条历史
            {"role": "user", "content": user_message}
        ]
        
        response = await self.ai_client.chat_completion(messages=messages)
        return response
    
    def _build_system_prompt(
        self, 
        intent: str, 
        task_context: Dict[str, Any],
        user_language: str
    ) -> str:
        """构建系统Prompt"""
        lang_instruction = {
            "en": "Respond in English.",
            "zh": "用中文回复。",
            "id": "Balas dalam bahasa Indonesia."
        }.get(user_language, "Respond in English.")
        
        prompt = f"""You are an AI assistant for an HR recruitment system.

Current task type: {intent}
Task context: {task_context}

Your role:
- Help HR professionals with recruitment tasks
- Provide clear, actionable information
- Be professional and helpful
- {lang_instruction}

Guidelines:
- For job discussions: Help define requirements and create job postings
- For progress inquiries: Provide status updates and metrics
- For candidate reviews: Help evaluate and compare candidates
- For resume analysis: Extract key information and provide insights
"""
        return prompt

