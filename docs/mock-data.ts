export interface Job {
  id: string
  title: string
  department: string
  location: string
  type: "full-time" | "part-time" | "contract"
  status: "open" | "closed" | "draft"
  minSalary?: number // 最低薪资（元/月）
  maxSalary?: number // 最高薪资（元/月）
  description: string
  requirements: string[]
  createdAt: string
  applicants: number
  // New fields
  minAge?: number // 最低年龄
  maxAge?: number // 最高年龄
  gender?: "male" | "female" | "unlimited"
  education?: string
  preferredSchools?: string[]
  jobLevel?: string
  recruitmentInvitation?: string
  publishedChannels?: string[]
}

export interface Resume {
  id: string
  candidateName: string
  email: string
  phone: string
  position: string
  status: "pending" | "reviewing" | "interview" | "offered" | "rejected"
  source: string
  submittedAt: string
  experience: string
  education: string
  skills: string[]
  resumeUrl?: string
  // New fields
  age?: number
  gender?: "male" | "female"
  location?: string
  school?: string
  major?: string
  workHistory?: WorkExperience[]
  projectHistory?: ProjectExperience[]
  educationHistory?: EducationHistory[]
  jobPreferences?: JobPreferences
  // AI matching results
  aiMatch?: {
    isMatch: boolean
    score: number // 0-100
    reason: string
    strengths?: string[]
    weaknesses?: string[]
    recommendation?: string
  }
  // AI chat history
  aiChatHistory?: {
    sender: "ai" | "candidate"
    message: string
    timestamp: string
  }[]
  conversationSummary?: string
}

export interface WorkExperience {
  company: string
  position: string
  startDate: string
  endDate: string
  description: string
}

export interface ProjectExperience {
  name: string
  role: string
  startDate: string
  endDate: string
  description: string
  technologies: string[]
}

export interface EducationHistory {
  school: string
  degree: string
  major: string
  startDate: string
  endDate: string
}

export interface JobPreferences {
  expectedSalary: string
  preferredLocations: string[]
  jobType: string
  availableDate: string
}

export interface Channel {
  id: string
  name: string
  type: "job-board" | "social-media" | "referral" | "agency" | "website"
  status: "active" | "inactive"
  applicants: number
  cost: string
  lastSync: string
  // New fields
  apiKey?: string
  contactPerson?: string
  contactEmail?: string
  description?: string
}

export interface Task {
  id: string
  jobId: string
  jobTitle: string
  status: "not-started" | "in-progress" | "paused" | "completed"
  createdAt: string
  createdBy: string
  // Progress metrics
  channelsPublished: number
  totalChannels: number
  resumesViewed: number
  greetingsSent: number
  conversationsActive: number
  resumesRequested: number
  resumesReceived: number
  interviewsScheduled: number
}

export interface Interview {
  id: string
  candidateId: string
  candidateName: string
  position: string
  date: string
  time: string
  interviewer: string
  interviewerTitle?: string
  type: "phone" | "video" | "onsite"
  status: "scheduled" | "completed" | "cancelled" | "rescheduled"
  location?: string
  meetingLink?: string
  notes?: string
}

export interface ChatSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messages: ChatMessage[]
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export const mockJobs: Job[] = [
  {
    id: "1",
    title: "高级前端工程师",
    department: "技术部",
    location: "北京",
    type: "full-time",
    status: "open",
    minSalary: 25000,
    maxSalary: 40000,
    description: "负责公司核心产品的前端开发工作",
    requirements: ["5年以上前端开发经验", "精通React/Vue", "有大型项目经验"],
    createdAt: "2025-01-05",
    applicants: 23,
    minAge: 25,
    maxAge: 35,
    gender: "unlimited",
    education: "本科及以上",
    preferredSchools: ["清华大学", "北京大学", "浙江大学", "上海交通大学"],
    jobLevel: "P6-P7",
    recruitmentInvitation: "我们正在寻找有激情的前端工程师加入我们的团队，共同打造下一代产品。",
    publishedChannels: ["1", "3"],
  },
  {
    id: "2",
    title: "HR经理",
    department: "人力资源部",
    location: "上海",
    type: "full-time",
    status: "open",
    minSalary: 20000,
    maxSalary: 30000,
    description: "负责公司招聘和人力资源管理工作",
    requirements: ["3年以上HR管理经验", "熟悉招聘流程", "良好的沟通能力"],
    createdAt: "2025-01-08",
    applicants: 15,
    minAge: 28,
    maxAge: 40,
    gender: "unlimited",
    education: "本科及以上",
    preferredSchools: [],
    jobLevel: "M1",
    recruitmentInvitation: "加入我们，帮助公司吸引和培养最优秀的人才。",
    publishedChannels: ["2"],
  },
  {
    id: "3",
    title: "产品经理",
    department: "产品部",
    location: "深圳",
    type: "full-time",
    status: "open",
    minSalary: 30000,
    maxSalary: 50000,
    description: "负责产品规划和需求管理",
    requirements: ["5年以上产品经验", "B端产品经验优先", "数据驱动思维"],
    createdAt: "2025-01-10",
    applicants: 31,
    minAge: 28,
    maxAge: 38,
    gender: "unlimited",
    education: "本科及以上",
    preferredSchools: ["复旦大学", "中山大学"],
    jobLevel: "P7-P8",
    recruitmentInvitation: "寻找有远见的产品经理，一起定义产品的未来。",
    publishedChannels: ["1", "2", "3"],
  },
]

export const mockResumes: Resume[] = [
  {
    id: "1",
    candidateName: "张伟",
    email: "zhangwei@example.com",
    phone: "13800138000",
    position: "高级前端工程师",
    status: "pending",
    source: "智联招聘",
    submittedAt: "2025-01-13 10:30",
    experience: "6年",
    education: "本科",
    skills: ["React", "TypeScript", "Node.js", "Next.js"],
    age: 29,
    gender: "male",
    location: "北京",
    school: "北京大学",
    major: "计算机科学与技术",
    aiMatch: {
      isMatch: true,
      score: 92,
      reason: "候选人具备丰富的前端开发经验，技术栈完全匹配，有大厂背景，项目经验丰富。",
      strengths: ["6年前端开发经验", "熟练掌握React/TypeScript", "有字节跳动等大厂经验", "项目架构能力强"],
      weaknesses: ["缺少移动端开发经验"],
      recommendation: "强烈推荐面试，技术能力和项目经验都很符合要求"
    },
    workHistory: [
      {
        company: "字节跳动",
        position: "高级前端工程师",
        startDate: "2021-03",
        endDate: "至今",
        description: "负责抖音Web端核心功能开发，优化页面性能，提升用户体验。",
      },
      {
        company: "美团",
        position: "前端工程师",
        startDate: "2019-07",
        endDate: "2021-02",
        description: "参与外卖平台前端开发，实现多个重要功能模块。",
      },
    ],
    projectHistory: [
      {
        name: "抖音创作者平台",
        role: "前端负责人",
        startDate: "2022-06",
        endDate: "2024-12",
        description: "从0到1搭建创作者平台，支持百万级创作者使用。",
        technologies: ["React", "TypeScript", "Next.js", "TailwindCSS"],
      },
    ],
    educationHistory: [
      {
        school: "北京大学",
        degree: "本科",
        major: "计算机科学与技术",
        startDate: "2015-09",
        endDate: "2019-06",
      },
    ],
    jobPreferences: {
      expectedSalary: "35K-45K",
      preferredLocations: ["北京", "上海"],
      jobType: "全职",
      availableDate: "2025-02-01",
    },
    aiChatHistory: [
      {
        sender: "ai",
        message: "您好，张伟！我是贵公司的AI招聘助手。我们看到您投递了高级前端工程师的职位，您的简历非常出色！能否简单介绍一下您在字节跳动的主要工作内容？",
        timestamp: "2025-01-13 10:35"
      },
      {
        sender: "candidate",
        message: "您好！我在字节跳动主要负责抖音创作者平台的前端开发，从0到1搭建了整个平台，目前支持百万级创作者使用。主要技术栈是React + TypeScript + Next.js。",
        timestamp: "2025-01-13 10:42"
      },
      {
        sender: "ai",
        message: "非常棒的经历！我注意到您的项目中大量使用了TypeScript和Next.js，这正是我们目前技术栈的核心。能详细说说您在性能优化方面的经验吗？",
        timestamp: "2025-01-13 10:43"
      },
      {
        sender: "candidate",
        message: "在性能优化方面，我做过很多工作：1) 使用React.memo和useMemo减少不必要的重渲染；2) 实现虚拟滚动处理大列表；3) 使用代码分割和懒加载优化首屏加载；4) 通过SSR提升SEO和首屏性能。这些优化让页面加载时间从3s降到了1s以内。",
        timestamp: "2025-01-13 10:48"
      },
      {
        sender: "ai",
        message: "太棒了！您的经验完全符合我们的需求。关于薪资期望，您提到35K-45K，我们的预算范围是25K-40K，不过考虑到您的优秀背景，我们可以争取更高的package。您最快什么时候可以到岗？",
        timestamp: "2025-01-13 10:50"
      },
      {
        sender: "candidate",
        message: "我的离职交接需要一个月，预计2月1日可以到岗。关于薪资，我比较看重公司的发展空间和技术氛围，如果项目有挑战性，薪资可以适当调整。",
        timestamp: "2025-01-13 10:55"
      },
      {
        sender: "ai",
        message: "非常感谢您的理解！我们公司目前正在做一个创新性的产品，技术挑战性很高，团队氛围也很好。我会安排我们的技术总监与您进行面试，预计本周内会有HR联系您确定具体时间。",
        timestamp: "2025-01-13 10:58"
      }
    ],
    conversationSummary: "候选人张伟在字节跳动有丰富的前端开发经验，主导开发了抖音创作者平台，技术栈完全匹配（React/TypeScript/Next.js）。在性能优化方面有深入实践，成功将页面加载时间从3s优化到1s以内。薪资期望35K-45K，但表示可以根据项目挑战性调整。预计2月1日可到岗。候选人对技术挑战和团队氛围较为看重，态度积极，沟通顺畅，强烈推荐安排技术面试。"
  },
  {
    id: "2",
    candidateName: "李娜",
    email: "lina@example.com",
    phone: "13900139000",
    position: "HR经理",
    status: "interview",
    source: "猎聘",
    submittedAt: "2025-01-12 14:20",
    experience: "4年",
    education: "硕士",
    skills: ["招聘管理", "绩效考核", "员工关系"],
    age: 32,
    gender: "female",
    location: "上海",
    school: "复旦大学",
    major: "人力资源管理",
    aiMatch: {
      isMatch: true,
      score: 88,
      reason: "具备丰富的HR管理经验，专业背景匹配，有大厂招聘经验，能力全面。",
      strengths: ["4年HR管理经验", "专业对口", "有阿里巴巴招聘经验", "年均招聘50+人才"],
      weaknesses: ["缺少跨国公司经验"],
      recommendation: "推荐面试，HR专业能力强，招聘经验丰富"
    },
    workHistory: [
      {
        company: "阿里巴巴",
        position: "招聘经理",
        startDate: "2021-01",
        endDate: "至今",
        description: "负责技术团队招聘，年均招聘50+人才。",
      },
    ],
    educationHistory: [
      {
        school: "复旦大学",
        degree: "硕士",
        major: "人力资源管理",
        startDate: "2018-09",
        endDate: "2021-06",
      },
    ],
    jobPreferences: {
      expectedSalary: "25K-35K",
      preferredLocations: ["上海"],
      jobType: "全职",
      availableDate: "2025-03-01",
    },
    aiChatHistory: [
      {
        sender: "ai",
        message: "李娜您好！感谢您投递我们HR经理的职位。看到您在阿里巴巴有4年的招聘经验，能分享一下您最自豪的招聘成果吗？",
        timestamp: "2025-01-12 14:25"
      },
      {
        sender: "candidate",
        message: "您好！我最自豪的是去年为技术团队招聘了50多位优秀人才，其中包括5位P8级别的技术专家。我建立了一套完整的技术人才评估体系，大大提高了招聘效率和质量。",
        timestamp: "2025-01-12 14:30"
      },
      {
        sender: "ai",
        message: "这个成绩非常亮眼！您能详细说说这套技术人才评估体系是如何运作的吗？",
        timestamp: "2025-01-12 14:32"
      },
      {
        sender: "candidate",
        message: "这套体系主要包括三个维度：1) 技术能力评估（编程能力、系统设计、技术深度）；2) 软实力评估（沟通能力、团队协作、学习能力）；3) 文化匹配度。我们还引入了AI辅助筛选，大大提高了初筛效率。",
        timestamp: "2025-01-12 14:38"
      },
      {
        sender: "ai",
        message: "您对AI在招聘中的应用很有见解！这正是我们看重的。您目前的团队规模有多大？管理经验如何？",
        timestamp: "2025-01-12 14:40"
      },
      {
        sender: "candidate",
        message: "我目前管理一个6人的招聘团队，负责技术和产品线的招聘。我比较注重团队赋能，会定期组织培训和分享会，团队的招聘效率在过去一年提升了40%。",
        timestamp: "2025-01-12 14:45"
      }
    ],
    conversationSummary: "候选人李娜在阿里巴巴有4年招聘经验，去年成功招聘50+技术人才，包括5位P8专家。她建立了完整的技术人才评估体系，并引入AI辅助筛选提高效率。目前管理6人招聘团队，团队效率提升40%。对AI在招聘中的应用有深入理解和实践。薪资期望25K-35K，3月1日可到岗。候选人管理经验丰富，注重团队赋能，推荐安排面试。"
  },
  {
    id: "3",
    candidateName: "王强",
    email: "wangqiang@example.com",
    phone: "13700137000",
    position: "产品经理",
    status: "reviewing",
    source: "BOSS直聘",
    submittedAt: "2025-01-13 09:15",
    experience: "7年",
    education: "本科",
    skills: ["产品规划", "需求分析", "Axure", "SQL"],
    age: 33,
    gender: "male",
    location: "深圳",
    school: "中山大学",
    major: "软件工程",
    aiMatch: {
      isMatch: false,
      score: 45,
      reason: "虽然有丰富的产品经验，但技术背景不够强，缺少前端开发经验，与高级前端工程师职位不匹配。",
      strengths: ["7年产品管理经验", "有腾讯大厂背景", "逻辑思维能力强"],
      weaknesses: ["缺少前端开发经验", "技术栈不匹配", "职业方向偏差较大"],
      recommendation: "不建议面试此职位，建议关注产品经理相关职位"
    },
    workHistory: [
      {
        company: "腾讯",
        position: "高级产品经理",
        startDate: "2020-05",
        endDate: "至今",
        description: "负责企业微信核心功能规划和迭代。",
      },
    ],
    educationHistory: [
      {
        school: "中山大学",
        degree: "本科",
        major: "软件工程",
        startDate: "2012-09",
        endDate: "2016-06",
      },
    ],
    jobPreferences: {
      expectedSalary: "40K-55K",
      preferredLocations: ["深圳", "广州"],
      jobType: "全职",
      availableDate: "2025-02-15",
    },
  },
  {
    id: "4",
    candidateName: "刘芳",
    email: "liufang@example.com",
    phone: "13600136000",
    position: "高级前端工程师",
    status: "pending",
    source: "拉勾网",
    submittedAt: "2025-01-13 11:45",
    experience: "5年",
    education: "本科",
    skills: ["Vue", "React", "Webpack", "CSS"],
    age: 28,
    gender: "female",
    location: "杭州",
    school: "浙江大学",
    major: "软件工程",
    workHistory: [
      {
        company: "网易",
        position: "前端工程师",
        startDate: "2020-07",
        endDate: "至今",
        description: "负责网易云音乐Web端开发。",
      },
    ],
    educationHistory: [
      {
        school: "浙江大学",
        degree: "本科",
        major: "软件工程",
        startDate: "2016-09",
        endDate: "2020-06",
      },
    ],
    jobPreferences: {
      expectedSalary: "30K-40K",
      preferredLocations: ["杭州", "上海"],
      jobType: "全职",
      availableDate: "2025-01-20",
    },
  },
]

export const mockChannels: Channel[] = [
  {
    id: "1",
    name: "智联招聘",
    type: "job-board",
    status: "active",
    applicants: 156,
    cost: "¥50,000/年",
    lastSync: "2025-01-13 12:00",
    contactPerson: "张经理",
    contactEmail: "zhang@zhaopin.com",
    description: "国内领先的招聘平台，覆盖各行业人才。",
  },
  {
    id: "2",
    name: "猎聘",
    type: "job-board",
    status: "active",
    applicants: 89,
    cost: "¥80,000/年",
    lastSync: "2025-01-13 11:30",
    contactPerson: "李总监",
    contactEmail: "li@liepin.com",
    description: "专注中高端人才招聘。",
  },
  {
    id: "3",
    name: "BOSS直聘",
    type: "job-board",
    status: "active",
    applicants: 203,
    cost: "¥60,000/年",
    lastSync: "2025-01-13 12:15",
    contactPerson: "王主管",
    contactEmail: "wang@zhipin.com",
    description: "直接与求职者沟通的招聘平台。",
  },
  {
    id: "4",
    name: "LinkedIn",
    type: "social-media",
    status: "active",
    applicants: 45,
    cost: "¥30,000/年",
    lastSync: "2025-01-13 10:00",
    contactPerson: "Sarah Chen",
    contactEmail: "sarah@linkedin.com",
    description: "全球职业社交平台。",
  },
  {
    id: "5",
    name: "内部推荐",
    type: "referral",
    status: "active",
    applicants: 67,
    cost: "¥0",
    lastSync: "2025-01-13 12:30",
    description: "员工内部推荐渠道。",
  },
]

export const mockTasks: Task[] = [
  {
    id: "1",
    jobId: "1",
    jobTitle: "高级前端工程师",
    status: "in-progress",
    createdAt: "2025-01-10 09:00",
    createdBy: "AI助手",
    channelsPublished: 2,
    totalChannels: 3,
    resumesViewed: 45,
    greetingsSent: 23,
    conversationsActive: 12,
    resumesRequested: 15,
    resumesReceived: 8,
    interviewsScheduled: 3,
  },
  {
    id: "2",
    jobId: "2",
    jobTitle: "HR经理",
    status: "in-progress",
    createdAt: "2025-01-11 10:30",
    createdBy: "AI助手",
    channelsPublished: 1,
    totalChannels: 2,
    resumesViewed: 28,
    greetingsSent: 15,
    conversationsActive: 8,
    resumesRequested: 10,
    resumesReceived: 6,
    interviewsScheduled: 2,
  },
  {
    id: "3",
    jobId: "3",
    jobTitle: "产品经理",
    status: "completed",
    createdAt: "2025-01-08 14:00",
    createdBy: "AI助手",
    channelsPublished: 3,
    totalChannels: 3,
    resumesViewed: 67,
    greetingsSent: 31,
    conversationsActive: 5,
    resumesRequested: 20,
    resumesReceived: 15,
    interviewsScheduled: 5,
  },
]

export const mockInterviews: Interview[] = [
  {
    id: "1",
    candidateId: "2",
    candidateName: "李娜",
    position: "HR经理",
    date: "2025-01-15",
    time: "14:00",
    interviewer: "王总监",
    interviewerTitle: "人力资源总监",
    type: "video",
    status: "scheduled",
    meetingLink: "https://meet.example.com/abc123",
    notes: "重点考察招聘管理经验和团队协作能力",
  },
  {
    id: "2",
    candidateId: "3",
    candidateName: "王强",
    position: "产品经理",
    date: "2025-01-14",
    time: "10:00",
    interviewer: "张经理",
    interviewerTitle: "产品总监",
    type: "onsite",
    status: "scheduled",
    location: "深圳市南山区科技园",
    notes: "准备产品案例分析题目",
  },
  {
    id: "3",
    candidateId: "1",
    candidateName: "张伟",
    position: "高级前端工程师",
    date: "2025-01-16",
    time: "15:30",
    interviewer: "李技术总监",
    interviewerTitle: "技术总监",
    type: "video",
    status: "scheduled",
    meetingLink: "https://meet.example.com/xyz789",
    notes: "技术面试，重点考察React和性能优化",
  },
]

export const mockChatSessions: ChatSession[] = [
  {
    id: "1",
    title: "招聘咨询 - 前端工程师",
    createdAt: "2025-01-13 09:00",
    updatedAt: "2025-01-13 15:30",
    messages: [
      {
        id: "1",
        role: "assistant",
        content: "你好！我是AI招聘助手，很高兴为您服务。我可以帮助您筛选简历、安排面试、分析招聘数据等。请问需要什么帮助？",
        timestamp: new Date("2025-01-13T09:00:00"),
      },
      {
        id: "2",
        role: "user",
        content: "帮我筛选一下前端工程师的简历",
        timestamp: new Date("2025-01-13T09:01:00"),
      },
      {
        id: "3",
        role: "assistant",
        content: "我已经为你筛选了最近的简历。发现3份高质量简历匹配高级前端工程师职位，其中张伟的简历匹配度最高（92分），有6年经验和字节跳动背景。李明的简历也不错（85分），有阿里巴巴经验。建议优先面试这两位候选人。",
        timestamp: new Date("2025-01-13T09:02:00"),
      },
      {
        id: "4",
        role: "user",
        content: "张伟的技术栈怎么样？",
        timestamp: new Date("2025-01-13T15:25:00"),
      },
      {
        id: "5",
        role: "assistant",
        content: "张伟的技术栈非常匹配我们的需求：\n\n✅ 前端框架：React、Vue.js\n✅ 开发语言：TypeScript、JavaScript\n✅ 构建工具：Webpack、Vite\n✅ 后端技能：Node.js、Express\n✅ 数据库：MySQL、MongoDB\n\n他在字节跳动负责抖音Web端核心功能开发，有大型项目架构经验。建议安排技术面试。",
        timestamp: new Date("2025-01-13T15:30:00"),
      },
    ],
  },
  {
    id: "2",
    title: "面试安排 - HR经理",
    createdAt: "2025-01-12 14:00",
    updatedAt: "2025-01-12 16:45",
    messages: [
      {
        id: "1",
        role: "user",
        content: "帮我安排李娜的面试",
        timestamp: new Date("2025-01-12T14:00:00"),
      },
      {
        id: "2",
        role: "assistant",
        content: "好的，我来帮您安排李娜（HR经理职位）的面试。根据她的简历，她有4年HR经验，目前在阿里巴巴担任招聘经理。建议安排以下面试流程：\n\n1. 初面：HR部门负责人（30分钟）\n2. 专业面试：业务部门经理（45分钟）\n3. 终面：VP或总监级别（30分钟）\n\n您希望什么时候开始安排？",
        timestamp: new Date("2025-01-12T14:01:00"),
      },
      {
        id: "3",
        role: "user",
        content: "明天下午可以吗？",
        timestamp: new Date("2025-01-12T16:40:00"),
      },
      {
        id: "4",
        role: "assistant",
        content: "明天下午的时间安排如下：\n\n📅 1月13日（明天）\n🕐 14:00-14:30 初面（HR王总监）\n🕐 14:45-15:30 专业面试（业务部门张经理）\n🕐 15:45-16:15 终面（VP李总）\n\n面试地点：公司会议室A\n已发送面试邀请邮件给候选人，请确认是否需要调整。",
        timestamp: new Date("2025-01-12T16:45:00"),
      },
    ],
  },
  {
    id: "3",
    title: "数据分析 - 招聘效果",
    createdAt: "2025-01-11 10:00",
    updatedAt: "2025-01-11 11:30",
    messages: [
      {
        id: "1",
        role: "user",
        content: "分析一下这个月的招聘数据",
        timestamp: new Date("2025-01-11T10:00:00"),
      },
      {
        id: "2",
        role: "assistant",
        content: "📊 本月招聘数据分析（截至1月11日）：\n\n📈 **整体数据**\n• 收到简历：156份（↑23% vs上月）\n• 安排面试：45场（↑15% vs上月）\n• 发出offer：12个（↑8% vs上月）\n• 入职确认：8人（↑33% vs上月）\n\n🎯 **转化率**\n• 简历→面试：28.8%（行业平均25%）\n• 面试→offer：26.7%（行业平均20%）\n• offer→入职：66.7%（行业平均70%）\n\n💡 **建议**：offer接受率略低，建议优化薪酬包装和候选人体验。",
        timestamp: new Date("2025-01-11T10:05:00"),
      },
      {
        id: "3",
        role: "user",
        content: "哪个渠道效果最好？",
        timestamp: new Date("2025-01-11T11:25:00"),
      },
      {
        id: "4",
        role: "assistant",
        content: "🏆 **招聘渠道效果排名**：\n\n1. **BOSS直聘** - 42份简历，转化率32%\n2. **智联招聘** - 38份简历，转化率28%\n3. **猎聘网** - 31份简历，转化率25%\n4. **拉勾网** - 28份简历，转化率22%\n5. **内推** - 17份简历，转化率65%（质量最高）\n\n💰 **成本效益**：内推成本最低且质量最高，建议加大内推激励力度。BOSS直聘虽然量大但成本适中，可以作为主要渠道。",
        timestamp: new Date("2025-01-11T11:30:00"),
      },
    ],
  },
]
