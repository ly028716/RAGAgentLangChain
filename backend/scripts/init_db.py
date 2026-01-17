#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表结构和初始配置
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.config import settings
from app.models import (
    user, conversation, message, knowledge_base, document,
    agent_tool, agent_execution, api_usage, user_quota, login_attempt
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        # Parse database URL to get connection info
        db_url = settings.DATABASE_URL
        if "mysql" in db_url:
            # Extract database name from URL
            parts = db_url.split("/")
            db_name = parts[-1].split("?")[0]
            base_url = "/".join(parts[:-1])
            
            # Connect without database name
            engine = create_engine(base_url + "/mysql")
            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
                )
                if not result.fetchone():
                    logger.info(f"Creating database: {db_name}")
                    conn.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                    conn.commit()
                    logger.info(f"Database {db_name} created successfully")
                else:
                    logger.info(f"Database {db_name} already exists")
            engine.dispose()
        else:
            logger.info("Non-MySQL database, skipping database creation")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


def init_database():
    """初始化数据库表结构"""
    try:
        logger.info("Starting database initialization...")
        
        # Create database if not exists
        create_database_if_not_exists()
        
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create session
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        try:
            # Verify tables were created
            with engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result]
                logger.info(f"Created tables: {', '.join(tables)}")
            
            logger.info("Database initialization completed successfully")
            
        finally:
            session.close()
            engine.dispose()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def verify_database():
    """验证数据库连接和表结构"""
    try:
        logger.info("Verifying database setup...")
        
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check connection
            conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
            
            # Check tables
            expected_tables = [
                'users', 'conversations', 'messages', 
                'knowledge_bases', 'documents',
                'agent_tools', 'agent_executions',
                'api_usage', 'user_quotas', 'login_attempts'
            ]
            
            result = conn.execute(text("SHOW TABLES"))
            existing_tables = [row[0] for row in result]
            
            for table in expected_tables:
                if table in existing_tables:
                    logger.info(f"✓ Table '{table}' exists")
                else:
                    logger.warning(f"✗ Table '{table}' not found")
            
            logger.info("Database verification completed")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"Error verifying database: {e}")
        raise


if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("Database Initialization Script")
        logger.info("=" * 60)
        
        # Initialize database
        init_database()
        
        # Verify setup
        verify_database()
        
        logger.info("=" * 60)
        logger.info("Database initialization completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
