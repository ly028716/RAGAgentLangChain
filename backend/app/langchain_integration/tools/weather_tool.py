"""天气查询工具 - 用于查询天气信息"""
import json
from datetime import datetime
from typing import Optional, Type

import httpx
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    """天气工具的输入模型"""

    location: str = Field(description="要查询天气的城市或地区名称，例如: '北京', '上海', 'Beijing'")
    days: int = Field(default=1, ge=1, le=7, description="查询未来几天的天气，默认1天（今天）")


class WeatherTool(BaseTool):
    """
    天气查询工具 - 查询指定地区的天气信息

    支持的功能:
    - 查询当前天气
    - 查询未来几天的天气预报
    - 返回温度、湿度、风力等信息

    注意: 这是一个简化的实现，实际生产环境中应该集成真实的天气API
    如和风天气API、OpenWeatherMap API等
    """

    name: str = "weather"
    description: str = (
        "用于查询天气信息的工具。"
        "输入应该是一个城市或地区名称，例如: '北京', '上海', 'Beijing'。"
        "工具会返回该地区的当前天气和未来几天的天气预报。"
    )
    args_schema: Type[BaseModel] = WeatherInput

    # 天气API配置（可以从环境变量读取）
    weather_api_url: str = "https://api.example.com/weather"  # 示例URL
    weather_api_key: Optional[str] = None

    def _mock_weather(self, location: str, days: int) -> dict:
        """
        模拟天气数据（用于演示）

        在实际生产环境中，应该替换为真实的天气API调用
        例如：和风天气API、OpenWeatherMap API、心知天气API等

        Args:
            location: 城市或地区名称
            days: 查询天数

        Returns:
            天气数据字典
        """
        # 模拟当前天气
        current_weather = {
            "location": location,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": 22,
            "feels_like": 20,
            "condition": "晴",
            "humidity": 45,
            "wind_speed": 12,
            "wind_direction": "东北风",
            "air_quality": "良",
            "aqi": 65,
            "uv_index": 5,
            "visibility": 10,
        }

        # 模拟未来天气预报
        forecast = []
        conditions = ["晴", "多云", "阴", "小雨", "晴转多云"]

        for i in range(days):
            day_forecast = {
                "date": datetime.now().strftime("%Y-%m-%d") if i == 0 else f"未来第{i}天",
                "day": "今天" if i == 0 else f"未来第{i}天",
                "condition": conditions[i % len(conditions)],
                "temp_high": 25 + i,
                "temp_low": 15 + i,
                "humidity": 40 + i * 5,
                "wind_speed": 10 + i * 2,
                "precipitation_probability": 10 + i * 10,
            }
            forecast.append(day_forecast)

        return {"current": current_weather, "forecast": forecast}

    async def _real_weather(self, location: str, days: int) -> Optional[dict]:
        """
        真实的天气API调用（示例实现）

        在实际使用时，需要：
        1. 配置真实的天气API URL和密钥
        2. 处理API的认证和请求格式
        3. 解析API返回的结果

        Args:
            location: 城市或地区名称
            days: 查询天数

        Returns:
            天气数据字典，如果失败返回None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 构建请求参数
                params = {
                    "location": location,
                    "days": days,
                }

                headers = {}
                if self.weather_api_key:
                    headers["Authorization"] = f"Bearer {self.weather_api_key}"

                # 发送请求
                response = await client.get(
                    self.weather_api_url, params=params, headers=headers
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return None

        except Exception as e:
            # 如果API调用失败，返回None
            return None

    def _format_weather(self, weather_data: dict) -> str:
        """
        格式化天气数据为可读的字符串

        Args:
            weather_data: 天气数据字典

        Returns:
            格式化后的天气信息字符串
        """
        if not weather_data:
            return "无法获取天气信息。"

        current = weather_data.get("current", {})
        forecast = weather_data.get("forecast", [])

        # 格式化当前天气
        result = f"📍 {current.get('location', '未知地区')} 天气信息\n"
        result += f"🕐 更新时间: {current.get('update_time', '未知')}\n\n"

        result += "【当前天气】\n"
        result += f"🌡️  温度: {current.get('temperature', 'N/A')}°C (体感 {current.get('feels_like', 'N/A')}°C)\n"
        result += f"☁️  天气: {current.get('condition', '未知')}\n"
        result += f"💧 湿度: {current.get('humidity', 'N/A')}%\n"
        result += f"🌬️  风速: {current.get('wind_speed', 'N/A')} km/h ({current.get('wind_direction', '未知')})\n"
        result += f"🏭 空气质量: {current.get('air_quality', '未知')} (AQI: {current.get('aqi', 'N/A')})\n"
        result += f"☀️  紫外线指数: {current.get('uv_index', 'N/A')}\n"
        result += f"👁️  能见度: {current.get('visibility', 'N/A')} km\n"

        # 格式化天气预报
        if forecast:
            result += "\n【天气预报】\n"
            for day in forecast:
                result += f"\n📅 {day.get('day', '未知')}\n"
                result += f"   天气: {day.get('condition', '未知')}\n"
                result += f"   温度: {day.get('temp_low', 'N/A')}°C ~ {day.get('temp_high', 'N/A')}°C\n"
                result += f"   湿度: {day.get('humidity', 'N/A')}%\n"
                result += f"   风速: {day.get('wind_speed', 'N/A')} km/h\n"
                result += f"   降水概率: {day.get('precipitation_probability', 'N/A')}%\n"

        return result

    def _validate_location(self, location: str) -> bool:
        """
        验证地区名称的有效性

        Args:
            location: 地区名称

        Returns:
            是否有效
        """
        if not location or not location.strip():
            return False

        # 检查长度
        if len(location.strip()) < 2 or len(location.strip()) > 50:
            return False

        return True

    def _run(
        self,
        location: str,
        days: int = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        查询天气（同步版本）

        Args:
            location: 城市或地区名称
            days: 查询天数
            run_manager: 回调管理器

        Returns:
            格式化的天气信息
        """
        try:
            # 验证输入
            if not self._validate_location(location):
                return "错误: 请提供有效的城市或地区名称（2-50个字符）"

            location = location.strip()

            # 限制days范围
            days = max(1, min(days, 7))

            # 执行查询（使用模拟天气）
            # 在生产环境中，应该使用真实的天气API
            weather_data = self._mock_weather(location, days)

            # 格式化并返回结果
            return self._format_weather(weather_data)

        except Exception as e:
            return f"天气查询失败: {str(e)}"

    async def _arun(
        self,
        location: str,
        days: int = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        查询天气（异步版本）

        Args:
            location: 城市或地区名称
            days: 查询天数
            run_manager: 回调管理器

        Returns:
            格式化的天气信息
        """
        try:
            # 验证输入
            if not self._validate_location(location):
                return "错误: 请提供有效的城市或地区名称（2-50个字符）"

            location = location.strip()

            # 限制days范围
            days = max(1, min(days, 7))

            # 尝试使用真实API，如果失败则使用模拟天气
            if self.weather_api_key:
                weather_data = await self._real_weather(location, days)
                if weather_data:
                    return self._format_weather(weather_data)

            # 使用模拟天气
            weather_data = self._mock_weather(location, days)
            return self._format_weather(weather_data)

        except Exception as e:
            return f"天气查询失败: {str(e)}"
