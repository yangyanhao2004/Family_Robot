import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from core.connection_manager import manager
from core.message_router import router
from pi.handlers import handle_status_message, handle_webrtc_signaling_message
from models.common import RegisterMessage, BaseMessage, ErrorMessage

# 配置日志
logger = logging.getLogger('backend.pi')

async def websocket_pi_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info(f"树莓派连接已注册: {client_ip}:{client_port}")
    manager.register_pi(websocket)
    
    try:
        logger.info(f"开始处理树莓派 {client_ip}:{client_port} 的消息")
        while True:
            # 设置较长的接收超时时间，例如60秒
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                logger.debug(f"收到树莓派 {client_ip}:{client_port} 的消息: {data}")
                
                try:
                    base_msg = BaseMessage(**data)
                    message_type = base_msg.type
                    
                    if message_type == "register":
                        register_msg = RegisterMessage(**data)
                        logger.info(f"树莓派 {client_ip}:{client_port} 重新注册")
                        # 发送注册成功消息
                        register_success_msg = {
                            "type": "register_success"
                        }
                        await websocket.send_json(register_success_msg)
                        logger.info(f"发送注册成功消息给树莓派 {client_ip}:{client_port}")
                    elif message_type == "status":
                        logger.info(f"处理树莓派 {client_ip}:{client_port} 的状态消息")
                        await handle_status_message(data)
                        await router.route_message("robot", data)
                    elif message_type == "webrtc_signaling":
                        logger.info(f"处理树莓派 {client_ip}:{client_port} 的 WebRTC 信令消息")
                        await handle_webrtc_signaling_message(data)
                        await router.route_message("robot", data)
                    else:
                        logger.warning(f"收到树莓派 {client_ip}:{client_port} 的未知消息类型: {message_type}")
                except Exception as e:
                    logger.error(f"处理树莓派 {client_ip}:{client_port} 消息时出错: {str(e)}")
                    error_msg = ErrorMessage(
                        type="error",
                        message=f"消息格式非法: {str(e)}"
                    )
                    await manager.send_to_pi(error_msg.model_dump())
            except asyncio.TimeoutError:
                # 超时后继续循环，保持连接活跃
                logger.debug(f"树莓派 {client_ip}:{client_port} 消息接收超时，保持连接活跃")
                pass
    except WebSocketDisconnect:
        logger.info(f"树莓派 {client_ip}:{client_port} 连接断开")
        manager.disconnect(websocket)
    except Exception as e:
        # 妥善处理错误，避免因小错误而关闭连接
        logger.error(f"树莓派 {client_ip}:{client_port} 连接处理时出错: {str(e)}")
        try:
            error_msg = ErrorMessage(
                type="error",
                message=f"处理消息时出错: {str(e)}"
            )
            await manager.send_to_pi(error_msg.model_dump())
        except:
            pass
        finally:
            manager.disconnect(websocket)
