PROMPT_CONFIG = {
    "matching": {
        "provider": "volcengine",
        "model": "volcengine/qwen-plus",
        "temperature": 0.7,
        "max_tokens": None,
        "prompt": "matching.md"
    },
    "transfer_human_intent": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "doubao-1.5-pro-32k-250115",
        "temperature": 0.1,
        "top_p": 0.1,
        "max_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "transfer_human_intent.md",
        "alias_name": "TransferHumanIntent"
    },
    "candidate_emotion": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "deepseek-r1",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "prompt": "candidate_emotion.md",
        "alias_name": "emotionToC_NEW"
    },
    "candidate_communication_willingness": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "ernie-4.5-turbo-32k",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "system": "你作为一名公司资深招聘者，当前正在使用即时消息（IM）与一位求职者进行沟通，关于这个岗位的沟通是由你主动发起的。",
        "prompt": "candidate_communication_willingness.md",
        "alias_name": "bigCustomerUserReplyChatAgain_NEW"
    },
    "candidate_first_communication_willingness": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "ernie-4.5-turbo-32k",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "candidate_first_communication_willingness.md",
        "alias_name": "agreeInterviewApplyEvaluation_NEW"
    },
    "candidate_ask_question": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "glm-4-0520",
        "temperature": 0.08,
        "top_p": 0.8,
        "max_tokens": None,
        "prompt": "candidate_ask_question.md",
        "alias_name": "semanticSelectOnHelpChatWithKnowledgePure_NEW"
    },
    "answer_based_on_knowledge": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "deepseek-r1",
        "temperature": 0.01,
        "top_p": 0.8,
        "max_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "answer_based_on_knowledge.md",
        "alias_name": "KnowledgeBaseJDandQA_NEW"
    },
    "answer_without_knowledge": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "deepseek-r1",
        "temperature": 0.01,
        "top_p": 0.8,
        "max_tokens": None,
        "prompt": "answer_without_knowledge.md",
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "alias_name": "PersonalizedQAfallbackV2"
    },
    "casual_conversation": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "qwen-max",
        "temperature": 0.1,
        "top_p": 0.1,
        "max_tokens": None,
        "prompt": "casual_conversation.md",
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "alias_name": "casualConversation"
    },
    "high_eq_response": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "qwen-max",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "prompt": "high_eq_response.md",
        "alias_name": "changeToGoodWord_NEW"
    },
    "resume_conversation": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "qwen-plus",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "system": "你是一名礼貌的、具有同理心的AI智能招聘助手",
        "prompt": "resume_conversation.md",
        "alias_name": "aiChatAgain"
    },
    "relevance_reply_and_question": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "glm-4-0520",
        "temperature": 0.1,
        "top_p": 0.8,
        "max_tokens": None,
        "system": "你是一名专业的招聘者，正在即时通讯软件中与候选人进行问答沟通。",
        "prompt": "relevance_reply_and_question.md",
        "alias_name": "identifyIntention_NEW"
    },
    "reply_match_question_requirement": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "glm-4-0520",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "prompt": "reply_match_question_requirement.md",
        "alias_name": "matchCondition_NEW"
    },
    "candidate_communication_willingness_for_question": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "ernie-4.5-turbo-32k",
        "temperature": 0.1,
        "max_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "candidate_communication_willingness_for_question.md",
        "alias_name": "interviewApplyQuestionSemanticAnalysis_NEW"
    },
    "answer_based_on_knowledge_without_job_description": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "glm-4-0520",
        "temperature": 0.08,
        "top_p": 0.1,
        "max_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "answer_based_on_knowledge_without_job_description.md",
        "alias_name": "KnowledgeBaseRAG_NEW"
    },
    "continue_conversation_with_candidate": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "glm-4-0520",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "prompt": "continue_conversation_with_candidate.md",
        "alias_name": "comprehensive_intentional_judgment_general"
    },
    "candidate_position_willingness": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "ernie-4.5-turbo-32k",
        "temperature": 0.01,
        "max_tokens": None,
        "prompt": "candidate_position_willingness.md",
        "alias_name": "agreeInterviewApplySemanticAnalysis_NEW"
    },
    "generate_question_variants": {
        "module": "conversation_flow",
        "provider": "volcengine",
        "model": "doubao-1.5-pro-32k-250115",
        "temperature": 0.1,
        "top_p": 0.8,
        "max_tokens": 2000,
        "system": "你是一个专业的HR助手，负责为知识库问题生成相似的问法变体。",
        "prompt": "generate_question_variants.md"
    },
    "job_candidate_match.job_candidate_match_for_sales": {
        "module": "job_candidate_match",
        "provider": "volcengine",
        "model": "deepseek-v3",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "prompt": "job_candidate_match_for_sales.md",
        "alias_name": "doSalesResumeBlackScore"
    },
    "job_candidate_match.job_candidate_match_for_strong_skills": {
        "module": "job_candidate_match",
        "provider": "volcengine",
        "model": "doubao-1.5-pro-32k-250115",
        "temperature": 0.01,
        "top_p": 0.01,
        "max_tokens": None,
        "system": "你是一个 AI 助手，你能根据我的要求给我准确的回复，并且会简明扼要的回答。",
        "prompt": "job_candidate_match_for_strong_skills.md",
        "alias_name": "doItDouBaoResumeBlackScore"
    }
}

