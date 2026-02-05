"""
API调用工具测试
"""
import pytest
import json
from unittest.mock import Mock, patch
import requests

from app.langchain_integration.tools.api_call_tool import APICallTool


@pytest.fixture
def api_tool():
    """创建API调用工具实例"""
    return APICallTool()


class TestAPICallTool:
    """API调用工具测试类"""

    def test_tool_initialization(self, api_tool):
        """测试工具初始化"""
        assert api_tool.name == "api_call"
        assert api_tool.timeout == 30
        assert api_tool.max_retries == 3
        assert "API接口" in api_tool.description

    @patch('requests.request')
    def test_get_request_success(self, mock_request, api_tool):
        """测试GET请求成功"""
        # Mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"message": "success"}
        mock_request.return_value = mock_response

        result = api_tool._run(
            url="https://api.example.com/users",
            method="GET"
        )

        assert "状态码: 200" in result
        assert "成功: 是" in result
        assert "success" in result

    @patch('requests.request')
    def test_post_request_with_body(self, mock_request, api_tool):
        """测试POST请求带请求体"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {}
        mock_response.json.return_value = {"id": 1, "created": True}
        mock_request.return_value = mock_response

        result = api_tool._run(
            url="https://api.example.com/users",
            method="POST",
            body=json.dumps({"name": "test"})
        )

        assert "状态码: 201" in result
        assert "成功: 是" in result

    def test_invalid_url(self, api_tool):
        """测试无效URL"""
        result = api_tool._run(
            url="not-a-url",
            method="GET"
        )

        assert "错误" in result
        assert "无效或不安全的URL" in result

    def test_localhost_blocked(self, api_tool):
        """测试禁止访问localhost"""
        result = api_tool._run(
            url="http://localhost:8000/api",
            method="GET"
        )

        assert "错误" in result
        assert "无效或不安全的URL" in result

    def test_127_0_0_1_blocked(self, api_tool):
        """测试禁止访问127.0.0.1"""
        result = api_tool._run(
            url="http://127.0.0.1:8000/api",
            method="GET"
        )

        assert "错误" in result

    def test_invalid_http_method(self, api_tool):
        """测试无效的HTTP方法"""
        with patch('requests.request') as mock_request:
            result = api_tool._run(
                url="https://api.example.com/users",
                method="INVALID"
            )

            assert "错误" in result
            assert "不支持的HTTP方法" in result

    @patch('requests.request')
    def test_request_timeout(self, mock_request, api_tool):
        """测试请求超时"""
        mock_request.side_effect = requests.Timeout("Connection timeout")

        result = api_tool._run(
            url="https://api.example.com/slow",
            method="GET"
        )

        assert "API调用失败" in result
        assert "请求超时" in result

    @patch('requests.request')
    def test_connection_error(self, mock_request, api_tool):
        """测试连接错误"""
        mock_request.side_effect = requests.ConnectionError("Connection refused")

        result = api_tool._run(
            url="https://api.example.com/down",
            method="GET"
        )

        assert "API调用失败" in result

    @patch('requests.request')
    def test_retry_mechanism(self, mock_request, api_tool):
        """测试重试机制"""
        # 前两次失败，第三次成功
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"success": True}

        mock_request.side_effect = [
            requests.Timeout("timeout"),
            requests.Timeout("timeout"),
            mock_response
        ]

        result = api_tool._run(
            url="https://api.example.com/retry",
            method="GET"
        )

        assert "状态码: 200" in result
        assert mock_request.call_count == 3

    @patch('requests.request')
    def test_non_json_response(self, mock_request, api_tool):
        """测试非JSON响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)
        mock_response.text = "HTML content here"
        mock_request.return_value = mock_response

        result = api_tool._run(
            url="https://example.com",
            method="GET"
        )

        assert "状态码: 200" in result
        assert "HTML content" in result

    @patch('requests.request')
    def test_response_size_limit(self, mock_request, api_tool):
        """测试响应大小限制"""
        mock_response = Mock()
        mock_response.headers = {"Content-Length": str(2 * 1024 * 1024)}  # 2MB
        mock_request.return_value = mock_response

        result = api_tool._run(
            url="https://api.example.com/large",
            method="GET"
        )

        assert "错误" in result or "API调用失败" in result

    def test_invalid_json_headers(self, api_tool):
        """测试无效的JSON请求头"""
        result = api_tool._run(
            url="https://api.example.com/users",
            method="GET",
            headers="invalid json"
        )

        assert "错误" in result
        assert "JSON解析失败" in result

    @patch('requests.request')
    def test_custom_headers(self, mock_request, api_tool):
        """测试自定义请求头"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        result = api_tool._run(
            url="https://api.example.com/users",
            method="GET",
            headers=json.dumps({"Authorization": "Bearer token123"})
        )

        assert "状态码: 200" in result
        # 验证请求头被正确传递
        call_kwargs = mock_request.call_args[1]
        assert "Authorization" in call_kwargs["headers"]

    @patch('requests.request')
    def test_query_params(self, mock_request, api_tool):
        """测试URL查询参数"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"results": []}
        mock_request.return_value = mock_response

        result = api_tool._run(
            url="https://api.example.com/search",
            method="GET",
            params=json.dumps({"q": "test", "limit": 10})
        )

        assert "状态码: 200" in result
        call_kwargs = mock_request.call_args[1]
        assert "params" in call_kwargs

    @pytest.mark.asyncio
    async def test_async_run(self, api_tool):
        """测试异步执行"""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.json.return_value = {"success": True}
            mock_request.return_value = mock_response

            result = await api_tool._arun(
                url="https://api.example.com/test",
                method="GET"
            )

            assert "状态码: 200" in result
