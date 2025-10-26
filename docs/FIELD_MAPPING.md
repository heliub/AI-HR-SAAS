# 字段映射说明

本文档说明前端API接口字段（驼峰命名）与数据库字段（下划线命名）的映射关系。

## 命名规范

- **前端API接口**: 使用驼峰命名（camelCase）
- **数据库字段**: 使用下划线命名（snake_case）
- **Python模型**: 使用下划线命名（snake_case）

## Job 职位表字段映射

| 前端API字段 (camelCase) | 数据库字段 (snake_case) | 类型 | 说明 |
|------------------------|------------------------|------|------|
| `id` | `id` | UUID | 职位ID |
| `title` | `title` | String | 职位标题 |
| `department` | `department` | String | 所属部门 |
| `location` | `location` | String | 工作地点 |
| `type` | `type` | String | 职位类型 |
| `status` | `status` | String | 职位状态 |
| `minSalary` | `min_salary` | Integer | 最低薪资（元/月） |
| `maxSalary` | `max_salary` | Integer | 最高薪资（元/月） |
| `description` | `description` | Text | 职位描述 |
| `requirements` | `requirements` | Array | 职位要求列表 |
| `minAge` | `min_age` | Integer | 最低年龄要求 |
| `maxAge` | `max_age` | Integer | 最高年龄要求 |
| `gender` | `gender` | String | 性别要求 |
| `education` | `education` | String | 学历要求 |
| `preferredSchools` | `preferred_schools` | Array | 偏好学校列表 |
| `jobLevel` | `job_level` | String | 职级要求 |
| `recruitmentInvitation` | `recruitment_invitation` | Text | 招聘邀请语 |
| `applicants` | `applicants_count` | Integer | 申请人数 |
| `createdAt` | `created_at` | DateTime | 创建时间 |
| `updatedAt` | `updated_at` | DateTime | 更新时间 |
| `publishedAt` | `published_at` | DateTime | 发布时间 |
| `closedAt` | `closed_at` | DateTime | 关闭时间 |
| `publishedChannels` | - | Array | 发布渠道（关联表） |

### 范围类字段设计

对于范围类数据，采用 min/max 两个独立字段的设计：

- **薪资范围**: `minSalary` (25000) + `maxSalary` (40000) 代替 `salary: "25K-40K"`
- **年龄范围**: `minAge` (25) + `maxAge` (35) 代替 `ageRange: "25-35岁"`

**优势：**
1. 数值类型存储，支持范围查询和比较
2. 便于统计分析（如计算平均薪资）
3. 避免字符串解析的复杂性
4. 数据库索引更高效

## 实现方式

使用 Pydantic 的字段别名功能实现自动转换：

```python
from pydantic import BaseModel, Field, ConfigDict

class JobBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    # 薪资范围：使用 min/max 两个字段
    min_salary: Optional[int] = Field(
        None,
        validation_alias="minSalary",      # 接收前端的驼峰命名
        serialization_alias="minSalary",   # 返回给前端时用驼峰命名
        description="最低薪资（元/月）"
    )
    max_salary: Optional[int] = Field(
        None,
        validation_alias="maxSalary",
        serialization_alias="maxSalary",
        description="最高薪资（元/月）"
    )
    
    # 年龄范围：使用 min/max 两个字段
    min_age: Optional[int] = Field(
        None,
        validation_alias="minAge",
        serialization_alias="minAge",
        description="最低年龄"
    )
    max_age: Optional[int] = Field(
        None,
        validation_alias="maxAge",
        serialization_alias="maxAge",
        description="最高年龄"
    )
    
    # 其他字段
    preferred_schools: Optional[List[str]] = Field(
        None,
        validation_alias="preferredSchools",
        serialization_alias="preferredSchools"
    )
    job_level: Optional[str] = Field(
        None,
        validation_alias="jobLevel",
        serialization_alias="jobLevel"
    )
    recruitment_invitation: Optional[str] = Field(
        None,
        validation_alias="recruitmentInvitation",
        serialization_alias="recruitmentInvitation"
    )
```

## 注意事项

1. **前端请求**: 可以使用驼峰命名（如 `ageRange`）或下划线命名（如 `age_range`），因为设置了 `populate_by_name=True`
2. **前端响应**: 统一返回驼峰命名（如 `ageRange`），通过 `serialization_alias` 实现
3. **数据库操作**: 始终使用下划线命名（如 `age_range`）
4. **SQL迁移**: 数据库表结构使用下划线命名

## 示例

### 创建职位请求

```json
{
  "title": "高级前端工程师",
  "department": "技术部",
  "location": "北京",
  "type": "full-time",
  "minSalary": 25000,
  "maxSalary": 40000,
  "minAge": 25,
  "maxAge": 35,
  "preferredSchools": ["清华大学", "北京大学"],
  "jobLevel": "P6-P7",
  "recruitmentInvitation": "我们正在寻找有激情的前端工程师..."
}
```

### 职位响应

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "uuid",
    "title": "高级前端工程师",
    "department": "技术部",
    "location": "北京",
    "type": "full-time",
    "minSalary": 25000,
    "maxSalary": 40000,
    "minAge": 25,
    "maxAge": 35,
    "preferredSchools": ["清华大学", "北京大学"],
    "jobLevel": "P6-P7",
    "recruitmentInvitation": "我们正在寻找有激情的前端工程师...",
    "createdAt": "2025-01-26T10:00:00Z",
    "updatedAt": "2025-01-26T10:00:00Z"
  }
}
```

### 数据库存储

```sql
INSERT INTO jobs (
    title, department, location, type, 
    min_salary, max_salary, min_age, max_age,
    preferred_schools, job_level, recruitment_invitation
) VALUES (
    '高级前端工程师', '技术部', '北京', 'full-time',
    25000, 40000, 25, 35,
    ARRAY['清华大学', '北京大学'], 'P6-P7', '我们正在寻找有激情的前端工程师...'
);
```

### 范围查询示例

使用 min/max 设计的优势 - 支持高效的范围查询：

```sql
-- 查询薪资在 20K-30K 范围内的职位
SELECT * FROM jobs 
WHERE min_salary <= 30000 AND max_salary >= 20000;

-- 查询适合 28 岁候选人的职位
SELECT * FROM jobs 
WHERE (min_age IS NULL OR min_age <= 28) 
  AND (max_age IS NULL OR max_age >= 28);

-- 查询平均薪资超过 35K 的职位
SELECT * FROM jobs 
WHERE (min_salary + max_salary) / 2 > 35000;
```

