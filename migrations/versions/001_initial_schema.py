"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建租户表
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('company_name', sa.String(200)),
        sa.Column('contact_name', sa.String(100)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('plan_type', sa.String(50), server_default='basic'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('max_users', sa.Integer, server_default='10'),
        sa.Column('max_jobs', sa.Integer, server_default='50'),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_tenants_status', 'tenants', ['status'])
    
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='hr'),
        sa.Column('avatar_url', sa.Text),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_tenant_email', 'users', ['tenant_id', 'email'])
    
    # 创建用户设置表
    op.create_table(
        'user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('language', sa.String(10), server_default='zh'),
        sa.Column('email_notifications', sa.Boolean, server_default='true'),
        sa.Column('task_reminders', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'])
    
    # 创建职位表
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('department', sa.String(100), nullable=False),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('min_salary', sa.Integer),
        sa.Column('max_salary', sa.Integer),
        sa.Column('description', sa.Text),
        sa.Column('requirements', postgresql.ARRAY(sa.Text)),
        sa.Column('preferred_schools', postgresql.ARRAY(sa.Text)),
        sa.Column('recruitment_invitation', sa.Text),
        sa.Column('min_age', sa.Integer),
        sa.Column('max_age', sa.Integer),
        sa.Column('gender', sa.String(20)),
        sa.Column('education', sa.String(100)),
        sa.Column('job_level', sa.String(50)),
        sa.Column('applicants_count', sa.Integer, server_default='0'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_jobs_tenant_id', 'jobs', ['tenant_id'])
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    
    # 创建渠道表
    op.create_table(
        'channels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('applicants_count', sa.Integer, server_default='0'),
        sa.Column('annual_cost', sa.Numeric(10, 2)),
        sa.Column('cost_currency', sa.String(10), server_default='CNY'),
        sa.Column('api_key', sa.Text),
        sa.Column('contact_person', sa.String(100)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('last_sync_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_channels_tenant_id', 'channels', ['tenant_id'])
    
    # 创建简历表
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('candidate_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('position', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('source', sa.String(100)),
        sa.Column('source_channel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('channels.id')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id')),
        sa.Column('experience_years', sa.String(20)),
        sa.Column('education_level', sa.String(50)),
        sa.Column('age', sa.Integer),
        sa.Column('gender', sa.String(20)),
        sa.Column('location', sa.String(100)),
        sa.Column('school', sa.String(200)),
        sa.Column('major', sa.String(200)),
        sa.Column('skills', postgresql.ARRAY(sa.Text)),
        sa.Column('resume_url', sa.Text),
        sa.Column('conversation_summary', sa.Text),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_resumes_tenant_id', 'resumes', ['tenant_id'])
    op.create_index('idx_resumes_status', 'resumes', ['status'])
    
    # 插入示例租户数据
    op.execute("""
        INSERT INTO tenants (name, company_name, contact_email, plan_type, status, max_users, max_jobs)
        VALUES ('演示公司', 'Demo Company Ltd.', 'demo@example.com', 'pro', 'active', 50, 100)
    """)
    
    print("数据库初始化完成！")


def downgrade() -> None:
    op.drop_table('resumes')
    op.drop_table('channels')
    op.drop_table('jobs')
    op.drop_table('user_settings')
    op.drop_table('users')
    op.drop_table('tenants')

