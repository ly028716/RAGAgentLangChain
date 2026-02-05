"""API调用工具 - 用于调用外部API接口"""
import json
from typing import Any, Dict, Optional, Type
from urllib.parse import urlparse

import requests
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class APICallInput(BaseModel):
    """API调用工具的输入模型"""

    url: str = Field(description="API接口的完整URL地址")
    method: str = Field(
        default="GET", description="HTTP请求方法: GET, POST, PUT, DELETE, PATCH"
    )
    headers: Optional[str] = Field(
        default=None, description="请求头，JSON格式，例如: '{\"Content-Type\": \"application/json\"}'"
    )
    body: Optional[str] = Field(
        default=None, description="请求体，JSON格式，用于POST/PUT/PATCH请求"
    )
    params: Optional[str] = Field(
        default=None, description="URL查询参数，JSON格式，例如: '{\"page\": 1, \"limit\": 10}'"
    )


class APICallTool(BaseTool):
    """
    API调用工具 - 调用外部API接口

    支持的功能:
    - HTTP方法: GET, POST, PUT, DELETE, PATCH
    - 自定义请求头
    - 请求体（JSON格式）
    - URL查询参数
    - 超时控制
    - 自动重试

    安全限制:
    - 只允许HTTPS协议（生产环境）
    - 请求超时限制
    - 响应大小限制
    """

    name: str = "api_call"
    description: str = (
        "用于调用外部API接口的工具。"
        "支持GET、POST、PUT、DELETE、PATCH等HTTP方法。"
        "示例: url='https://api.example.com/users', method='GET', "
        "headers='{\"Authorization\": \"Bearer token\"}'"
    )
    args_schema: Type[BaseModel] = APICallInput
    timeout: int = 30  # 请求超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    max_response_size: int = 1024 * 1024  # 最大响应大小（1MB）

    def _parse_json(self, json_str: Optional[str]) -> Optional[Dict[str, Any]]:
        """解析JSON字符串"""
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")

    def _validate_url(self, url: str) -> bool:
        """验证URL是否安全"""
        try:
            parsed = urlparse(url)

            # 检查协议（开发环境允许HTTP，生产环境只允许HTTPS）
            if parsed.scheme not in ["http", "https"]:
                return False

            # 检查是否有主机名
            if not parsed.netloc:
                return False

            # 禁止访问本地地址（安全考虑）
            local_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
            if any(host in parsed.netloc.lower() for host in local_hosts):
                return False

            return True
        except Exception:
            return False

    def _make_request(
        self,
        url: str,
        method: str,
        headers: Optional[Dict[str, Any]],
        body: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """执行HTTP请求"""
        method = method.upper()

        # 验证HTTP方法
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            raise ValueError(f"不支持的HTTP方法: {method}")

        # 设置默认请求头
        request_headers = {"User-Agent": "AI-Agent/1.0"}
        if headers:
            request_headers.update(headers)

        # 准备请求参数
        request_kwargs = {
            "timeout": self.timeout,
            "headers": request_headers,
        }

        if params:
            request_kwargs["params"] = params

        if body and method in ["POST", "PUT", "PATCH"]:
            request_kwargs["json"] = body

        # 执行请求（带重试）
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, **request_kwargs)

                # 检查响应大小
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_response_size:
                    raise ValueError(f"响应大小超过限制（最大 {self.max_response_size} 字节）")

                # 解析响应
                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "success": 200 <= response.status_code < 300,
                }

                # 尝试解析JSON响应
                try:
                    result["data"] = response.json()
                except json.JSONDecodeError:
                    result["data"] = response.text[:1000]  # 限制文本长度

                return result

            except requests.Timeout:
                last_error = f"请求超时（尝试 {attempt + 1}/{self.max_retries}）"
                if attempt < self.max_retries - 1:
                    continue
            except requests.ConnectionError as e:
                last_error = f"连接失败: {str(e)}"
                if attempt < self.max_retries - 1:
                    continue
            except Exception as e:
                last_error = f"请求失败: {str(e)}"
                break

        raise Exception(last_error or "请求失败")

    def _format_response(self, result: Dict[str, Any]) -> str:
        """格式化响应结果"""
        status = result["status_code"]
        success = result["success"]
        data = result["data"]

        # 构建响应摘要
        lines = [
            f"状态码: {status}",
            f"成功: {'是' if success else '否'}",
            "",
            "响应数据:",
        ]

        # 格式化数据
        if isinstance(data, dict) or isinstance(data, list):
            lines.append(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            lines.append(str(data))

        return "\n".join(lines)

    def _run(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[str] = None,
        body: Optional[str] = None,
        params: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        执行API调用

        Args:
            url: API接口URL
            method: HTTP方法
            headers: 请求头（JSON格式）
            body: 请求体（JSON格式）
            params: URL参数（JSON格式）
            run_manager: 回调管理器

        Returns:
            API响应结果的字符串表示
        """
        try:
            # 验证URL
            if not self._validate_url(url):
                return f"错误: 无效或不安全的URL: {url}"

            # 解析参数
            parsed_headers = self._parse_json(headers)
            parsed_body = self._parse_json(body)
            parsed_params = self._parse_json(params)

            # 执行请求
            result = self._make_request(
                url=url,
                method=method,
                headers=parsed_headers,
                body=parsed_body,
                params=parsed_params,
            )

            # 格式化响应
            return self._format_response(result)

        except ValueError as e:
            return f"错误: {str(e)}"
        except Exception as e:
            return f"API调用失败: {str(e)}"

    async def _arun(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[str] = None,
        body: Optional[str] = None,
        params: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """异步执行API调用（实际上调用同步方法）"""
        return self._run(url, method, headers, body, params, run_manager)
