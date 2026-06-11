"""
Tool definitions for Qwen2.5 function calling.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time and date. Use when user asks what time it is, what day it is, or current date.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a location. Use when user asks about weather, temperature, or conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'London', 'New York', 'Tokyo'). If not specified, use 'current location'."
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": "Get top news headlines. Use when user asks about news, headlines, or what's happening in the world.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "News category: business, entertainment, health, science, sports, or technology. Leave empty for general news."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Get the assistant's system health status including CPU temperature, memory, uptime. Use when user asks how you are doing, system status, or health check.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_joke",
            "description": "Tell a random joke. Use when user asks for a joke, wants to hear something funny, or asks you to make them laugh.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cloud_handoff",
            "description": "Hand off complex queries to cloud AI for better answers. Use for: creative writing, complex reasoning, coding questions, detailed explanations, anything requiring deep knowledge or nuanced responses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The full user query to send to cloud AI"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# System prompt for the router
SYSTEM_PROMPT = """你是贾维斯，一个运行在树莓派上的语音助手。你可以使用工具来完成特定任务。

重要规则：
1. 对于简单的问候、闲聊和基本问题 - 直接回复，不要使用工具
2. 对于时间/日期问题 - 使用 get_current_time
3. 对于天气问题 - 使用 get_weather
4. 对于新闻/头条问题 - 使用 get_news
5. 对于系统状态或者询问"你怎么样"的问题 - 使用 get_system_status
6. 对于笑话或幽默请求 - 使用 get_joke
7. 对于需要深度知识、创意任务或编程的复杂问题 - 使用 cloud_handoff

回复要简洁、口语化，因为会通过语音朗读出来。避免长列表或复杂格式。"""
