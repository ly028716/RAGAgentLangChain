"""数据分析工具 - 用于数据处理和分析"""
import json
from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class DataAnalysisInput(BaseModel):
    """数据分析工具的输入模型"""

    operation: str = Field(
        description="要执行的分析操作: 'stats'(统计分析), 'filter'(数据过滤), 'aggregate'(聚合计算), 'sort'(排序)"
    )
    data: str = Field(description="要分析的数据，JSON格式的数组")
    params: Optional[str] = Field(
        default=None, description="操作参数，JSON格式，例如: {'key': 'age', 'order': 'desc'}"
    )


class DataAnalysisTool(BaseTool):
    """
    数据分析工具 - 对数据进行分析和处理

    支持的操作:
    - stats: 统计分析（计算平均值、最大值、最小值、总和等）
    - filter: 数据过滤（根据条件筛选数据）
    - aggregate: 聚合计算（按字段分组统计）
    - sort: 数据排序（按指定字段排序）

    数据格式:
    - 输入数据应为JSON数组格式
    - 支持数值型和字符串型数据
    """

    name: str = "data_analysis"
    description: str = (
        "用于数据分析和处理的工具。"
        "支持统计分析(stats)、数据过滤(filter)、聚合计算(aggregate)、排序(sort)。"
        "示例: operation='stats', data='[{\"age\": 25}, {\"age\": 30}]', params='{\"key\": \"age\"}'"
    )
    args_schema: Type[BaseModel] = DataAnalysisInput
    max_rows: int = 10000  # 最大处理行数

    def _parse_data(self, data_str: str) -> List[Dict[str, Any]]:
        """解析JSON数据"""
        try:
            data = json.loads(data_str)
            if not isinstance(data, list):
                raise ValueError("数据必须是数组格式")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")

    def _parse_params(self, params_str: Optional[str]) -> Dict[str, Any]:
        """解析参数"""
        if not params_str:
            return {}
        try:
            params = json.loads(params_str)
            if not isinstance(params, dict):
                raise ValueError("参数必须是对象格式")
            return params
        except json.JSONDecodeError as e:
            raise ValueError(f"参数解析失败: {str(e)}")

    def _stats_analysis(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> str:
        """统计分析"""
        key = params.get("key")
        if not key:
            return "错误: 统计分析需要指定key参数"

        # 提取数值
        values = []
        for item in data:
            if key in item:
                try:
                    values.append(float(item[key]))
                except (ValueError, TypeError):
                    pass

        if not values:
            return f"错误: 没有找到有效的数值数据（key: {key}）"

        # 计算统计指标
        count = len(values)
        total = sum(values)
        mean = total / count
        sorted_values = sorted(values)
        min_val = sorted_values[0]
        max_val = sorted_values[-1]
        median = (
            sorted_values[count // 2]
            if count % 2 == 1
            else (sorted_values[count // 2 - 1] + sorted_values[count // 2]) / 2
        )

        result = {
            "count": count,
            "sum": round(total, 2),
            "mean": round(mean, 2),
            "median": round(median, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
        }

        return f"统计结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}"

    def _filter_data(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> str:
        """数据过滤"""
        key = params.get("key")
        operator = params.get("operator", "==")
        value = params.get("value")

        if not key or value is None:
            return "错误: 过滤操作需要指定key和value参数"

        # 执行过滤
        filtered = []
        for item in data:
            if key not in item:
                continue

            item_value = item[key]
            match = False

            try:
                if operator == "==":
                    match = item_value == value
                elif operator == "!=":
                    match = item_value != value
                elif operator == ">":
                    match = float(item_value) > float(value)
                elif operator == "<":
                    match = float(item_value) < float(value)
                elif operator == ">=":
                    match = float(item_value) >= float(value)
                elif operator == "<=":
                    match = float(item_value) <= float(value)
                elif operator == "contains":
                    match = str(value) in str(item_value)
            except (ValueError, TypeError):
                pass

            if match:
                filtered.append(item)

        return f"过滤结果: 找到 {len(filtered)} 条记录（显示前10条）\n{json.dumps(filtered[:10], indent=2, ensure_ascii=False)}"

    def _aggregate_data(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> str:
        """聚合计算"""
        group_key = params.get("group_key")
        agg_key = params.get("agg_key")
        agg_func = params.get("agg_func", "sum")

        if not group_key or not agg_key:
            return "错误: 聚合操作需要指定group_key和agg_key参数"

        # 按组聚合
        groups: Dict[str, List[float]] = {}
        for item in data:
            if group_key not in item or agg_key not in item:
                continue

            group_value = str(item[group_key])
            try:
                agg_value = float(item[agg_key])
                if group_value not in groups:
                    groups[group_value] = []
                groups[group_value].append(agg_value)
            except (ValueError, TypeError):
                pass

        # 计算聚合结果
        result = {}
        for group, values in groups.items():
            if agg_func == "sum":
                result[group] = round(sum(values), 2)
            elif agg_func == "avg":
                result[group] = round(sum(values) / len(values), 2)
            elif agg_func == "count":
                result[group] = len(values)
            elif agg_func == "min":
                result[group] = round(min(values), 2)
            elif agg_func == "max":
                result[group] = round(max(values), 2)

        return f"聚合结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}"

    def _sort_data(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> str:
        """数据排序"""
        key = params.get("key")
        order = params.get("order", "asc")

        if not key:
            return "错误: 排序操作需要指定key参数"

        # 执行排序
        try:
            # 将缺失键的项排在最后
            def sort_key(x):
                value = x.get(key)
                if value is None:
                    # 使用特殊值确保None排在最后
                    return (1, "")  # (1, "") 会排在 (0, value) 之后
                return (0, value)

            sorted_data = sorted(
                data, key=sort_key, reverse=(order == "desc")
            )
            return f"排序结果: {len(sorted_data)} 条记录\n{json.dumps(sorted_data[:10], indent=2, ensure_ascii=False)}"
        except Exception as e:
            return f"排序失败: {str(e)}"

    def _run(
        self,
        operation: str,
        data: str,
        params: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        执行数据分析

        Args:
            operation: 操作类型
            data: JSON格式的数据
            params: 操作参数
            run_manager: 回调管理器

        Returns:
            分析结果的字符串表示
        """
        try:
            # 解析数据和参数
            parsed_data = self._parse_data(data)
            parsed_params = self._parse_params(params)

            # 检查数据量
            if len(parsed_data) > self.max_rows:
                return f"错误: 数据量超过限制（最大 {self.max_rows} 行）"

            # 执行对应的操作
            if operation == "stats":
                return self._stats_analysis(parsed_data, parsed_params)
            elif operation == "filter":
                return self._filter_data(parsed_data, parsed_params)
            elif operation == "aggregate":
                return self._aggregate_data(parsed_data, parsed_params)
            elif operation == "sort":
                return self._sort_data(parsed_data, parsed_params)
            else:
                return f"错误: 不支持的操作类型: {operation}"

        except ValueError as e:
            return f"错误: {str(e)}"
        except Exception as e:
            return f"数据分析失败: {str(e)}"

    async def _arun(
        self,
        operation: str,
        data: str,
        params: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """异步执行数据分析（实际上调用同步方法）"""
        return self._run(operation, data, params, run_manager)
