"""搜索工具 - 用于网络搜索"""
import json
from typing import Optional, Type

import httpx
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    """搜索工具的输入模型"""

    query: str = Field(description="要搜索的关键词或问题")
    max_results: int = Field(default=5, ge=1, le=10, description="返回的最大结果数量")


class SearchTool(BaseTool):
    """
    网络搜索工具 - 执行网络搜索并返回结果

    支持的功能:
    - 关键词搜索
    - 返回搜索结果摘要
    - 可配置返回结果数量

    注意: 这是一个简化的实现，实际生产环境中应该集成真实的搜索API
    如百度搜索API、Google Custom Search API等
    """

    name: str = "search"
    description: str = (
        "用于在互联网上搜索信息的工具。"
        "输入应该是一个搜索查询字符串，例如: '人工智能的最新发展', 'Python编程教程'。"
        "工具会返回相关的搜索结果摘要。"
    )
    args_schema: Type[BaseModel] = SearchInput

    # 搜索API配置（可以从环境变量读取）
    search_api_url: str = "https://api.example.com/search"  # 示例URL
    search_api_key: Optional[str] = None

    def _mock_search(self, query: str, max_results: int) -> list:
        """
        模拟搜索结果（用于演示）

        在实际生产环境中，应该替换为真实的搜索API调用
        例如：百度搜索API、Google Custom Search API、Bing Search API等

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        # 模拟搜索结果
        mock_results = [
            {
                "title": f"关于'{query}'的搜索结果 1",
                "snippet": f"这是关于{query}的详细信息。包含了相关的背景知识和最新动态。",
                "url": f"https://example.com/result1?q={query}",
                "source": "示例网站1",
            },
            {
                "title": f"'{query}'完整指南",
                "snippet": f"深入了解{query}的各个方面，包括基础概念、应用场景和最佳实践。",
                "url": f"https://example.com/result2?q={query}",
                "source": "示例网站2",
            },
            {
                "title": f"{query}的最新研究进展",
                "snippet": f"最新的{query}研究成果和技术突破，来自权威机构的报告。",
                "url": f"https://example.com/result3?q={query}",
                "source": "示例网站3",
            },
            {
                "title": f"如何使用{query}",
                "snippet": f"实用的{query}使用教程，包含详细的步骤说明和示例代码。",
                "url": f"https://example.com/result4?q={query}",
                "source": "示例网站4",
            },
            {
                "title": f"{query}常见问题解答",
                "snippet": f"关于{query}的常见问题和解答，帮助您快速解决疑问。",
                "url": f"https://example.com/result5?q={query}",
                "source": "示例网站5",
            },
        ]

        return mock_results[:max_results]

    async def _real_search(self, query: str, max_results: int) -> list:
        """
        真实的搜索API调用（示例实现）

        在实际使用时，需要：
        1. 配置真实的搜索API URL和密钥
        2. 处理API的认证和请求格式
        3. 解析API返回的结果

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 构建请求参数
                params = {
                    "q": query,
                    "num": max_results,
                }

                headers = {}
                if self.search_api_key:
                    headers["Authorization"] = f"Bearer {self.search_api_key}"

                # 发送请求
                response = await client.get(
                    self.search_api_url, params=params, headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    # 解析搜索结果（根据实际API格式调整）
                    return data.get("results", [])
                else:
                    return []

        except Exception as e:
            # 如果API调用失败，返回空列表
            return []

    def _format_results(self, results: list) -> str:
        """
        格式化搜索结果为可读的字符串

        Args:
            results: 搜索结果列表

        Returns:
            格式化后的结果字符串
        """
        if not results:
            return "未找到相关搜索结果。"

        formatted = f"找到 {len(results)} 条搜索结果:\n\n"

        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            snippet = result.get("snippet", "无摘要")
            url = result.get("url", "")
            source = result.get("source", "未知来源")

            formatted += f"{i}. {title}\n"
            formatted += f"   来源: {source}\n"
            formatted += f"   摘要: {snippet}\n"
            if url:
                formatted += f"   链接: {url}\n"
            formatted += "\n"

        return formatted.strip()

    def _run(
        self,
        query: str,
        max_results: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        执行搜索（同步版本）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            run_manager: 回调管理器

        Returns:
            格式化的搜索结果
        """
        try:
            # 验证输入
            if not query or not query.strip():
                return "错误: 搜索查询不能为空"

            query = query.strip()

            # 限制max_results范围
            max_results = max(1, min(max_results, 10))

            # 执行搜索（使用模拟搜索）
            # 在生产环境中，应该使用真实的搜索API
            results = self._mock_search(query, max_results)

            # 格式化并返回结果
            return self._format_results(results)

        except Exception as e:
            return f"搜索失败: {str(e)}"

    async def _arun(
        self,
        query: str,
        max_results: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        执行搜索（异步版本）

        Args:
            query: 搜索查询
            max_results: 最大结果数
            run_manager: 回调管理器

        Returns:
            格式化的搜索结果
        """
        try:
            # 验证输入
            if not query or not query.strip():
                return "错误: 搜索查询不能为空"

            query = query.strip()

            # 限制max_results范围
            max_results = max(1, min(max_results, 10))

            # 尝试使用真实API，如果失败则使用模拟搜索
            if self.search_api_key:
                results = await self._real_search(query, max_results)
                if results:
                    return self._format_results(results)

            # 使用模拟搜索
            results = self._mock_search(query, max_results)
            return self._format_results(results)

        except Exception as e:
            return f"搜索失败: {str(e)}"
