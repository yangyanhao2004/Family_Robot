from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from core.connection_manager import manager
from core.rtc_service import rtc_service
from models.common import BaseMessage, RegisterMessage, ErrorMessage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('backend')



app = FastAPI(
    title="家庭机器人后端服务",
    description="提供 WebSocket 通信和视频流接口",
    version="1.0.0",
    # 增加 WebSocket 最大消息大小到 5MB
    websocket_max_message_size=5 * 1024 * 1024
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio

async def websocket_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info(f"接受来自 {client_ip}:{client_port} 的 WebSocket 连接")
    await manager.connect(websocket)
    
    try:
        # 等待客户端发送 register 消息
        try:
            logger.info(f"等待 {client_ip}:{client_port} 发送注册消息...")
            data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            logger.info(f"收到 {client_ip}:{client_port} 的消息: {data}")
            
            base_msg = BaseMessage(**data)
            
            if base_msg.type == "register":
                register_msg = RegisterMessage(**data)
                role = register_msg.role
                logger.info(f"{client_ip}:{client_port} 注册为 {role} 角色")
                
                # 发送注册成功消息
                register_success_msg = {
                    "type": "register_success"
                }
                await websocket.send_json(register_success_msg)
                logger.info(f"发送注册成功消息给 {client_ip}:{client_port}")
                
                if role == "web":
                    logger.info(f"将 {client_ip}:{client_port} 路由到前端处理端点")
                    from front.ws_front import websocket_front_endpoint
                    await websocket_front_endpoint(websocket)
                elif role == "robot":
                    logger.info(f"将 {client_ip}:{client_port} 路由到树莓派处理端点")
                    from pi.ws_pi import websocket_pi_endpoint
                    await websocket_pi_endpoint(websocket)
                else:
                    logger.warning(f"{client_ip}:{client_port} 注册了无效角色: {role}")
                    error_msg = ErrorMessage(
                        type="error",
                        message="无效的角色"
                    )
                    await websocket.send_json(error_msg.model_dump())
                    await websocket.close()
            else:
                logger.warning(f"{client_ip}:{client_port} 未发送注册消息，消息类型: {base_msg.type}")
                error_msg = ErrorMessage(
                    type="error",
                    message="请先发送 register 消息"
                )
                await websocket.send_json(error_msg.model_dump())
                await websocket.close()
        except asyncio.TimeoutError:
            # 超时后关闭连接
            logger.warning(f"{client_ip}:{client_port} 注册消息超时，关闭连接")
            await websocket.close()
        except WebSocketDisconnect:
            # 直接处理断开连接，不发送消息
            logger.info(f"{client_ip}:{client_port} 主动断开连接")
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"处理 {client_ip}:{client_port} 消息时出错: {str(e)}")
            try:
                error_msg = ErrorMessage(
                    type="error",
                    message=f"消息处理错误: {str(e)}"
                )
                await websocket.send_json(error_msg.model_dump())
                await websocket.close()
            except:
                manager.disconnect(websocket)
    except WebSocketDisconnect:
        # 直接处理断开连接，不发送消息
        logger.info(f"{client_ip}:{client_port} 连接断开")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"{client_ip}:{client_port} 连接处理时出错: {str(e)}")
        try:
            error_msg = ErrorMessage(
                type="error",
                message=f"连接错误: {str(e)}"
            )
            await websocket.send_json(error_msg.model_dump())
            await websocket.close()
        except:
            # 如果发送消息失败（连接已关闭），直接断开连接
            manager.disconnect(websocket)

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    # 添加详细的连接日志
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info(f"收到来自 {client_ip}:{client_port} 的 WebSocket 连接请求")
    try:
        await websocket_endpoint(websocket)
    finally:
        logger.info(f"来自 {client_ip}:{client_port} 的 WebSocket 连接已关闭")

@app.get("/video/stream")
async def video_stream():
    raise HTTPException(status_code=501, detail="Not Implemented")

@app.get("/")
async def root():
    return {"message": "家庭机器人后端服务运行中"}



@app.websocket("/ws/rtc")
async def websocket_rtc_endpoint(websocket: WebSocket):
    """
    RTC WebSocket 端点
    处理WebRTC信令消息，支持实时音频通信
    """
    client_ip = websocket.client.host
    client_port = websocket.client.port
    logger.info(f"收到来自 {client_ip}:{client_port} 的 RTC WebSocket 连接请求")
    
    # 等待客户端发送注册消息，获取客户端ID
    try:
        # 接收客户端注册消息
        data = await websocket.receive_json()
        logger.info(f"收到来自 {client_ip}:{client_port} 的 RTC 注册消息: {data}")
        
        if data.get('type') == 'register':
            client_id = data.get('client_id')
            if not client_id:
                logger.error("RTC 注册缺少 client_id")
                await websocket.close(code=1008, reason="缺少 client_id")
                return
            
            # 接受连接并注册到RTC服务
            await rtc_service.connect(websocket, client_id)
            
            # 发送注册成功消息
            await websocket.send_json({
                "type": "register_success",
                "client_id": client_id
            })
            
            # 处理后续信令消息
            while True:
                try:
                    data = await websocket.receive_json()
                    await rtc_service.handle_signaling(client_id, data)
                except WebSocketDisconnect:
                    logger.info(f"RTC客户端 {client_id} 主动断开连接")
                    rtc_service.disconnect(client_id)
                    break
                except Exception as e:
                    logger.error(f"处理RTC客户端 {client_id} 消息时出错: {str(e)}")
                    # 发送错误消息但不关闭连接
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"处理消息失败: {str(e)}"
                        })
                    except:
                        # 如果发送失败，说明连接已关闭
                        rtc_service.disconnect(client_id)
                        break
        else:
            logger.error(f"RTC 连接缺少注册消息，消息类型: {data.get('type')}")
            await websocket.close(code=1008, reason="缺少注册消息")
    except WebSocketDisconnect:
        logger.info(f"RTC连接 {client_ip}:{client_port} 主动断开")
    except Exception as e:
        logger.error(f"处理RTC连接 {client_ip}:{client_port} 时出错: {str(e)}")
        try:
            await websocket.close(code=1011, reason=f"处理错误: {str(e)}")
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
