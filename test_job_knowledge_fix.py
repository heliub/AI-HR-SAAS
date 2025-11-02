#!/usr/bin/env python3
"""
测试知识库修复是否有效
"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import init_db, async_session_maker
from app.services.job_knowledge_service import JobKnowledgeService
from app.schemas.job_knowledge import ScopeType

async def test_knowledge_operations():
    """测试知识库操作"""
    # 初始化数据库
    await init_db()
    
    # 创建数据库会话
    async with async_session_maker() as db:
        service = JobKnowledgeService(db)
        
        # 创建测试数据
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        scope_id = uuid.uuid4()
        
        print("创建知识库条目...")
        knowledge_data = {
            "scope_type": ScopeType.JOB.value,
            "scope_id": scope_id,
            "categories": ["tech_stack", "salary"],
            "question": "这个岗位的技术栈是什么？",
            "answer": "主要使用React、TypeScript、Node.js、PostgreSQL，薪资范围15k-25k。",
            "keywords": "React,TypeScript,技术栈,薪资"
        }
        
        # 创建知识库
        knowledge = await service.create_knowledge(
            data=knowledge_data,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        print(f"创建成功: {knowledge.id}")
        
        # 查询列表
        print("\n查询知识库列表...")
        items, total = await service.list_knowledge(
            tenant_id=tenant_id,
            scope_type=ScopeType.JOB.value,
            scope_id=scope_id,
            user_id=user_id,
            is_admin=False
        )
        
        print(f"查询结果: 总数={total}, 实际条目数={len(items)}")
        for item in items:
            print(f"- {item.question[:50]}...")
        
        # 按分类查询
        print("\n按分类查询...")
        items, total = await service.list_knowledge(
            tenant_id=tenant_id,
            category="tech_stack",
            user_id=user_id,
            is_admin=False
        )
        
        print(f"分类查询结果: 总数={total}, 实际条目数={len(items)}")
        for item in items:
            print(f"- {item.question[:50]}...")
        
        # 更新知识库
        print("\n更新知识库...")
        update_data = {
            "answer": "主要使用React、TypeScript、Node.js、PostgreSQL和Redis，薪资范围15k-25k。"
        }
        
        updated_knowledge = await service.update_knowledge(
            knowledge_id=knowledge.id,
            data=update_data,
            tenant_id=tenant_id,
            user_id=user_id,
            is_admin=False
        )
        
        print(f"更新成功: {updated_knowledge.answer[:50]}...")
        
        # 再次查询
        print("\n再次查询列表...")
        items, total = await service.list_knowledge(
            tenant_id=tenant_id,
            scope_type=ScopeType.JOB.value,
            scope_id=scope_id,
            user_id=user_id,
            is_admin=False
        )
        
        print(f"查询结果: 总数={total}, 实际条目数={len(items)}")
        for item in items:
            print(f"- {item.question[:50]}... -> {item.answer[:50]}...")
        
        # 删除知识库
        print("\n删除知识库...")
        success = await service.delete_knowledge(
            knowledge_id=knowledge.id,
            tenant_id=tenant_id,
            user_id=user_id,
            is_admin=False
        )
        
        print(f"删除成功: {success}")
        
        # 最后查询
        print("\n最后查询列表...")
        items, total = await service.list_knowledge(
            tenant_id=tenant_id,
            scope_type=ScopeType.JOB.value,
            scope_id=scope_id,
            user_id=user_id,
            is_admin=False
        )
        
        print(f"查询结果: 总数={total}, 实际条目数={len(items)}")
        
        # 提交事务
        await db.commit()
        print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(test_knowledge_operations())
