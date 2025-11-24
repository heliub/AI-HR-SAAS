PROMPT_CONFIG = {
    "matching": {
        "provider": "volcengine",
        "model": "volcengine/qwen-plus",
        "temperature": 0.7,
        "max_completion_tokens": None,
        "prompt": "matching.md"
    },
    "transfer_human_intent": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.1,
        "top_p": 0.1,
        "max_completion_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "transfer_human_intent.md",
        "json_output": True,
        "alias_name": "TransferHumanIntent"
    },
    "candidate_emotion": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_completion_tokens": None,
        "prompt": "candidate_emotion.md",
        "json_output": True,
        "alias_name": "emotionToC_NEW"
    },
    "candidate_communication_willingness": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "ernie-4.5-turbo-32k",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_completion_tokens": None,
        "system": "你作为一名公司资深招聘者，当前正在使用即时消息（IM）与一位求职者进行沟通，关于这个岗位的沟通是由你主动发起的。",
        "prompt": "candidate_communication_willingness.md",
        "json_output": True,
        "alias_name": "bigCustomerUserReplyChatAgain_NEW"
    },
    "candidate_first_communication_willingness": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "ernie-4.5-turbo-32k",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_completion_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "candidate_first_communication_willingness.md",
        "json_output": False,
        "alias_name": "agreeInterviewApplyEvaluation_NEW"
    },
    "candidate_ask_question": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "glm-4-0520",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.08,
        "top_p": 0.8,
        "max_completion_tokens": None,
        "prompt": "candidate_ask_question.md",
        "json_output": True,
        "alias_name": "semanticSelectOnHelpChatWithKnowledgePure_NEW"
    },
    "answer_based_on_knowledge": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "deepseek-r1",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.8,
        "max_completion_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "answer_based_on_knowledge.md",
        "json_output": True,
        "alias_name": "KnowledgeBaseJDandQA_NEW"
    },
    "answer_without_knowledge": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.8,
        "max_completion_tokens": None,
        "prompt": "answer_without_knowledge.md",
        "json_output": True,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "alias_name": "PersonalizedQAfallbackV2"
    },
    "casual_conversation": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "qwen-max",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.1,
        "top_p": 0.1,
        "max_completion_tokens": None,
        "prompt": "casual_conversation.md",
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "json_output": True,
        "alias_name": "casualConversation"
    },
    "high_eq_response": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "qwen-max",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_completion_tokens": None,
        "prompt": "high_eq_response.md",
        "json_output": True,
        "alias_name": "changeToGoodWord_NEW"
    },
    "resume_conversation": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "qwen-plus",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_completion_tokens": None,
        "system": "你是一名礼貌的、具有同理心的AI智能招聘助手",
        "prompt": "resume_conversation.md",
        "json_output": True,
        "alias_name": "aiChatAgain"
    },
    "relevance_reply_and_question": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "glm-4-0520",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.1,
        "top_p": 0.8,
        "max_completion_tokens": None,
        "system": "你是一名专业的招聘者，正在即时通讯软件中与候选人进行问答沟通。",
        "prompt": "relevance_reply_and_question.md",
        "json_output": True,
        "alias_name": "identifyIntention_NEW"
    },
    "reply_match_question_requirement": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "glm-4-0520",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_completion_tokens": None,
        "prompt": "reply_match_question_requirement.md",
        "json_output": True,
        "alias_name": "matchCondition_NEW"
    },
    "candidate_communication_willingness_for_question": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "ernie-4.5-turbo-32k",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.1,
        "max_completion_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "candidate_communication_willingness_for_question.md",
        "json_output": True,
        "alias_name": "interviewApplyQuestionSemanticAnalysis_NEW"
    },
    "answer_based_on_knowledge_without_job_description": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "glm-4-0520",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.08,
        "top_p": 0.1,
        "max_completion_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "answer_based_on_knowledge_without_job_description.md",
        "json_output": True,
        "alias_name": "KnowledgeBaseRAG_NEW"
    },
    "continue_conversation_with_candidate": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "glm-4-0520",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_completion_tokens": None,
        "prompt": "continue_conversation_with_candidate.md",
        "json_output": False,
        "alias_name": "comprehensive_intentional_judgment_general"
    },
    "candidate_position_willingness": {
        "module": "conversation_flow",
        "provider": "volcengine",
        # "model": "ernie-4.5-turbo-32k",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "max_completion_tokens": None,
        "prompt": "candidate_position_willingness.md",
        "json_output": True,
        "alias_name": "agreeInterviewApplySemanticAnalysis_NEW"
    },
    "generate_question_variants": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.1,
        "top_p": 0.8,
        "max_completion_tokens": 2000,
        "system": "你是一个专业的HR助手，负责为知识库问题生成相似的问法变体。",
        "json_output": True,
        "prompt": "generate_question_variants.md"
    },
    "job_candidate_match.job_candidate_match_for_sales": {
        "module": "job_candidate_match",
        "provider": "volcengine",
        # "model": "deepseek-v3",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        # "top_p": 0.01,
        "max_completion_tokens": None,
        "prompt": "job_candidate_match_for_sales.md",
        "json_output": True,
        "alias_name": "doSalesResumeBlackScore"
    },
    "job_candidate_match.job_candidate_match_for_strong_skills": {
        "module": "job_candidate_match",
        "provider": "volcengine",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        # "top_p": 0.01,
        "max_completion_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "job_candidate_match_for_strong_skills.md",
        "json_output": False,
        "alias_name": "doItDouBaoResumeBlackScore"
    },
    "job_candidate_match.job_candidate_match_common": {
        "module": "job_candidate_match",
        "provider": "volcengine",
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.01,
        "max_completion_tokens": 20000,
        "prompt": "job_candidate_match_common.md",
        "json_output": True,
        "system": """
        你是一个智能职位–简历匹配分析器。任务：阅读职位描述（JD）与简历（Resume）文本，
        判断候选人是否满足岗位硬性要求，并评估软性匹配度与潜力。

        【核心判断标准】
        1. 硬性要求（Hard Requirements）
        - 必须满足，否则“不匹配”；
        - 识别关键词：必须、需具备、至少、require、must；
        - 包括：学历、经验年限、行业经验、证书、语言、关键技能；
        - 若为“优先”“希望”“更佳”等字样 → 视为软性。
            
        2. 软性要求（Soft Requirements）
        - 非必需，仅影响潜力与匹配度；
        - 判断语义相似性（如“沟通能力”“团队协作”等），
        仅作“高/中/低”打分参考，不影响过滤。
            
        3. 客观 / 主观判断区分
        - 可客观验证（学历、年限、技能、行业、语言）→ 允许直接判断；
        - 主观评价（沟通能力、性格、学习能力）→ 不作为过滤条件；
        - 若主观条件有明确客观佐证（如“多次担任销售培训讲师”）→ 可加权入潜力评分。
            
        4. 稀缺 / 普遍判断
        - 普遍技能（办公软件、基本沟通）→ 默认具备；
        - 稀缺技能（特定行业经验、专业系统）→ 若为硬性且缺失 → 不匹配。
            
        5. 判断优先级
        - 过滤结论由硬性要求决定；
        - 软性与潜力只用于评分参考；
        - 不进行结构化提取，只需理解文本内容。
            
        【输出格式】
        {
        "硬性要求匹配": [
            {"要求": "…", "是否满足": "是/否", "判断理由": "…"},
            ...
        ],
        "软性要求匹配度": "高 / 中 / 低",
        "潜力评分": 0–100,
        "过滤结果": "匹配 / 不匹配",
        "总体说明": "简要说明逻辑与不确定点（≤50字）"
        }
        """
    }
}