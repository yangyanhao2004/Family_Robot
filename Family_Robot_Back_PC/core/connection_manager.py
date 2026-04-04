import logging
from fastapi import WebSocket
from typing import Optional

# 配置日志
logger = logging.getLogger('backend.connection')

class ConnectionManager:
    def __init__(self):
        self.web_connection: Optional[WebSocket] = None
        self.pi_connection: Optional[WebSocket] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        client_ip = websocket.client.host
        client_port = websocket.client.port
        logger.info(f"接受连接: {client_ip}:{client_port}")

    def register_web(self, websocket: WebSocket):
        client_ip = websocket.client.host
        client_port = websocket.client.port
        logger.info(f"注册前端连接: {client_ip}:{client_port}")
        self.web_connection = websocket

    def register_pi(self, websocket: WebSocket):
        client_ip = websocket.client.host
        client_port = websocket.client.port
        logger.info(f"注册树莓派连接: {client_ip}:{client_port}")
        self.pi_connection = websocket

    def disconnect(self, websocket: WebSocket):
        client_ip = websocket.client.host
        client_port = websocket.client.port
        if websocket == self.web_connection:
            logger.info(f"断开前端连接: {client_ip}:{client_port}")
            self.web_connection = None
        elif websocket == self.pi_connection:
            logger.info(f"断开树莓派连接: {client_ip}:{client_port}")
            self.pi_connection = None

    async def send_to_web(self, message: dict):
        if self.web_connection:
            try:
                client_ip = self.web_connection.client.host
                client_port = self.web_connection.client.port
                logger.debug(f"发送消息到前端 {client_ip}:{client_port}: {message}")
                await self.web_connection.send_json(message)
            except Exception as e:
                logger.error(f"发送消息到前端时出错: {str(e)}")
                self.disconnect(self.web_connection)

    async def send_to_pi(self, message: dict):
        if self.pi_connection:
            try:
                client_ip = self.pi_connection.client.host
                client_port = self.pi_connection.client.port
                logger.debug(f"发送消息到树莓派 {client_ip}:{client_port}: {message}")
                await self.pi_connection.send_json(message)
            except Exception as e:
                logger.error(f"发送消息到树莓派时出错: {str(e)}")
                self.disconnect(self.pi_connection)

    async def broadcast(self, message: dict):
        logger.debug(f"广播消息: {message}")
        if self.web_connection:
            await self.send_to_web(message)
        if self.pi_connection:
            await self.send_to_pi(message)

    def is_web_connected(self) -> bool:
        connected = self.web_connection is not None
        logger.debug(f"前端连接状态: {connected}")
        return connected

    def is_pi_connected(self) -> bool:
        connected = self.pi_connection is not None
        logger.debug(f"树莓派连接状态: {connected}")
        return connected

manager = ConnectionManager()
