import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from core.connection_manager import manager
from core.message_router import router
from front.handlers import handle_command_message, handle_webrtc_signaling_message
from models.common import RegisterMessage, BaseMessage, ErrorMessage

# 配置日志
logger = logging.getLogger('backend.front')

async def websocket_front_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info(f"前端连接已注册: {client_ip}:{client_port}")
    manager.register_web(websocket)
    
    try:
        logger.info(f"开始处理前端 {client_ip}:{client_port} 的消息")
        while True:
            # 设置较长的接收超时时间，例如60秒
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                logger.debug(f"收到前端 {client_ip}:{client_port} 的消息: {data}")
                
                try:
                    base_msg = BaseMessage(**data)
                    message_type = base_msg.type
                    
                    if message_type == "register":
                        register_msg = RegisterMessage(**data)
                        logger.info(f"前端 {client_ip}:{client_port} 重新注册")
                        # 发送注册成功消息
                        register_success_msg = {
                            "type": "register_success"
                        }
                        await websocket.send_json(register_success_msg)
                        logger.info(f"发送注册成功消息给前端 {client_ip}:{client_port}")
                    elif message_type == "command":
                        logger.info(f"处理前端 {client_ip}:{client_port} 的控制指令: {data['payload']['command']}")
                        await handle_command_message(data)
                        await router.route_message("web", data)
                    elif message_type == "webrtc_signaling":
                        logger.info(f"处理前端 {client_ip}:{client_port} 的 WebRTC 信令消息")
                        await handle_webrtc_signaling_message(data)
                        await router.route_message("web", data)
                    elif message_type == "heartbeat":
                        logger.debug(f"收到前端 {client_ip}:{client_port} 的心跳消息")
                        # 处理心跳消息，无需回复
                        pass
                    else:
                        logger.warning(f"收到前端 {client_ip}:{client_port} 的未知消息类型: {message_type}")
                except Exception as e:
                    logger.error(f"处理前端 {client_ip}:{client_port} 消息时出错: {str(e)}")
                    error_msg = ErrorMessage(
                        type="error",
                        message=f"消息格式非法: {str(e)}"
                    )
                    await manager.send_to_web(error_msg.model_dump())
            except asyncio.TimeoutError:
                # 超时后继续循环，保持连接活跃
                logger.debug(f"前端 {client_ip}:{client_port} 消息接收超时，保持连接活跃")
                pass
    except WebSocketDisconnect:
        logger.info(f"前端 {client_ip}:{client_port} 连接断开")
        manager.disconnect(websocket)
    except Exception as e:
        # 妥善处理错误，避免因小错误而关闭连接
        logger.error(f"前端 {client_ip}:{client_port} 连接处理时出错: {str(e)}")
        try:
            error_msg = ErrorMessage(
                type="error",
                message=f"处理消息时出错: {str(e)}"
            )
            await manager.send_to_web(error_msg.model_dump())
        except:
            pass
        finally:
            manager.disconnect(websocket)
