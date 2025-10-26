# 范围类字段重构说明

## 变更概述

将原有的字符串形式的范围字段（如 `salary: "25K-40K"`, `ageRange: "25-35岁"`）重构为使用 min/max 两个独立的数值字段。

## 变更原因

### 原有设计的问题
1. **数据类型不准确**: 使用字符串存储数值范围
2. **查询困难**: 无法直接进行范围查询和数值比较
3. **需要解析**: 前端和后端都需要解析字符串才能使用
4. **统计困难**: 无法直接进行统计分析（如计算平均薪资）
5. **索引效率低**: 字符串字段的索引效率远低于数值字段

### 新设计的优势
1. **数据类型准确**: 使用 Integer 类型存储数值
2. **查询高效**: 支持直接的范围查询和比较操作
3. **无需解析**: 数值可以直接使用
4. **便于统计**: 可以直接进行数学运算和统计分析
5. **索引高效**: 数值字段的索引效率更高

## 字段变更对照表

| 原字段名 | 原类型 | 示例值 | 新字段名 | 新类型 | 示例值 |
|---------|--------|--------|---------|--------|--------|
| `salary` | String | "25K-40K" | `minSalary` + `maxSalary` | Integer | 25000 + 40000 |
| `ageRange` | String | "25-35岁" | `minAge` + `maxAge` | Integer | 25 + 35 |

## 前端 API 字段

```typescript
interface Job {
  // 薪资范围（单位：元/月）
  minSalary?: number  // 最低薪资
  maxSalary?: number  // 最高薪资
  
  // 年龄范围
  minAge?: number     // 最低年龄
  maxAge?: number     // 最高年龄
}
```

## 数据库字段

```sql
CREATE TABLE jobs (
    -- 薪资范围（单位：元/月）
    min_salary INTEGER,  -- 最低薪资
    max_salary INTEGER,  -- 最高薪资
    
    -- 年龄范围
    min_age INTEGER,     -- 最低年龄
    max_age INTEGER,     -- 最高年龄
    
    -- ... 其他字段
);
```

## API 示例

### 创建职位

**请求**:
```json
POST /api/v1/jobs

{
  "title": "高级前端工程师",
  "department": "技术部",
  "location": "北京",
  "type": "full-time",
  "minSalary": 25000,
  "maxSalary": 40000,
  "minAge": 25,
  "maxAge": 35,
  "education": "本科及以上",
  "jobLevel": "P6-P7"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "职位创建成功",
  "data": {
    "id": "uuid",
    "title": "高级前端工程师",
    "minSalary": 25000,
    "maxSalary": 40000,
    "minAge": 25,
    "maxAge": 35,
    "createdAt": "2025-01-26T10:00:00Z",
    "updatedAt": "2025-01-26T10:00:00Z"
  }
}
```

## 数据库查询示例

### 1. 查询薪资在指定范围内的职位

```sql
-- 查询薪资在 20K-30K 范围内的职位
SELECT * FROM jobs 
WHERE min_salary <= 30000 AND max_salary >= 20000;
```

### 2. 查询适合指定年龄的职位

```sql
-- 查询适合 28 岁候选人的职位
SELECT * FROM jobs 
WHERE (min_age IS NULL OR min_age <= 28) 
  AND (max_age IS NULL OR max_age >= 28);
```

### 3. 计算平均薪资

```sql
-- 查询平均薪资超过 35K 的职位
SELECT 
    id, 
    title,
    (min_salary + max_salary) / 2 AS avg_salary
FROM jobs 
WHERE (min_salary + max_salary) / 2 > 35000;
```

### 4. 薪资排序

```sql
-- 按最低薪资排序
SELECT * FROM jobs 
ORDER BY min_salary DESC;

-- 按平均薪资排序
SELECT * FROM jobs 
ORDER BY (min_salary + max_salary) / 2 DESC;
```

### 5. 统计分析

```sql
-- 统计各部门的平均薪资
SELECT 
    department,
    AVG((min_salary + max_salary) / 2) AS avg_salary,
    MIN(min_salary) AS lowest_salary,
    MAX(max_salary) AS highest_salary
FROM jobs
GROUP BY department;
```

## 前端展示建议

虽然数据库使用独立的 min/max 字段存储，但前端展示时可以格式化为用户友好的形式：

```typescript
// 格式化薪资显示
function formatSalary(minSalary?: number, maxSalary?: number): string {
  if (!minSalary && !maxSalary) return '面议';
  if (!maxSalary) return `${minSalary / 1000}K起`;
  if (!minSalary) return `${maxSalary / 1000}K封顶`;
  return `${minSalary / 1000}K-${maxSalary / 1000}K`;
}

// 格式化年龄显示
function formatAge(minAge?: number, maxAge?: number): string {
  if (!minAge && !maxAge) return '年龄不限';
  if (!maxAge) return `${minAge}岁以上`;
  if (!minAge) return `${maxAge}岁以下`;
  return `${minAge}-${maxAge}岁`;
}

// 使用示例
const job = {
  minSalary: 25000,
  maxSalary: 40000,
  minAge: 25,
  maxAge: 35
};

console.log(formatSalary(job.minSalary, job.maxSalary)); // "25K-40K"
console.log(formatAge(job.minAge, job.maxAge));           // "25-35岁"
```

## 数据迁移

对于已有数据，需要创建迁移脚本将字符串格式转换为数值格式：

```sql
-- 示例：将 "25K-40K" 转换为 min_salary=25000, max_salary=40000
-- 实际迁移脚本需要根据具体数据格式编写

UPDATE jobs 
SET 
    min_salary = 25000,
    max_salary = 40000
WHERE salary = '25K-40K';
```

## 兼容性说明

### 向后兼容

为了保持向后兼容，可以在 Schema 中添加计算属性：

```python
class JobResponse(JobBase, IDSchema, TimestampSchema):
    """职位响应"""
    status: str
    applicants: int = 0
    
    @property
    def salary(self) -> str:
        """为了兼容旧版本，提供 salary 属性"""
        if not self.min_salary and not self.max_salary:
            return "面议"
        if not self.max_salary:
            return f"{self.min_salary // 1000}K起"
        if not self.min_salary:
            return f"{self.max_salary // 1000}K封顶"
        return f"{self.min_salary // 1000}K-{self.max_salary // 1000}K"
    
    @property
    def age_range(self) -> str:
        """为了兼容旧版本，提供 ageRange 属性"""
        if not self.min_age and not self.max_age:
            return "年龄不限"
        if not self.max_age:
            return f"{self.min_age}岁以上"
        if not self.min_age:
            return f"{self.max_age}岁以下"
        return f"{self.min_age}-{self.max_age}岁"
```

## 已更新的文件

### 后端文件
- ✅ `app/models/job.py` - 数据库模型
- ✅ `app/schemas/job.py` - API Schema
- ✅ `app/services/job_service.py` - 业务逻辑
- ✅ `app/api/v1/jobs.py` - API 接口
- ✅ `migrations/versions/001_initial_schema.py` - 数据库迁移
- ✅ `tests/conftest.py` - 测试 Fixture
- ✅ `scripts/import_mock_data.sql` - Mock 数据脚本

### 文档文件
- ✅ `docs/DATABASE_SCHEMA.sql` - 数据库 Schema 文档
- ✅ `docs/FIELD_MAPPING.md` - 字段映射文档
- ✅ `docs/mock-data.ts` - 前端 Mock 数据

## 测试建议

### 单元测试
```python
def test_job_salary_range():
    """测试薪资范围字段"""
    job = Job(
        title="测试职位",
        min_salary=20000,
        max_salary=30000
    )
    assert job.min_salary == 20000
    assert job.max_salary == 30000

def test_job_age_range():
    """测试年龄范围字段"""
    job = Job(
        title="测试职位",
        min_age=25,
        max_age=35
    )
    assert job.min_age == 25
    assert job.max_age == 35
```

### 集成测试
```python
async def test_create_job_with_ranges(client, auth_headers):
    """测试创建包含范围字段的职位"""
    response = await client.post(
        "/api/v1/jobs",
        json={
            "title": "测试职位",
            "department": "技术部",
            "location": "北京",
            "type": "full-time",
            "minSalary": 25000,
            "maxSalary": 40000,
            "minAge": 25,
            "maxAge": 35
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["minSalary"] == 25000
    assert data["maxSalary"] == 40000
    assert data["minAge"] == 25
    assert data["maxAge"] == 35
```

## 总结

这次重构将范围类字段从字符串格式改为数值格式，使得：
1. 数据类型更准确
2. 查询效率更高
3. 统计分析更方便
4. 代码更易维护

这是一个更合理、更规范的数据库设计。

