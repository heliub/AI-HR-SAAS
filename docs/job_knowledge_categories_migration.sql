-- 知识库表categories字段类型变更迁移脚本
-- 将categories字段从ARRAY(String(50))修改为VARCHAR(2000)
-- 日期: 2025-11-02

-- 1. 添加新的VARCHAR(2000)字段
ALTER TABLE job_knowledge_base 
ADD COLUMN categories_new VARCHAR(2000);

-- 2. 将ARRAY数据转换为逗号分隔的字符串
UPDATE job_knowledge_base 
SET categories_new = ARRAY_TO_STRING(categories, ',')
WHERE categories IS NOT NULL;

-- 3. 删除旧的ARRAY字段
ALTER TABLE job_knowledge_base 
DROP COLUMN categories;

-- 4. 重命名新字段为categories
ALTER TABLE job_knowledge_base 
RENAME COLUMN categories_new TO categories;

-- 5. 添加字段注释
COMMENT ON COLUMN job_knowledge_base.categories IS '分类标签，逗号分隔的字符串，如：salary,benefits,culture';

-- 6. 更新索引（如果需要）
-- 删除原有的数组索引（如果存在）
DROP INDEX IF EXISTS idx_knowledge_categories;

-- 创建新的文本索引（如果需要）
CREATE INDEX IF NOT EXISTS idx_knowledge_categories_text 
ON job_knowledge_base USING gin(to_tsvector('simple', COALESCE(categories, '')));

-- 7. 验证数据迁移
SELECT 
    id, 
    question,
    categories,
    LENGTH(categories) as categories_length
FROM job_knowledge_base 
WHERE categories IS NOT NULL AND categories != ''
LIMIT 10;
