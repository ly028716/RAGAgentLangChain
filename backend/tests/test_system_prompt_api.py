"""
系统提示词API测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.system_prompt import SystemPrompt


class TestSystemPromptAPI:
    """系统提示词API测试类"""
    
    def test_get_prompts_list(self, client: TestClient, auth_headers: dict):
        """测试获取提示词列表"""
        response = client.get("/api/v1/prompts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_create_prompt(self, client: TestClient, auth_headers: dict):
        """测试创建提示词"""
        prompt_data = {
            "name": "测试提示词",
            "content": "这是一个测试提示词内容",
            "category": "general"
        }
        response = client.post("/api/v1/prompts", json=prompt_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == prompt_data["name"]
        assert data["content"] == prompt_data["content"]
        assert data["is_system"] == False
    
    def test_get_prompt_by_id(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        """测试获取提示词详情"""
        # 先创建一个提示词
        prompt = SystemPrompt(
            user_id=test_user.id,
            name="测试提示词",
            content="测试内容",
            category="general",
            is_system=False
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        response = client.get(f"/api/v1/prompts/{prompt.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == prompt.id
        assert data["name"] == prompt.name
    
    def test_update_prompt(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        """测试更新提示词"""
        # 先创建一个提示词
        prompt = SystemPrompt(
            user_id=test_user.id,
            name="原始名称",
            content="原始内容",
            category="general",
            is_system=False
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        update_data = {"name": "更新后的名称"}
        response = client.put(f"/api/v1/prompts/{prompt.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
    
    def test_delete_prompt(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        """测试删除提示词"""
        # 先创建一个提示词
        prompt = SystemPrompt(
            user_id=test_user.id,
            name="待删除提示词",
            content="待删除内容",
            category="general",
            is_system=False
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        response = client.delete(f"/api/v1/prompts/{prompt.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 验证已删除
        deleted = db.query(SystemPrompt).filter(SystemPrompt.id == prompt.id).first()
        assert deleted is None
    
    def test_cannot_delete_system_prompt(self, client: TestClient, auth_headers: dict, db: Session):
        """测试不能删除系统提示词"""
        # 创建系统提示词
        prompt = SystemPrompt(
            user_id=None,
            name="系统提示词",
            content="系统内容",
            category="general",
            is_system=True
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        response = client.delete(f"/api/v1/prompts/{prompt.id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_set_default_prompt(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        """测试设置默认提示词"""
        # 先创建一个提示词
        prompt = SystemPrompt(
            user_id=test_user.id,
            name="测试提示词",
            content="测试内容",
            category="general",
            is_system=False,
            is_default=False
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        response = client.put(f"/api/v1/prompts/{prompt.id}/default", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_get_prompts_with_category_filter(self, client: TestClient, auth_headers: dict):
        """测试按分类筛选提示词"""
        response = client.get("/api/v1/prompts?category=general", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "general"
