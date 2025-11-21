"""
Enumerations
"""
from enum import Enum


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    HR = "hr"


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class TaskType(str, Enum):
    """任务类型"""
    JOB_DISCUSSION = "job_discussion"
    PROGRESS_INQUIRY = "progress_inquiry"
    CANDIDATE_REVIEW = "candidate_review"
    RESUME_ANALYSIS = "resume_analysis"
    GENERAL_QUESTION = "general_question"
    OTHER = "other"


class TaskStatus(str, Enum):
    """任务状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class JobStatus(str, Enum):
    """职位状态"""
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold"


class EmploymentType(str, Enum):
    """雇佣类型"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class ResumeParseStatus(str, Enum):
    """简历解析状态"""
    PENDING = "pending"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResumeSource(str, Enum):
    """简历来源"""
    EMAIL = "email"
    PLATFORM = "platform"
    MANUAL = "manual"


class MatchingResult(str, Enum):
    """匹配结果"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class MatchingStatus(str, Enum):
    """匹配状态"""
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Platform(str, Enum):
    """平台"""
    LINKEDIN = "linkedin"
    JOBSTREET = "jobstreet"


class PlatformAccountStatus(str, Enum):
    """平台账号状态"""
    ACTIVE = "active"
    INVALID = "invalid"
    SUSPENDED = "suspended"


class EmailProtocol(str, Enum):
    """邮件协议"""
    EXCHANGE = "exchange"
    IMAP = "imap"
    POP3 = "pop3"


class ChatMessageType(str, Enum):
    """聊天消息类型"""
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class AsyncTaskType(str, Enum):
    """异步任务类型"""
    RESUME_PARSE = "resume_parse"
    EMAIL_SYNC = "email_sync"
    RPA_JOB_POST = "rpa_job_post"
    RPA_CANDIDATE_SEARCH = "rpa_candidate_search"
    RPA_MESSAGE_SEND = "rpa_message_send"
    MATCHING = "matching"
    CHAT_GENERATION = "chat_generation"


class AsyncTaskStatus(str, Enum):
    """异步任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class Language(str, Enum):
    """语言"""
    ENGLISH = "en"
    CHINESE = "zh"
    INDONESIAN = "id"


class QuestionType(str, Enum):
    """问题类型"""
    INFORMATION = "information"  # 信息采集
    ASSESSMENT = "assessment"   # 考察评估（判卷）

class QuestionStatus(str, Enum):
    """问题状态"""
    PENDING = "pending"  # 待处理
    ONGOING = "ongoing"  # 进行中
    COMPLETED = "completed"  # 已完成
    SKIPPED = "skipped"  # 已跳过
    DELETED = "deleted"  # 已删除

class CandidateMessageRole(str, Enum):
    """候选人消息角色"""
    CANDIDATE = "candidate"
    HR = "hr"