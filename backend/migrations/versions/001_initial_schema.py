"""初始数据库架构

创建所有基础表结构，包括：
- users: 用户表
- conversations: 对话表
- messages: 消息表
- knowledge_bases: 知识库表
- documents: 文档表
- agent_tools: Agent工具表
- agent_executions: Agent执行记录表
- user_quotas: 用户配额表
- api_usage: API使用记录表
- login_attempts: 登录尝试记录表

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-08

需求引用:
- 需求1.1: 用户认证与授权
- 需求2.1, 2.2: 智能对话管理
- 需求3.1, 3.2: 知识库文档管理
- 需求5.2, 6.2: Agent工具和执行
- 需求8.1: 使用统计
- 需求11.1: 用户配额管理
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库到此版本 - 创建所有表"""
    
    # 1. 创建users表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('username', sa.String(50), nullable=False, comment='用户名'),
        sa.Column('email', sa.String(100), nullable=True, comment='邮箱地址'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='密码哈希值'),
        sa.Column('avatar', sa.String(255), nullable=True, comment='头像URL'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('last_login', sa.DateTime(), nullable=True, comment='最后登录时间'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='是否激活'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户表'
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # 2. 创建conversations表
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False, comment='对话ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('title', sa.String(200), nullable=False, default='新对话', comment='对话标题'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False, comment='是否已删除（软删除）'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='对话表'
    )
    op.create_index('ix_conversations_id', 'conversations', ['id'], unique=False)
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'], unique=False)
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'], unique=False)
    op.create_index('idx_user_created', 'conversations', ['user_id', 'created_at'], unique=False)
    
    # 3. 创建messages表
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False, comment='消息ID'),
        sa.Column('conversation_id', sa.Integer(), nullable=False, comment='对话ID'),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='messagerole'), nullable=False, comment='消息角色'),
        sa.Column('content', sa.Text(), nullable=False, comment='消息内容'),
        sa.Column('tokens', sa.Integer(), nullable=False, default=0, comment='消耗的token数量'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='消息表'
    )
    op.create_index('ix_messages_id', 'messages', ['id'], unique=False)
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'], unique=False)
    op.create_index('ix_messages_created_at', 'messages', ['created_at'], unique=False)
    op.create_index('idx_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)
    
    # 4. 创建knowledge_bases表
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.Integer(), nullable=False, comment='知识库ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='知识库名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='知识库描述'),
        sa.Column('category', sa.String(50), nullable=True, comment='知识库分类'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='知识库表'
    )
    op.create_index('ix_knowledge_bases_id', 'knowledge_bases', ['id'], unique=False)
    op.create_index('ix_knowledge_bases_user_id', 'knowledge_bases', ['user_id'], unique=False)
    op.create_index('ix_knowledge_bases_created_at', 'knowledge_bases', ['created_at'], unique=False)
    op.create_index('idx_kb_user_created', 'knowledge_bases', ['user_id', 'created_at'], unique=False)
    
    # 5. 创建documents表
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False, comment='文档ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='知识库ID'),
        sa.Column('filename', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='文件存储路径'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='文件大小（字节）'),
        sa.Column('file_type', sa.String(50), nullable=False, comment='文件类型'),
        sa.Column('status', sa.Enum('processing', 'completed', 'failed', name='documentstatus'), nullable=False, default='processing', comment='处理状态'),
        sa.Column('chunk_count', sa.Integer(), nullable=False, default=0, comment='分块数量'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='文档表'
    )
    op.create_index('ix_documents_id', 'documents', ['id'], unique=False)
    op.create_index('ix_documents_knowledge_base_id', 'documents', ['knowledge_base_id'], unique=False)
    op.create_index('ix_documents_status', 'documents', ['status'], unique=False)
    op.create_index('ix_documents_created_at', 'documents', ['created_at'], unique=False)
    op.create_index('idx_doc_kb_created', 'documents', ['knowledge_base_id', 'created_at'], unique=False)
    op.create_index('idx_doc_kb_status', 'documents', ['knowledge_base_id', 'status'], unique=False)

    
    # 6. 创建agent_tools表
    op.create_table(
        'agent_tools',
        sa.Column('id', sa.Integer(), nullable=False, comment='工具ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='工具名称'),
        sa.Column('description', sa.Text(), nullable=False, comment='工具描述'),
        sa.Column('tool_type', sa.Enum('builtin', 'custom', name='tooltype'), nullable=False, default='builtin', comment='工具类型（builtin/custom）'),
        sa.Column('config', sa.JSON(), nullable=True, comment='工具配置参数'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True, comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='Agent工具表'
    )
    op.create_index('ix_agent_tools_id', 'agent_tools', ['id'], unique=False)
    op.create_index('ix_agent_tools_name', 'agent_tools', ['name'], unique=True)
    
    # 7. 创建agent_executions表
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.Integer(), nullable=False, comment='执行记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('task', sa.Text(), nullable=False, comment='任务描述'),
        sa.Column('steps', sa.JSON(), nullable=True, comment='执行步骤记录'),
        sa.Column('result', sa.Text(), nullable=True, comment='执行结果'),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='executionstatus'), nullable=False, default='pending', comment='执行状态'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Agent执行记录表'
    )
    op.create_index('ix_agent_executions_id', 'agent_executions', ['id'], unique=False)
    op.create_index('ix_agent_executions_user_id', 'agent_executions', ['user_id'], unique=False)
    op.create_index('ix_agent_executions_created_at', 'agent_executions', ['created_at'], unique=False)
    op.create_index('idx_agent_exec_user_created', 'agent_executions', ['user_id', 'created_at'], unique=False)
    
    # 8. 创建user_quotas表
    op.create_table(
        'user_quotas',
        sa.Column('id', sa.Integer(), nullable=False, comment='配额记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('monthly_quota', sa.Integer(), nullable=False, default=100000, comment='月度配额上限（tokens）'),
        sa.Column('used_quota', sa.Integer(), nullable=False, default=0, comment='当月已使用配额（tokens）'),
        sa.Column('reset_date', sa.Date(), nullable=False, comment='配额重置日期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户配额表'
    )
    op.create_index('ix_user_quotas_id', 'user_quotas', ['id'], unique=False)
    op.create_index('ix_user_quotas_user_id', 'user_quotas', ['user_id'], unique=True)
    op.create_index('idx_quota_reset_date', 'user_quotas', ['reset_date'], unique=False)
    
    # 9. 创建api_usage表
    op.create_table(
        'api_usage',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('api_type', sa.String(50), nullable=False, comment='API类型（chat/rag/agent等）'),
        sa.Column('tokens_used', sa.Integer(), nullable=False, comment='消耗的token数量'),
        sa.Column('cost', sa.Numeric(10, 4), nullable=False, default=0, comment='调用费用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='调用时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='API使用记录表'
    )
    op.create_index('ix_api_usage_id', 'api_usage', ['id'], unique=False)
    op.create_index('ix_api_usage_user_id', 'api_usage', ['user_id'], unique=False)
    op.create_index('ix_api_usage_api_type', 'api_usage', ['api_type'], unique=False)
    op.create_index('ix_api_usage_created_at', 'api_usage', ['created_at'], unique=False)
    op.create_index('idx_usage_user_created', 'api_usage', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_usage_user_api_type', 'api_usage', ['user_id', 'api_type'], unique=False)
    op.create_index('idx_usage_api_type_created', 'api_usage', ['api_type', 'created_at'], unique=False)
    
    # 10. 创建login_attempts表
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('username', sa.String(50), nullable=False, comment='尝试登录的用户名'),
        sa.Column('ip_address', sa.String(45), nullable=False, comment='登录请求IP地址（支持IPv6）'),
        sa.Column('success', sa.Boolean(), nullable=False, comment='登录是否成功'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='尝试时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='登录尝试记录表'
    )
    op.create_index('ix_login_attempts_id', 'login_attempts', ['id'], unique=False)
    op.create_index('ix_login_attempts_username', 'login_attempts', ['username'], unique=False)
    op.create_index('ix_login_attempts_created_at', 'login_attempts', ['created_at'], unique=False)
    op.create_index('idx_login_username_created', 'login_attempts', ['username', 'created_at'], unique=False)
    op.create_index('idx_login_username_success', 'login_attempts', ['username', 'success'], unique=False)
    op.create_index('idx_login_ip_created', 'login_attempts', ['ip_address', 'created_at'], unique=False)


def downgrade() -> None:
    """降级数据库到上一版本 - 删除所有表"""
    
    # 按照依赖关系的逆序删除表
    # 先删除有外键依赖的表
    
    # 删除login_attempts表
    op.drop_index('idx_login_ip_created', table_name='login_attempts')
    op.drop_index('idx_login_username_success', table_name='login_attempts')
    op.drop_index('idx_login_username_created', table_name='login_attempts')
    op.drop_index('ix_login_attempts_created_at', table_name='login_attempts')
    op.drop_index('ix_login_attempts_username', table_name='login_attempts')
    op.drop_index('ix_login_attempts_id', table_name='login_attempts')
    op.drop_table('login_attempts')
    
    # 删除api_usage表
    op.drop_index('idx_usage_api_type_created', table_name='api_usage')
    op.drop_index('idx_usage_user_api_type', table_name='api_usage')
    op.drop_index('idx_usage_user_created', table_name='api_usage')
    op.drop_index('ix_api_usage_created_at', table_name='api_usage')
    op.drop_index('ix_api_usage_api_type', table_name='api_usage')
    op.drop_index('ix_api_usage_user_id', table_name='api_usage')
    op.drop_index('ix_api_usage_id', table_name='api_usage')
    op.drop_table('api_usage')
    
    # 删除user_quotas表
    op.drop_index('idx_quota_reset_date', table_name='user_quotas')
    op.drop_index('ix_user_quotas_user_id', table_name='user_quotas')
    op.drop_index('ix_user_quotas_id', table_name='user_quotas')
    op.drop_table('user_quotas')
    
    # 删除agent_executions表
    op.drop_index('idx_agent_exec_user_created', table_name='agent_executions')
    op.drop_index('ix_agent_executions_created_at', table_name='agent_executions')
    op.drop_index('ix_agent_executions_user_id', table_name='agent_executions')
    op.drop_index('ix_agent_executions_id', table_name='agent_executions')
    op.drop_table('agent_executions')
    
    # 删除agent_tools表
    op.drop_index('ix_agent_tools_name', table_name='agent_tools')
    op.drop_index('ix_agent_tools_id', table_name='agent_tools')
    op.drop_table('agent_tools')
    
    # 删除documents表
    op.drop_index('idx_doc_kb_status', table_name='documents')
    op.drop_index('idx_doc_kb_created', table_name='documents')
    op.drop_index('ix_documents_created_at', table_name='documents')
    op.drop_index('ix_documents_status', table_name='documents')
    op.drop_index('ix_documents_knowledge_base_id', table_name='documents')
    op.drop_index('ix_documents_id', table_name='documents')
    op.drop_table('documents')
    
    # 删除knowledge_bases表
    op.drop_index('idx_kb_user_created', table_name='knowledge_bases')
    op.drop_index('ix_knowledge_bases_created_at', table_name='knowledge_bases')
    op.drop_index('ix_knowledge_bases_user_id', table_name='knowledge_bases')
    op.drop_index('ix_knowledge_bases_id', table_name='knowledge_bases')
    op.drop_table('knowledge_bases')
    
    # 删除messages表
    op.drop_index('idx_conversation_created', table_name='messages')
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_index('ix_messages_id', table_name='messages')
    op.drop_table('messages')
    
    # 删除conversations表
    op.drop_index('idx_user_created', table_name='conversations')
    op.drop_index('ix_conversations_created_at', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    op.drop_index('ix_conversations_id', table_name='conversations')
    op.drop_table('conversations')
    
    # 删除users表
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
    
    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS tooltype")
    op.execute("DROP TYPE IF EXISTS executionstatus")
