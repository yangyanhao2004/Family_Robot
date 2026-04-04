import asyncio
import websockets
import json
import logging
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pi_client')

# PC 后端 WebSocket 地址
PC_IP = "10.155.77.112"  # 请替换为实际的 PC IP 地址
WS_URL = f"ws://{PC_IP}:8080/ws"

# 重连间隔（秒）
RECONNECT_INTERVAL = 3

# 状态发送间隔（秒）
STATUS_INTERVAL = 2

# 电机控制接口函数
def move_forward():
    """前进"""
    logger.info("执行前进指令")
    # 预留硬件接口，实际项目中替换为真实的电机控制代码
    pass

def move_backward():
    """后退"""
    logger.info("执行后退指令")
    # 预留硬件接口，实际项目中替换为真实的电机控制代码
    pass

def turn_left():
    """左转"""
    logger.info("执行左转指令")
    # 预留硬件接口，实际项目中替换为真实的电机控制代码
    pass

def turn_right():
    """右转"""
    logger.info("执行右转指令")
    # 预留硬件接口，实际项目中替换为真实的电机控制代码
    pass

def stop():
    """停止"""
    logger.info("执行停止指令")
    # 预留硬件接口，实际项目中替换为真实的电机控制代码
    pass

def light_on():
    """开灯"""
    logger.info("执行开灯指令")
    # 预留硬件接口，实际项目中替换为真实的灯光控制代码
    pass

def light_off():
    """关灯"""
    logger.info("执行关灯指令")
    # 预留硬件接口，实际项目中替换为真实的灯光控制代码
    pass

# 命令处理映射
COMMAND_HANDLERS = {
    "forward": move_forward,
    "backward": move_backward,
    "left": turn_left,
    "right": turn_right,
    "stop": stop,
    "light_on": light_on,
    "light_off": light_off
}

async def send_register_message(websocket):
    """发送注册消息"""
    register_message = {
        "type": "register",
        "role": "robot"
    }
    await websocket.send(json.dumps(register_message))
    logger.info("发送注册消息")

async def send_status_message(websocket):
    """发送状态消息"""
    # 模拟状态数据，实际项目中替换为真实的传感器数据
    status_message = {
        "type": "status",
        "payload": {
            "battery": random.randint(70, 100),  # 模拟电池电量
            "isRunning": random.choice([True, False]),  # 模拟运行状态
            "temperature": round(random.uniform(30, 40), 1),  # 模拟温度
            "signalStrength": random.randint(1, 5)  # 模拟信号强度
        }
    }
    await websocket.send(json.dumps(status_message))
    logger.info(f"发送状态消息: {status_message}")

async def handle_message(websocket, message):
    """处理接收到的消息"""
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "command":
            payload = data.get("payload", {})
            command = payload.get("command")
            
            if command in COMMAND_HANDLERS:
                COMMAND_HANDLERS[command]()
            else:
                logger.warning(f"未知命令: {command}")
        elif message_type == "error":
            error_message = data.get("message", "未知错误")
            logger.error(f"收到错误消息: {error_message}")
        else:
            logger.debug(f"收到其他类型消息: {message_type}")
    except json.JSONDecodeError:
        logger.error(f"消息格式错误: {message}")
    except Exception as e:
        logger.error(f"处理消息时出错: {str(e)}")

async def status_sender(websocket):
    """周期性发送状态消息"""
    while True:
        try:
            await send_status_message(websocket)
            await asyncio.sleep(STATUS_INTERVAL)
        except websockets.ConnectionClosed:
            break
        except Exception as e:
            logger.error(f"发送状态消息时出错: {str(e)}")
            await asyncio.sleep(STATUS_INTERVAL)

async def websocket_client():
    """WebSocket 客户端主函数"""
    while True:
        try:
            logger.info(f"尝试连接到 PC 后端: {WS_URL}")
            async with websockets.connect(WS_URL) as websocket:
                logger.info("连接成功")
                
                # 发送注册消息
                await send_register_message(websocket)
                
                # 启动状态发送任务
                status_task = asyncio.create_task(status_sender(websocket))
                
                try:
                    # 接收并处理消息
                    async for message in websocket:
                        await handle_message(websocket, message)
                except websockets.ConnectionClosed:
                    logger.info("连接已关闭")
                finally:
                    # 取消状态发送任务
                    status_task.cancel()
                    try:
                        await status_task
                    except asyncio.CancelledError:
                        pass
        except Exception as e:
            logger.error(f"连接失败: {str(e)}")
        
        # 重连间隔
        logger.info(f"{RECONNECT_INTERVAL}秒后尝试重连...")
        await asyncio.sleep(RECONNECT_INTERVAL)

async def main():
    """主入口"""
    logger.info("树莓派客户端启动")
    await websocket_client()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("客户端已手动停止")
