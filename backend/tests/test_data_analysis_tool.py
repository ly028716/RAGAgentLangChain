"""
数据分析工具测试
"""
import pytest
import json

from app.langchain_integration.tools.data_analysis_tool import DataAnalysisTool


@pytest.fixture
def data_tool():
    """创建数据分析工具实例"""
    return DataAnalysisTool()


@pytest.fixture
def sample_data():
    """示例数据"""
    return [
        {"name": "Alice", "age": 25, "score": 85},
        {"name": "Bob", "age": 30, "score": 92},
        {"name": "Charlie", "age": 25, "score": 78},
        {"name": "David", "age": 35, "score": 88},
        {"name": "Eve", "age": 30, "score": 95}
    ]


class TestDataAnalysisTool:
    """数据分析工具测试类"""

    def test_tool_initialization(self, data_tool):
        """测试工具初始化"""
        assert data_tool.name == "data_analysis"
        assert data_tool.max_rows == 10000
        assert "数据分析" in data_tool.description

    def test_stats_analysis_success(self, data_tool, sample_data):
        """测试统计分析成功"""
        result = data_tool._run(
            operation="stats",
            data=json.dumps(sample_data),
            params=json.dumps({"key": "age"})
        )

        assert "统计结果" in result
        assert "count" in result
        assert "mean" in result
        assert "median" in result

    def test_stats_analysis_missing_key(self, data_tool, sample_data):
        """测试统计分析缺少key参数"""
        result = data_tool._run(
            operation="stats",
            data=json.dumps(sample_data)
        )

        assert "错误" in result
        assert "key" in result

    def test_filter_data_equal(self, data_tool, sample_data):
        """测试数据过滤（等于）"""
        result = data_tool._run(
            operation="filter",
            data=json.dumps(sample_data),
            params=json.dumps({"key": "age", "operator": "==", "value": 25})
        )

        assert "过滤结果" in result
        assert "2 条记录" in result
        assert "显示前10条" in result

    def test_filter_data_greater_than(self, data_tool, sample_data):
        """测试数据过滤（大于）"""
        result = data_tool._run(
            operation="filter",
            data=json.dumps(sample_data),
            params=json.dumps({"key": "score", "operator": ">", "value": 85})
        )

        assert "过滤结果" in result
        filtered = json.loads(result.split("\n", 1)[1])
        assert len(filtered) == 3  # Bob, David, Eve

    def test_filter_data_contains(self, data_tool, sample_data):
        """测试数据过滤（包含）"""
        result = data_tool._run(
            operation="filter",
            data=json.dumps(sample_data),
            params=json.dumps({"key": "name", "operator": "contains", "value": "e"})
        )

        assert "过滤结果" in result

    def test_aggregate_data_sum(self, data_tool, sample_data):
        """测试聚合计算（求和）"""
        result = data_tool._run(
            operation="aggregate",
            data=json.dumps(sample_data),
            params=json.dumps({
                "group_key": "age",
                "agg_key": "score",
                "agg_func": "sum"
            })
        )

        assert "聚合结果" in result
        agg_result = json.loads(result.split("\n", 1)[1])
        assert "25" in agg_result
        assert "30" in agg_result

    def test_aggregate_data_avg(self, data_tool, sample_data):
        """测试聚合计算（平均值）"""
        result = data_tool._run(
            operation="aggregate",
            data=json.dumps(sample_data),
            params=json.dumps({
                "group_key": "age",
                "agg_key": "score",
                "agg_func": "avg"
            })
        )

        assert "聚合结果" in result

    def test_sort_data_asc(self, data_tool, sample_data):
        """测试数据排序（升序）"""
        result = data_tool._run(
            operation="sort",
            data=json.dumps(sample_data),
            params=json.dumps({"key": "age", "order": "asc"})
        )

        assert "排序结果" in result
        sorted_data = json.loads(result.split("\n", 1)[1])
        assert sorted_data[0]["age"] == 25

    def test_sort_data_desc(self, data_tool, sample_data):
        """测试数据排序（降序）"""
        result = data_tool._run(
            operation="sort",
            data=json.dumps(sample_data),
            params=json.dumps({"key": "score", "order": "desc"})
        )

        assert "排序结果" in result
        sorted_data = json.loads(result.split("\n", 1)[1])
        assert sorted_data[0]["score"] == 95

    def test_sort_data_missing_key(self, data_tool):
        """测试排序时处理缺失键"""
        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob"},  # 缺少age
            {"name": "Charlie", "age": 30}
        ]

        result = data_tool._run(
            operation="sort",
            data=json.dumps(data),
            params=json.dumps({"key": "age", "order": "asc"})
        )

        assert "排序结果" in result

    def test_invalid_json_data(self, data_tool):
        """测试无效的JSON数据"""
        result = data_tool._run(
            operation="stats",
            data="invalid json",
            params=json.dumps({"key": "age"})
        )

        assert "错误" in result
        assert "JSON解析失败" in result

    def test_non_array_data(self, data_tool):
        """测试非数组数据"""
        result = data_tool._run(
            operation="stats",
            data=json.dumps({"key": "value"}),
            params=json.dumps({"key": "age"})
        )

        assert "错误" in result
        assert "数组格式" in result

    def test_max_rows_limit(self, data_tool):
        """测试最大行数限制"""
        large_data = [{"id": i} for i in range(10001)]

        result = data_tool._run(
            operation="stats",
            data=json.dumps(large_data),
            params=json.dumps({"key": "id"})
        )

        assert "错误" in result
        assert "数据量超过限制" in result

    def test_invalid_operation(self, data_tool, sample_data):
        """测试无效的操作类型"""
        result = data_tool._run(
            operation="invalid",
            data=json.dumps(sample_data)
        )

        assert "错误" in result
        assert "不支持的操作类型" in result

    @pytest.mark.asyncio
    async def test_async_run(self, data_tool, sample_data):
        """测试异步执行"""
        result = await data_tool._arun(
            operation="stats",
            data=json.dumps(sample_data),
            params=json.dumps({"key": "age"})
        )

        assert "统计结果" in result
