"""
Weather tool - fetches weather from OpenWeatherMap.
"""

import httpx
from typing import Optional
import os


class WeatherTool:
    """Fetches weather data from OpenWeatherMap."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    # Chinese → English city name mapping for OpenWeatherMap API
    _CITY_MAP = {
        # Chinese cities
        "北京": "Beijing",
        "上海": "Shanghai",
        "广州": "Guangzhou",
        "深圳": "Shenzhen",
        "成都": "Chengdu",
        "重庆": "Chongqing",
        "杭州": "Hangzhou",
        "南京": "Nanjing",
        "武汉": "Wuhan",
        "西安": "Xi'an",
        "天津": "Tianjin",
        "苏州": "Suzhou",
        "长沙": "Changsha",
        "郑州": "Zhengzhou",
        "济南": "Jinan",
        "青岛": "Qingdao",
        "大连": "Dalian",
        "厦门": "Xiamen",
        "昆明": "Kunming",
        "合肥": "Hefei",
        "福州": "Fuzhou",
        "南昌": "Nanchang",
        "沈阳": "Shenyang",
        "长春": "Changchun",
        "哈尔滨": "Harbin",
        "贵阳": "Guiyang",
        "兰州": "Lanzhou",
        "南宁": "Nanning",
        "太原": "Taiyuan",
        "石家庄": "Shijiazhuang",
        "海口": "Haikou",
        "拉萨": "Lhasa",
        "乌鲁木齐": "Urumqi",
        "呼和浩特": "Hohhot",
        "银川": "Yinchuan",
        "西宁": "Xining",
        "东莞": "Dongguan",
        "佛山": "Foshan",
        "宁波": "Ningbo",
        "温州": "Wenzhou",
        "无锡": "Wuxi",
        "台北": "Taipei",
        "香港": "Hong Kong",
        "澳门": "Macau",
        # Province → capital
        "山东": "Jinan",
        "山西": "Taiyuan",
        "广东": "Guangzhou",
        "广西": "Nanning",
        "江苏": "Nanjing",
        "浙江": "Hangzhou",
        "四川": "Chengdu",
        "福建": "Fuzhou",
        "湖北": "Wuhan",
        "湖南": "Changsha",
        "河南": "Zhengzhou",
        "河北": "Shijiazhuang",
        "辽宁": "Shenyang",
        "吉林": "Changchun",
        "黑龙江": "Harbin",
        "云南": "Kunming",
        "贵州": "Guiyang",
        "甘肃": "Lanzhou",
        "青海": "Xining",
        "海南": "Haikou",
        "西藏": "Lhasa",
        "新疆": "Urumqi",
        "内蒙古": "Hohhot",
        "宁夏": "Yinchuan",
        "江西": "Nanchang",
        "安徽": "Hefei",
        "陕西": "Xi'an",
        # International
        "东京": "Tokyo",
        "纽约": "New York",
        "伦敦": "London",
        "巴黎": "Paris",
        "首尔": "Seoul",
        "悉尼": "Sydney",
        "新加坡": "Singapore",
        "曼谷": "Bangkok",
        "迪拜": "Dubai",
        "莫斯科": "Moscow",
        "华盛顿": "Washington",
        "洛杉矶": "Los Angeles",
        "芝加哥": "Chicago",
        "旧金山": "San Francisco",
        "多伦多": "Toronto",
        "温哥华": "Vancouver",
        "柏林": "Berlin",
        "罗马": "Rome",
        "马德里": "Madrid",
        "波士顿": "Boston",
        "西雅图": "Seattle",
    }

    # Weather description translation (OpenWeatherMap returns English)
    _WEATHER_ZH = {
        "clear sky": "晴朗",
        "few clouds": "少云",
        "scattered clouds": "多云",
        "broken clouds": "阴天",
        "overcast clouds": "阴天",
        "light rain": "小雨",
        "moderate rain": "中雨",
        "heavy rain": "大雨",
        "thunderstorm": "雷暴",
        "snow": "雪",
        "mist": "薄雾",
        "haze": "雾霞",
        "fog": "雾",
        "drizzle": "毛毛雨",
        "shower rain": "阵雨",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key required")

        self.client = httpx.Client(timeout=10.0)

    @classmethod
    def _to_english_city(cls, location: str) -> str:
        """Translate Chinese city name to English for the API."""
        return cls._CITY_MAP.get(location, location)

    @classmethod
    def _translate_desc(cls, desc_en: str) -> str:
        """Translate weather description to Chinese (fuzzy match)."""
        desc_lower = desc_en.lower()
        for en, zh in cls._WEATHER_ZH.items():
            if en in desc_lower:
                return zh
        return desc_en  # fallback: return English as-is

    def get_weather(self, location: str) -> str:
        """
        Get weather for a location.

        Args:
            location: City name (Chinese or English)

        Returns:
            Chinese natural language weather description
        """
        query = self._to_english_city(location)
        try:
            response = self.client.get(
                self.BASE_URL,
                params={
                    "q": query,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": "zh_cn",
                },
            )
            response.raise_for_status()
            data = response.json()

            temp = round(data["main"]["temp"])
            feels_like = round(data["main"]["feels_like"])
            desc_en = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            city_name = location  # use the Chinese name the user gave

            # OpenWeatherMap lang=zh_cn sometimes works, sometimes doesn't
            # Use our own translation as fallback
            desc = self._translate_desc(desc_en)

            return (
                f"{city_name}现在{desc}，气温{temp}度，"
                f"体感温度{feels_like}度，"
                f"湿度百分之{humidity}。"
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"找不到{location}的天气数据。"
            raise
        except Exception as e:
            return f"抱歉，暂时无法获取天气信息。{str(e)}"
