-- AI HR SaaS PostgreSQL Database Schema (Multi-Tenant, Optimized)
-- Version: 2.1
-- Created: 2025-01-26
-- Updated: 2025-01-26
-- 
-- 优化说明：
-- 1. 合并职位要求到职位表（使用TEXT数组）
-- 2. 合并项目技术栈到项目经历表（使用TEXT数组）
-- 3. 合并期望地点到求职意向表（使用TEXT数组）
-- 4. 合并AI匹配优势/劣势到匹配结果表（使用JSONB）
-- 5. 增强聊天消息类型字段，支持多种消息类型
-- 
-- 表数量：从33张减少到26张

-- ==============================================
-- 1. 租户管理表
-- ==============================================

-- 租户表（公司）
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    company_name VARCHAR(200),
    contact_name VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    plan_type VARCHAR(50) DEFAULT 'basic',
    status VARCHAR(20) DEFAULT 'active',
    max_users INTEGER DEFAULT 10,
    max_jobs INTEGER DEFAULT 50,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tenants IS '租户表（公司）';
COMMENT ON COLUMN tenants.id IS '租户ID（主键）';
COMMENT ON COLUMN tenants.name IS '租户名称';
COMMENT ON COLUMN tenants.company_name IS '公司名称';
COMMENT ON COLUMN tenants.contact_name IS '联系人姓名';
COMMENT ON COLUMN tenants.contact_email IS '联系人邮箱';
COMMENT ON COLUMN tenants.contact_phone IS '联系人电话';
COMMENT ON COLUMN tenants.plan_type IS '套餐类型: basic-基础版, pro-专业版, enterprise-企业版';
COMMENT ON COLUMN tenants.status IS '状态: active-激活, inactive-停用, suspended-暂停';
COMMENT ON COLUMN tenants.max_users IS '最大用户数';
COMMENT ON COLUMN tenants.max_jobs IS '最大职位数';
COMMENT ON COLUMN tenants.expires_at IS '到期时间';
COMMENT ON COLUMN tenants.created_at IS '创建时间';
COMMENT ON COLUMN tenants.updated_at IS '更新时间';

-- ==============================================
-- 2. 用户和认证表
-- ==============================================

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.id IS '用户ID（主键）';
COMMENT ON COLUMN users.tenant_id IS '租户ID';
COMMENT ON COLUMN users.name IS '用户姓名';
COMMENT ON COLUMN users.email IS '邮箱地址';
COMMENT ON COLUMN users.password_hash IS '密码哈希值（bcrypt加密）';
COMMENT ON COLUMN users.role IS '用户角色: admin-管理员, hr-人力资源, recruiter-招聘专员';
COMMENT ON COLUMN users.avatar_url IS '头像URL';
COMMENT ON COLUMN users.created_at IS '创建时间';
COMMENT ON COLUMN users.updated_at IS '更新时间';
COMMENT ON COLUMN users.last_login_at IS '最后登录时间';
COMMENT ON COLUMN users.is_active IS '是否激活';

-- 用户设置表
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    language VARCHAR(10) DEFAULT 'zh',
    email_notifications BOOLEAN DEFAULT TRUE,
    task_reminders BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE user_settings IS '用户设置表';
COMMENT ON COLUMN user_settings.id IS '设置ID（主键）';
COMMENT ON COLUMN user_settings.tenant_id IS '租户ID';
COMMENT ON COLUMN user_settings.user_id IS '用户ID';
COMMENT ON COLUMN user_settings.language IS '界面语言: zh-中文, en-英文, id-印尼语';
COMMENT ON COLUMN user_settings.email_notifications IS '是否开启邮件通知';
COMMENT ON COLUMN user_settings.task_reminders IS '是否开启任务提醒';
COMMENT ON COLUMN user_settings.created_at IS '创建时间';
COMMENT ON COLUMN user_settings.updated_at IS '更新时间';

-- 认证Token表
CREATE TABLE auth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_revoked BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE auth_tokens IS '认证Token表';
COMMENT ON COLUMN auth_tokens.id IS 'Token ID（主键）';
COMMENT ON COLUMN auth_tokens.tenant_id IS '租户ID';
COMMENT ON COLUMN auth_tokens.user_id IS '用户ID';
COMMENT ON COLUMN auth_tokens.token IS 'JWT Token字符串';
COMMENT ON COLUMN auth_tokens.expires_at IS 'Token过期时间';
COMMENT ON COLUMN auth_tokens.created_at IS '创建时间';
COMMENT ON COLUMN auth_tokens.is_revoked IS '是否已撤销';
COMMENT ON COLUMN auth_tokens.updated_at IS '更新时间';

-- ==============================================
-- 3. 职位管理表
-- ==============================================

-- 职位表（优化：合并职位要求和偏好学校，支持LinkedIn/JobStreet标准字段）
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    title VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    location VARCHAR(100),
    type VARCHAR(20),
    status VARCHAR(20) NOT NULL,
    min_salary INTEGER,
    max_salary INTEGER,
    description TEXT,
    requirements TEXT,
    preferred_schools TEXT,
    recruitment_invitation TEXT,
    min_age INTEGER,
    max_age INTEGER,
    gender VARCHAR(20),
    education VARCHAR(100),
    job_level VARCHAR(50),
    applicants_count INTEGER DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    -- LinkedIn/JobStreet 标准字段
    company VARCHAR(200),
    workplace_type VARCHAR(20),
    pay_type VARCHAR(20),
    pay_currency VARCHAR(10) DEFAULT 'CNY',
    pay_shown_on_ad BOOLEAN DEFAULT FALSE,
    category VARCHAR(100)
);

COMMENT ON TABLE jobs IS '职位表（已合并职位要求和偏好学校，支持LinkedIn/JobStreet标准字段）';
COMMENT ON COLUMN jobs.id IS '职位ID（主键）';
COMMENT ON COLUMN jobs.tenant_id IS '租户ID';
COMMENT ON COLUMN jobs.user_id IS '创建该职位的HR用户ID';
COMMENT ON COLUMN jobs.title IS '职位标题';
COMMENT ON COLUMN jobs.department IS '所属部门';
COMMENT ON COLUMN jobs.location IS '工作地点';
COMMENT ON COLUMN jobs.type IS '职位类型: full-time-全职, part-time-兼职, contract-合同, intern-实习, temporary-临时工, volunteer-志愿者, casual-兼职';
COMMENT ON COLUMN jobs.status IS '职位状态: open-开放, closed-关闭, draft-草稿, deleted-已删除';
COMMENT ON COLUMN jobs.min_salary IS '最低薪资（单位：元/月）';
COMMENT ON COLUMN jobs.max_salary IS '最高薪资（单位：元/月）';
COMMENT ON COLUMN jobs.description IS '职位描述';
COMMENT ON COLUMN jobs.requirements IS '职位要求（多个要求用分隔符分开，如逗号）';
COMMENT ON COLUMN jobs.preferred_schools IS '偏好学校（多个学校用分隔符分开，如逗号）';
COMMENT ON COLUMN jobs.recruitment_invitation IS '招聘邀请语';
COMMENT ON COLUMN jobs.min_age IS '最低年龄要求';
COMMENT ON COLUMN jobs.max_age IS '最高年龄要求';
COMMENT ON COLUMN jobs.gender IS '性别要求: male-男, female-女, unlimited-不限';
COMMENT ON COLUMN jobs.education IS '学历要求';
COMMENT ON COLUMN jobs.job_level IS '职级要求，如：P6-P7';
COMMENT ON COLUMN jobs.applicants_count IS '申请人数（冗余字段）';
COMMENT ON COLUMN jobs.created_by IS '创建人用户ID';
COMMENT ON COLUMN jobs.created_at IS '创建时间';
COMMENT ON COLUMN jobs.updated_at IS '更新时间';
COMMENT ON COLUMN jobs.published_at IS '发布时间';
COMMENT ON COLUMN jobs.closed_at IS '关闭时间';
-- LinkedIn/JobStreet 标准字段注释
COMMENT ON COLUMN jobs.company IS '公司名称';
COMMENT ON COLUMN jobs.workplace_type IS '工作场所类型: on-site-现场办公, hybrid-混合办公, remote-远程办公';
COMMENT ON COLUMN jobs.pay_type IS '薪资类型: hourly-时薪, monthly-月薪, annual-年薪, annual_plus_commission-年薪加提成';
COMMENT ON COLUMN jobs.pay_currency IS '薪资货币: CNY-人民币, USD-美元, EUR-欧元, GBP-英镑, JPY-日元, KRW-韩元, SGD-新加坡元, HKD-港币, AUD-澳元, CAD-加元, CHF-瑞士法郎, SEK-瑞典克朗, NOK-挪威克朗, DKK-丹麦克朗, INR-印度卢比, MYR-马来西亚林吉特, THB-泰铢, PHP-菲律宾比索, IDR-印尼盾, NZD-新西兰元';
COMMENT ON COLUMN jobs.pay_shown_on_ad IS '是否在广告中显示薪资: true-显示, false-不显示';
COMMENT ON COLUMN jobs.category IS '职位分类: IT-技术类, 销售-营销类, 财务-会计类, 人事-行政类, 运营-管理类, 设计-创意类, 工程-技术类, 客服-支持类, 教学-培训类, 医疗-健康类, 制造-生产类, 物流-仓储类, 建筑-工程类, 法律-合规类, 咨询-顾问类, 媒体-传媒类, 零售-服务类, 金融-银行类, 保险-证券类, 房地产-建筑类, 旅游-酒店类, 餐饮-食品类, 娱乐-休闲类, 体育-健身类, 教育-科研类, 政府-公共类, 非营利组织类';

-- ==============================================
-- 4. 招聘渠道表
-- ==============================================

-- 渠道表
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20),
    status VARCHAR(20),
    applicants_count INTEGER DEFAULT 0,
    annual_cost DECIMAL(10, 2),
    cost_currency VARCHAR(10) DEFAULT 'CNY',
    api_key TEXT,
    contact_person VARCHAR(100),
    contact_email VARCHAR(255),
    description TEXT,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE channels IS '招聘渠道表';
COMMENT ON COLUMN channels.id IS '渠道ID（主键）';
COMMENT ON COLUMN channels.tenant_id IS '租户ID';
COMMENT ON COLUMN channels.user_id IS '负责该渠道的HR用户ID';
COMMENT ON COLUMN channels.name IS '渠道名称';
COMMENT ON COLUMN channels.type IS '渠道类型: job-board-招聘网站, social-media-社交媒体, referral-内推, agency-猎头, website-官网';
COMMENT ON COLUMN channels.status IS '渠道状态: active-激活, inactive-停用';
COMMENT ON COLUMN channels.applicants_count IS '该渠道总申请人数（冗余字段）';
COMMENT ON COLUMN channels.annual_cost IS '年度成本';
COMMENT ON COLUMN channels.cost_currency IS '货币单位';
COMMENT ON COLUMN channels.api_key IS 'API密钥（用于对接第三方平台）';
COMMENT ON COLUMN channels.contact_person IS '渠道联系人';
COMMENT ON COLUMN channels.contact_email IS '渠道联系邮箱';
COMMENT ON COLUMN channels.description IS '渠道描述';
COMMENT ON COLUMN channels.last_sync_at IS '最后同步时间';
COMMENT ON COLUMN channels.created_at IS '创建时间';
COMMENT ON COLUMN channels.updated_at IS '更新时间';

-- 职位发布渠道关联表
CREATE TABLE job_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    job_id UUID NOT NULL,
    channel_id UUID NOT NULL,
    published_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    external_id VARCHAR(100),
    external_url TEXT,
    views_count INTEGER DEFAULT 0,
    clicks_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE job_channels IS '职位发布渠道关联表';
COMMENT ON COLUMN job_channels.id IS '关联ID（主键）';
COMMENT ON COLUMN job_channels.tenant_id IS '租户ID';
COMMENT ON COLUMN job_channels.job_id IS '职位ID';
COMMENT ON COLUMN job_channels.channel_id IS '渠道ID';
COMMENT ON COLUMN job_channels.published_at IS '发布时间';
COMMENT ON COLUMN job_channels.external_id IS '外部平台的职位ID';
COMMENT ON COLUMN job_channels.external_url IS '外部平台的职位URL';
COMMENT ON COLUMN job_channels.views_count IS '浏览次数';
COMMENT ON COLUMN job_channels.clicks_count IS '点击次数';
COMMENT ON COLUMN job_channels.created_at IS '创建时间';
COMMENT ON COLUMN job_channels.updated_at IS '更新时间';
-- ==============================================
-- 5. 简历管理表
-- ==============================================

-- 简历表
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    candidate_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    position VARCHAR(200),
    status VARCHAR(20) NOT NULL,
    source VARCHAR(100),
    source_channel_id UUID,
    job_id UUID,
    experience_years VARCHAR(20),
    education_level VARCHAR(50),
    age INTEGER,
    gender VARCHAR(20),
    location VARCHAR(100),
    school VARCHAR(200),
    major VARCHAR(200),
    skills TEXT,
    resume_url TEXT,
    conversation_summary TEXT,
    is_match BOOLEAN,
    match_conclusion TEXT,
    submitted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE resumes IS '简历表（已合并技能列表）';
COMMENT ON COLUMN resumes.id IS '简历ID（主键）';
COMMENT ON COLUMN resumes.tenant_id IS '租户ID';
COMMENT ON COLUMN resumes.user_id IS '负责处理该简历的HR用户ID';
COMMENT ON COLUMN resumes.candidate_name IS '候选人姓名';
COMMENT ON COLUMN resumes.email IS '候选人邮箱';
COMMENT ON COLUMN resumes.phone IS '候选人电话';
COMMENT ON COLUMN resumes.position IS '应聘职位';
COMMENT ON COLUMN resumes.status IS '简历状态: pending-待处理, reviewing-审核中, interview-面试中, offered-已发offer, rejected-已拒绝';
COMMENT ON COLUMN resumes.source IS '简历来源渠道名称';
COMMENT ON COLUMN resumes.source_channel_id IS '来源渠道ID';
COMMENT ON COLUMN resumes.job_id IS '应聘职位ID';
COMMENT ON COLUMN resumes.experience_years IS '工作年限，如：5年';
COMMENT ON COLUMN resumes.education_level IS '学历水平，如：本科、硕士';
COMMENT ON COLUMN resumes.age IS '年龄';
COMMENT ON COLUMN resumes.gender IS '性别: male-男, female-女';
COMMENT ON COLUMN resumes.location IS '所在城市';
COMMENT ON COLUMN resumes.school IS '毕业院校';
COMMENT ON COLUMN resumes.major IS '专业';
COMMENT ON COLUMN resumes.skills IS '技能列表（多个技能用分隔符分开，如逗号）';
COMMENT ON COLUMN resumes.resume_url IS '简历文件URL';
COMMENT ON COLUMN resumes.conversation_summary IS 'AI对话总结';
COMMENT ON COLUMN resumes.is_match IS '是否匹配（基于AI分析结果）';
COMMENT ON COLUMN resumes.match_conclusion IS '匹配结论（基于AI分析结果）';
COMMENT ON COLUMN resumes.submitted_at IS '简历投递时间';
COMMENT ON COLUMN resumes.created_at IS '创建时间';
COMMENT ON COLUMN resumes.updated_at IS '更新时间';

-- 工作经历表
CREATE TABLE work_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    company VARCHAR(200),
    position VARCHAR(200),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE work_experiences IS '工作经历表';
COMMENT ON COLUMN work_experiences.id IS '经历ID（主键）';
COMMENT ON COLUMN work_experiences.tenant_id IS '租户ID';
COMMENT ON COLUMN work_experiences.resume_id IS '简历ID';
COMMENT ON COLUMN work_experiences.company IS '公司名称';
COMMENT ON COLUMN work_experiences.position IS '职位';
COMMENT ON COLUMN work_experiences.start_date IS '开始日期，如：2021-03';
COMMENT ON COLUMN work_experiences.end_date IS '结束日期，如：至今、2024-12';
COMMENT ON COLUMN work_experiences.description IS '工作描述';
COMMENT ON COLUMN work_experiences.sort_order IS '显示排序（越小越靠前）';
COMMENT ON COLUMN work_experiences.created_at IS '创建时间';
COMMENT ON COLUMN work_experiences.updated_at IS '更新时间';
-- 项目经历表（优化：合并技术栈）
CREATE TABLE project_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    role VARCHAR(100),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    description TEXT,
    technologies TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE project_experiences IS '项目经历表（已合并技术栈）';
COMMENT ON COLUMN project_experiences.id IS '项目ID（主键）';
COMMENT ON COLUMN project_experiences.tenant_id IS '租户ID';
COMMENT ON COLUMN project_experiences.resume_id IS '简历ID';
COMMENT ON COLUMN project_experiences.project_name IS '项目名称';
COMMENT ON COLUMN project_experiences.role IS '在项目中的角色';
COMMENT ON COLUMN project_experiences.start_date IS '开始日期';
COMMENT ON COLUMN project_experiences.end_date IS '结束日期';
COMMENT ON COLUMN project_experiences.description IS '项目描述';
COMMENT ON COLUMN project_experiences.technologies IS '技术栈列表（多个技术用分隔符分开，如逗号）';
COMMENT ON COLUMN project_experiences.sort_order IS '显示排序（越小越靠前）';
COMMENT ON COLUMN project_experiences.created_at IS '创建时间';
COMMENT ON COLUMN project_experiences.updated_at IS '更新时间';
-- 教育经历表
CREATE TABLE education_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    school VARCHAR(200) NOT NULL,
    degree VARCHAR(50),
    major VARCHAR(200),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE education_histories IS '教育经历表';
COMMENT ON COLUMN education_histories.id IS '教育经历ID（主键）';
COMMENT ON COLUMN education_histories.tenant_id IS '租户ID';
COMMENT ON COLUMN education_histories.resume_id IS '简历ID';
COMMENT ON COLUMN education_histories.school IS '学校名称';
COMMENT ON COLUMN education_histories.degree IS '学位，如：本科、硕士、博士';
COMMENT ON COLUMN education_histories.major IS '专业';
COMMENT ON COLUMN education_histories.start_date IS '开始日期';
COMMENT ON COLUMN education_histories.end_date IS '结束日期';
COMMENT ON COLUMN education_histories.sort_order IS '显示排序（越小越靠前）';
COMMENT ON COLUMN education_histories.created_at IS '创建时间';
COMMENT ON COLUMN education_histories.updated_at IS '更新时间'; 
-- 求职意向表（优化：合并期望地点）
CREATE TABLE job_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    expected_salary VARCHAR(50),
    preferred_locations TEXT,
    job_type VARCHAR(50),
    available_date DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE job_preferences IS '求职意向表（已合并期望地点）';
COMMENT ON COLUMN job_preferences.id IS '意向ID（主键）';
COMMENT ON COLUMN job_preferences.tenant_id IS '租户ID';
COMMENT ON COLUMN job_preferences.resume_id IS '简历ID';
COMMENT ON COLUMN job_preferences.expected_salary IS '期望薪资';
COMMENT ON COLUMN job_preferences.preferred_locations IS '期望工作地点（多个地点用分隔符分开，如逗号）';
COMMENT ON COLUMN job_preferences.job_type IS '期望工作类型，如：全职、兼职';
COMMENT ON COLUMN job_preferences.available_date IS '最早到岗日期';
COMMENT ON COLUMN job_preferences.created_at IS '创建时间';
COMMENT ON COLUMN job_preferences.updated_at IS '更新时间';

-- AI匹配结果表（优化：合并优势和劣势）
CREATE TABLE ai_match_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    resume_id UUID NOT NULL,
    job_id UUID NOT NULL,
    is_match BOOLEAN,
    match_score INTEGER,
    reason TEXT,
    strengths TEXT,
    weaknesses TEXT,
    recommendation TEXT,
    analyzed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ai_match_results IS 'AI简历匹配结果表（已合并优势和劣势）';
COMMENT ON COLUMN ai_match_results.id IS '匹配结果ID（主键）';
COMMENT ON COLUMN ai_match_results.tenant_id IS '租户ID';
COMMENT ON COLUMN ai_match_results.user_id IS '触发匹配的HR用户ID';
COMMENT ON COLUMN ai_match_results.resume_id IS '简历ID';
COMMENT ON COLUMN ai_match_results.job_id IS '职位ID';
COMMENT ON COLUMN ai_match_results.is_match IS '是否匹配';
COMMENT ON COLUMN ai_match_results.match_score IS '匹配分数（0-100）';
COMMENT ON COLUMN ai_match_results.reason IS 'AI分析原因';
COMMENT ON COLUMN ai_match_results.strengths IS '优势列表（多个优势用分隔符分开，如逗号）';
COMMENT ON COLUMN ai_match_results.weaknesses IS '劣势列表（多个劣势用分隔符分开，如逗号）';
COMMENT ON COLUMN ai_match_results.recommendation IS 'AI推荐意见';
COMMENT ON COLUMN ai_match_results.analyzed_at IS 'AI分析时间';
COMMENT ON COLUMN ai_match_results.created_at IS '创建时间';
COMMENT ON COLUMN ai_match_results.updated_at IS '更新时间';
-- ==============================================
-- 6. AI招聘任务表
-- ==============================================

-- AI招聘任务表
CREATE TABLE recruitment_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    job_id UUID NOT NULL,
    job_title VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_by UUID,
    channels_published INTEGER DEFAULT 0,
    total_channels INTEGER DEFAULT 0,
    resumes_viewed INTEGER DEFAULT 0,
    greetings_sent INTEGER DEFAULT 0,
    conversations_active INTEGER DEFAULT 0,
    resumes_requested INTEGER DEFAULT 0,
    resumes_received INTEGER DEFAULT 0,
    interviews_scheduled INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE recruitment_tasks IS 'AI招聘任务表';
COMMENT ON COLUMN recruitment_tasks.id IS '任务ID（主键）';
COMMENT ON COLUMN recruitment_tasks.tenant_id IS '租户ID';
COMMENT ON COLUMN recruitment_tasks.user_id IS '任务负责人HR用户ID';
COMMENT ON COLUMN recruitment_tasks.job_id IS '关联职位ID';
COMMENT ON COLUMN recruitment_tasks.job_title IS '职位标题（冗余字段）';
COMMENT ON COLUMN recruitment_tasks.status IS '任务状态: not-started-未开始, in-progress-进行中, paused-已暂停, completed-已完成';
COMMENT ON COLUMN recruitment_tasks.created_by IS '创建人用户ID';
COMMENT ON COLUMN recruitment_tasks.channels_published IS '已发布渠道数';
COMMENT ON COLUMN recruitment_tasks.total_channels IS '计划发布总渠道数';
COMMENT ON COLUMN recruitment_tasks.resumes_viewed IS 'AI已浏览简历数';
COMMENT ON COLUMN recruitment_tasks.greetings_sent IS 'AI已发送问候数';
COMMENT ON COLUMN recruitment_tasks.conversations_active IS 'AI活跃对话数';
COMMENT ON COLUMN recruitment_tasks.resumes_requested IS 'AI请求完整简历数';
COMMENT ON COLUMN recruitment_tasks.resumes_received IS 'AI收到完整简历数';
COMMENT ON COLUMN recruitment_tasks.interviews_scheduled IS 'AI安排面试数';
COMMENT ON COLUMN recruitment_tasks.created_at IS '任务创建时间';
COMMENT ON COLUMN recruitment_tasks.updated_at IS '任务更新时间';
COMMENT ON COLUMN recruitment_tasks.completed_at IS '任务完成时间';

-- ==============================================
-- 7. 面试管理表
-- ==============================================

-- 面试表
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    candidate_id UUID NOT NULL,
    candidate_name VARCHAR(100) NOT NULL,
    position VARCHAR(200),
    interview_date DATE NOT NULL,
    interview_time TIME NOT NULL,
    interviewer VARCHAR(100),
    interviewer_title VARCHAR(100),
    type VARCHAR(20),
    status VARCHAR(20) NOT NULL,
    location VARCHAR(200),
    meeting_link TEXT,
    notes TEXT,
    feedback TEXT,
    rating INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT
);

COMMENT ON TABLE interviews IS '面试表';
COMMENT ON COLUMN interviews.id IS '面试ID（主键）';
COMMENT ON COLUMN interviews.tenant_id IS '租户ID';
COMMENT ON COLUMN interviews.user_id IS '安排面试的HR用户ID';
COMMENT ON COLUMN interviews.candidate_id IS '候选人简历ID';
COMMENT ON COLUMN interviews.candidate_name IS '候选人姓名（冗余字段）';
COMMENT ON COLUMN interviews.position IS '应聘职位（冗余字段）';
COMMENT ON COLUMN interviews.interview_date IS '面试日期';
COMMENT ON COLUMN interviews.interview_time IS '面试时间';
COMMENT ON COLUMN interviews.interviewer IS '面试官姓名';
COMMENT ON COLUMN interviews.interviewer_title IS '面试官职位';
COMMENT ON COLUMN interviews.type IS '面试类型: phone-电话面试, video-视频面试, onsite-现场面试';
COMMENT ON COLUMN interviews.status IS '面试状态: scheduled-已安排, completed-已完成, cancelled-已取消, rescheduled-已改期';
COMMENT ON COLUMN interviews.location IS '面试地点（现场面试）';
COMMENT ON COLUMN interviews.meeting_link IS '会议链接（视频面试）';
COMMENT ON COLUMN interviews.notes IS '面试备注';
COMMENT ON COLUMN interviews.feedback IS '面试反馈';
COMMENT ON COLUMN interviews.rating IS '面试评分（1-5分）';
COMMENT ON COLUMN interviews.created_at IS '创建时间';
COMMENT ON COLUMN interviews.updated_at IS '更新时间';
COMMENT ON COLUMN interviews.cancelled_at IS '取消时间';
COMMENT ON COLUMN interviews.cancellation_reason IS '取消原因';

-- ==============================================
-- 8. AI聊天模块表
-- ==============================================

-- AI聊天会话表
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chat_sessions IS 'AI聊天会话表';
COMMENT ON COLUMN chat_sessions.id IS '会话ID（主键）';
COMMENT ON COLUMN chat_sessions.tenant_id IS '租户ID';
COMMENT ON COLUMN chat_sessions.user_id IS '用户ID';
COMMENT ON COLUMN chat_sessions.title IS '会话标题';
COMMENT ON COLUMN chat_sessions.created_at IS '创建时间';
COMMENT ON COLUMN chat_sessions.updated_at IS '最后更新时间';

-- AI聊天消息表（增强：支持多种消息类型）
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT,
    message_type VARCHAR(50) DEFAULT 'text',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chat_messages IS 'AI聊天消息表（支持多种消息类型）';
COMMENT ON COLUMN chat_messages.id IS '消息ID（主键）';
COMMENT ON COLUMN chat_messages.tenant_id IS '租户ID';
COMMENT ON COLUMN chat_messages.user_id IS '发送消息的用户ID';
COMMENT ON COLUMN chat_messages.session_id IS '会话ID';
COMMENT ON COLUMN chat_messages.role IS '消息角色: user-用户, assistant-AI助手, system-系统';
COMMENT ON COLUMN chat_messages.content IS '消息内容';
COMMENT ON COLUMN chat_messages.message_type IS '消息类型: text-普通文本, tool_call-工具调用请求, tool_result-工具执行结果, thinking-AI思考过程, code-代码, image-图片, file-文件';
COMMENT ON COLUMN chat_messages.metadata IS '消息元数据（JSONB格式），用于存储工具调用参数、结果、思考标记等扩展信息，如：{"tool_name":"search_resumes","tool_args":{"keyword":"前端"},"execution_time":1.2}';
COMMENT ON COLUMN chat_messages.created_at IS '消息发送时间';
COMMENT ON COLUMN chat_messages.updated_at IS '更新时间';
-- 候选人AI聊天历史表（增强：支持多种消息类型）
CREATE TABLE candidate_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    sender VARCHAR(20) ,
    message TEXT,
    message_type VARCHAR(50) DEFAULT 'text',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE candidate_chat_history IS '候选人AI聊天历史表（支持多种消息类型）';
COMMENT ON COLUMN candidate_chat_history.id IS '消息ID（主键）';
COMMENT ON COLUMN candidate_chat_history.tenant_id IS '租户ID';
COMMENT ON COLUMN candidate_chat_history.resume_id IS '简历ID';
COMMENT ON COLUMN candidate_chat_history.sender IS '发送者: ai-AI助手, candidate-候选人';
COMMENT ON COLUMN candidate_chat_history.message IS '消息内容';
COMMENT ON COLUMN candidate_chat_history.message_type IS '消息类型: text-普通文本, greeting-问候, question-提问, answer-回答, document_request-文档请求, schedule-日程安排';
COMMENT ON COLUMN candidate_chat_history.metadata IS '消息元数据（JSONB格式），如：{"document_type":"resume","status":"sent","scheduled_time":"2025-01-15 14:00"}';
COMMENT ON COLUMN candidate_chat_history.created_at IS '消息发送时间';
COMMENT ON COLUMN candidate_chat_history.updated_at IS '更新时间';
-- ==============================================
-- 8.1. 职位问题预设表
-- ==============================================

-- 职位问题预设表
CREATE TABLE job_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    job_id UUID NOT NULL,
    question TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    evaluation_criteria TEXT,
    sort_order INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE job_questions IS '职位问题预设表';
COMMENT ON COLUMN job_questions.id IS '问题ID（主键）';
COMMENT ON COLUMN job_questions.tenant_id IS '租户ID';
COMMENT ON COLUMN job_questions.user_id IS '创建问题的HR用户ID';
COMMENT ON COLUMN job_questions.job_id IS '关联职位ID';
COMMENT ON COLUMN job_questions.question IS '问题内容';
COMMENT ON COLUMN job_questions.question_type IS '问题类型: information-信息采集, assessment-考察评估';
COMMENT ON COLUMN job_questions.is_required IS '是否必须满足该要求';
COMMENT ON COLUMN job_questions.evaluation_criteria IS '判断标准（考察类问题使用）';
COMMENT ON COLUMN job_questions.sort_order IS '显示排序（越小越靠前）';
COMMENT ON COLUMN job_questions.status IS '状态: active-启用, deleted-已删除';
COMMENT ON COLUMN job_questions.created_at IS '创建时间';
COMMENT ON COLUMN job_questions.updated_at IS '更新时间';

-- ==============================================
-- 8.2. 候选人会话表
-- ==============================================

-- 候选人会话表
CREATE TABLE candidate_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    job_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'opened',
    stage VARCHAR(20) NOT NULL DEFAULT 'greeting',
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE candidate_conversations IS 'HR与候选人沟通会话主表';
COMMENT ON COLUMN candidate_conversations.id IS '会话ID（主键）';
COMMENT ON COLUMN candidate_conversations.tenant_id IS '租户ID';
COMMENT ON COLUMN candidate_conversations.user_id IS '负责该会话的HR用户ID';
COMMENT ON COLUMN candidate_conversations.resume_id IS '候选人简历ID';
COMMENT ON COLUMN candidate_conversations.job_id IS '关联职位ID';
COMMENT ON COLUMN candidate_conversations.status IS '会话状态: opened-会话开启, ongoing-沟通中, interrupted-中断, ended-会话结束, deleted-已删除';
COMMENT ON COLUMN candidate_conversations.stage IS '沟通阶段: greeting-开场白阶段, questioning-问题询问阶段, intention-职位意向询问阶段, matched-撮合成功';
COMMENT ON COLUMN candidate_conversations.summary IS '会话总结（AI生成）';
COMMENT ON COLUMN candidate_conversations.created_at IS '创建时间';
COMMENT ON COLUMN candidate_conversations.updated_at IS '更新时间';

-- ==============================================
-- 8.3. 会话问题跟踪表
-- ==============================================

-- 会话问题跟踪表
CREATE TABLE conversation_question_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    question_id UUID NOT NULL,
    job_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    question TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_satisfied BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE conversation_question_tracking IS '会话问题跟踪表';
COMMENT ON COLUMN conversation_question_tracking.id IS '跟踪记录ID（主键）';
COMMENT ON COLUMN conversation_question_tracking.tenant_id IS '租户ID';
COMMENT ON COLUMN conversation_question_tracking.user_id IS '执行问题的HR用户ID';
COMMENT ON COLUMN conversation_question_tracking.conversation_id IS '会话ID';
COMMENT ON COLUMN conversation_question_tracking.question_id IS '问题ID（关联job_questions表）';
COMMENT ON COLUMN conversation_question_tracking.job_id IS '职位ID（冗余字段，提高查询效率）';
COMMENT ON COLUMN conversation_question_tracking.resume_id IS '简历ID（冗余字段，提高查询效率）';
COMMENT ON COLUMN conversation_question_tracking.question IS '问题内容（冗余字段，提高查询效率）';
COMMENT ON COLUMN conversation_question_tracking.status IS '问题状态: pending-待处理, ongoing-进行中, completed-已完成, skipped-已跳过, deleted-已删除';
COMMENT ON COLUMN conversation_question_tracking.is_satisfied IS '是否满足要求（考察类问题）';
COMMENT ON COLUMN conversation_question_tracking.created_at IS '创建时间';
COMMENT ON COLUMN conversation_question_tracking.updated_at IS '更新时间';

-- ==============================================
-- 9. 系统日志表
-- ==============================================

-- 操作日志表
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE activity_logs IS '操作日志表';
COMMENT ON COLUMN activity_logs.id IS '日志ID（主键）';
COMMENT ON COLUMN activity_logs.tenant_id IS '租户ID（可为空，系统级操作）';
COMMENT ON COLUMN activity_logs.user_id IS '操作用户ID';
COMMENT ON COLUMN activity_logs.action IS '操作类型，如：create_job, update_resume';
COMMENT ON COLUMN activity_logs.entity_type IS '实体类型，如：job, resume, interview';
COMMENT ON COLUMN activity_logs.entity_id IS '实体ID';
COMMENT ON COLUMN activity_logs.details IS '详细信息（JSON格式）';
COMMENT ON COLUMN activity_logs.ip_address IS '操作IP地址';
COMMENT ON COLUMN activity_logs.user_agent IS '浏览器User-Agent';
COMMENT ON COLUMN activity_logs.created_at IS '操作时间';
COMMENT ON COLUMN activity_logs.updated_at IS '更新时间';
-- 邮件发送记录表
CREATE TABLE email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) ,
    content TEXT,
    template_name VARCHAR(100),
    status VARCHAR(20),
    error_message TEXT,
    resume_id UUID,
    sent_by UUID ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE email_logs IS '邮件发送记录表';
COMMENT ON COLUMN email_logs.id IS '邮件记录ID（主键）';
COMMENT ON COLUMN email_logs.tenant_id IS '租户ID';
COMMENT ON COLUMN email_logs.recipient_email IS '收件人邮箱';
COMMENT ON COLUMN email_logs.subject IS '邮件主题';
COMMENT ON COLUMN email_logs.content IS '邮件内容';
COMMENT ON COLUMN email_logs.template_name IS '使用的邮件模板名称';
COMMENT ON COLUMN email_logs.status IS '发送状态: pending-待发送, sent-已发送, failed-发送失败';
COMMENT ON COLUMN email_logs.error_message IS '错误信息（发送失败时）';
COMMENT ON COLUMN email_logs.resume_id IS '关联简历ID';
COMMENT ON COLUMN email_logs.sent_by IS '发送人用户ID';
COMMENT ON COLUMN email_logs.created_at IS '创建时间';
COMMENT ON COLUMN email_logs.sent_at IS '实际发送时间';
COMMENT ON COLUMN email_logs.updated_at IS '更新时间';
-- ==============================================
-- 10. 索引（精简版）
-- ==============================================

-- 租户表索引
CREATE INDEX idx_tenants_status ON tenants(status);

-- 用户表索引
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);

-- 用户设置表索引
CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);

-- 认证Token表索引
CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id);


-- 职位表索引
CREATE INDEX idx_jobs_tenant_status ON jobs(tenant_id, status);
CREATE INDEX idx_jobs_tenant_user ON jobs(tenant_id, user_id);
CREATE INDEX idx_jobs_title_search ON jobs USING gin(to_tsvector('simple', title));

-- LinkedIn/JobStreet 标准字段索引
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_category ON jobs(category);

-- 渠道表索引
CREATE INDEX idx_channels_tenant_status ON channels(tenant_id, status);
CREATE INDEX idx_channels_tenant_user ON channels(tenant_id, user_id);

-- 职位发布渠道表索引
CREATE INDEX idx_job_channels_job_id ON job_channels(job_id);
CREATE INDEX idx_job_channels_channel_id ON job_channels(channel_id);

-- 简历表索引
CREATE INDEX idx_resumes_tenant_status ON resumes(tenant_id, status);
CREATE INDEX idx_resumes_tenant_user ON resumes(tenant_id, user_id);
CREATE INDEX idx_resumes_job_id ON resumes(job_id);
CREATE INDEX idx_resumes_search ON resumes USING gin(
    to_tsvector('simple', candidate_name || ' ' || COALESCE(email, '') || ' ' || position)
);
CREATE INDEX idx_resumes_is_match ON resumes(is_match);

-- 工作经历表索引
CREATE INDEX idx_work_experiences_resume_id ON work_experiences(resume_id);

-- 项目经历表索引
CREATE INDEX idx_project_experiences_resume_id ON project_experiences(resume_id);

-- 教育经历表索引
CREATE INDEX idx_education_histories_resume_id ON education_histories(resume_id);

-- 求职意向表索引
CREATE INDEX idx_job_preferences_resume_id ON job_preferences(resume_id);

-- AI匹配结果索引
CREATE INDEX idx_ai_match_results_tenant_resume ON ai_match_results(tenant_id, resume_id);
CREATE INDEX idx_ai_match_results_tenant_job ON ai_match_results(tenant_id, job_id);

-- 招聘任务表索引
CREATE INDEX idx_recruitment_tasks_tenant_status ON recruitment_tasks(tenant_id, status);
CREATE INDEX idx_recruitment_tasks_tenant_user ON recruitment_tasks(tenant_id, user_id);
CREATE INDEX idx_recruitment_tasks_job_id ON recruitment_tasks(job_id);
CREATE INDEX idx_recruitment_tasks_created_at ON recruitment_tasks(created_at DESC);

-- 面试表索引
CREATE INDEX idx_interviews_tenant_status ON interviews(tenant_id, status);
CREATE INDEX idx_interviews_tenant_user ON interviews(tenant_id, user_id);
CREATE INDEX idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX idx_interviews_date_time ON interviews(interview_date, interview_time);

-- 聊天会话索引
CREATE INDEX idx_chat_sessions_tenant_user ON chat_sessions(tenant_id, user_id);

-- 聊天消息索引
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_metadata ON chat_messages USING gin(metadata);

-- 候选人聊天历史索引
CREATE INDEX idx_candidate_chat_history_resume_id ON candidate_chat_history(resume_id);

-- 职位问题预设表索引
CREATE INDEX idx_job_questions_tenant_job ON job_questions(tenant_id, job_id);

-- 候选人会话表索引
CREATE INDEX idx_candidate_conversations_tenant_user ON candidate_conversations(tenant_id, user_id);
CREATE INDEX idx_candidate_conversations_resume_job ON candidate_conversations(resume_id, job_id);

-- 会话问题跟踪表索引
CREATE INDEX idx_conversation_question_tracking_conversation ON conversation_question_tracking(conversation_id);
CREATE UNIQUE INDEX idx_conversation_question_unique ON conversation_question_tracking(conversation_id, question_id) WHERE status != 'deleted';

-- 活动日志索引
CREATE INDEX idx_activity_logs_tenant_user ON activity_logs(tenant_id, user_id);
CREATE INDEX idx_activity_logs_entity_type_id ON activity_logs(entity_type, entity_id);

-- 邮件日志索引
CREATE INDEX idx_email_logs_tenant_id ON email_logs(tenant_id);
CREATE INDEX idx_email_logs_status ON email_logs(status);
CREATE INDEX idx_email_logs_resume_id ON email_logs(resume_id);

-- ==============================================
-- 11. 初始化数据（示例）
-- ==============================================


-- 注意：实际使用时需要：
-- 1. 使用真实的租户信息
-- 2. 为管理员用户生成正确的密码哈希（使用bcrypt）
-- 3. 根据实际情况调整配置参数

-- ==============================================
-- 12. 数据示例和使用说明
-- ==============================================

-- 示例1：插入职位（包含要求、偏好学校数组和新字段）
-- INSERT INTO jobs (tenant_id, title, company, workplace_type, pay_type, pay_currency, category, requirements, preferred_schools) VALUES
-- ('tenant-uuid', '高级前端工程师', '腾讯科技', 'hybrid', 'monthly', 'CNY', 'IT-技术类',
--  '5年以上前端开发经验,精通React/Vue,有大型项目经验',
--  '清华大学,北京大学,浙江大学');

-- 示例2：插入简历（包含技能数组）
-- INSERT INTO resumes (tenant_id, candidate_name, skills) VALUES
-- ('tenant-uuid', '张伟',
--  'React,TypeScript,Node.js,Next.js');

-- 示例3：插入项目经历（包含技术栈数组）
-- INSERT INTO project_experiences (tenant_id, resume_id, project_name, technologies) VALUES
-- ('tenant-uuid', 'resume-uuid', '抖音创作者平台',
--  'React,TypeScript,Next.js,TailwindCSS');

-- 示例4：插入AI匹配结果（包含优势和劣势数组）
-- INSERT INTO ai_match_results (tenant_id, resume_id, job_id, strengths, weaknesses) VALUES
-- ('tenant-uuid', 'resume-uuid', 'job-uuid',
--  '6年前端开发经验,熟练掌握React/TypeScript,有大厂背景',
--  '缺少移动端开发经验');

-- 示例5：插入聊天消息（带工具调用metadata）
-- INSERT INTO chat_messages (tenant_id, session_id, role, content, message_type, metadata) VALUES
-- ('tenant-uuid', 'session-uuid', 'assistant', '正在搜索简历...', 'tool_call',
--  '{"tool_name": "search_resumes", "tool_args": {"keyword": "前端工程师"}}');

-- 示例6：插入职位问题预设
-- INSERT INTO job_questions (tenant_id, user_id, job_id, question, question_type, is_required, evaluation_criteria) VALUES
-- ('tenant-uuid', 'user-uuid', 'job-uuid', '您是否有React开发经验？', 'assessment', true, '必须具备2年以上React开发经验'),
-- ('tenant-uuid', 'user-uuid', 'job-uuid', '您的期望薪资范围是多少？', 'information', false, null);

-- 示例7：插入候选人会话
-- INSERT INTO candidate_conversations (tenant_id, user_id, resume_id, job_id, status, stage) VALUES
-- ('tenant-uuid', 'user-uuid', 'resume-uuid', 'job-uuid', 'ongoing', 'questioning');

-- 示例8：插入会话问题跟踪
-- INSERT INTO conversation_question_tracking (tenant_id, user_id, conversation_id, question_id, job_id, resume_id, question, status) VALUES
-- ('tenant-uuid', 'user-uuid', 'conversation-uuid', 'question-uuid', 'job-uuid', 'resume-uuid', '您是否有React开发经验？', 'ongoing');

-- 示例9：查询职位的所有要求
-- SELECT title, requirements FROM jobs WHERE id = 'job-uuid';

-- 示例10：查询简历的所有技能
-- SELECT candidate_name, skills FROM resumes WHERE id = 'resume-uuid';

-- 示例11：搜索包含特定技能的简历
-- SELECT * FROM resumes WHERE tenant_id = 'tenant-uuid' AND skills LIKE '%React%';

-- 示例12：搜索包含特定要求的职位
-- SELECT * FROM jobs WHERE tenant_id = 'tenant-uuid' AND requirements LIKE '%精通React%';
