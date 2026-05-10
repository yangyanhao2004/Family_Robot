import logging
from fastapi import WebSocket
from typing import Optional

logger = logging.getLogger('backend.connection')

class ConnectionManager:
    def __init__(self):
        self.web_connection: Optional[WebSocket] = None
        self.pi_connection: Optional[WebSocket] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        logger.info(f"Accept connection: {websocket.client.host}:{websocket.client.port}")

    def register_web(self, websocket: WebSocket):
        logger.info(f"Register web: {websocket.client.host}:{websocket.client.port}")
        self.web_connection = websocket

    def register_pi(self, websocket: WebSocket):
        logger.info(f"Register Pi: {websocket.client.host}:{websocket.client.port}")
        self.pi_connection = websocket

    def disconnect(self, websocket: WebSocket):
        if websocket == self.web_connection:
            logger.info(f"Disconnect web: {websocket.client.host}:{websocket.client.port}")
            self.web_connection = None
        elif websocket == self.pi_connection:
            logger.info(f"Disconnect Pi: {websocket.client.host}:{websocket.client.port}")
            self.pi_connection = None

    async def send_to_web(self, message: dict):
        if self.web_connection:
            try:
                await self.web_connection.send_json(message)
            except Exception as e:
                logger.error(f"Send to web failed: {e}")
                self.disconnect(self.web_connection)

    async def send_to_pi(self, message: dict):
        if self.pi_connection:
            try:
                await self.pi_connection.send_json(message)
            except Exception as e:
                logger.error(f"Send to Pi failed: {e}")
                self.disconnect(self.pi_connection)

    async def broadcast(self, message: dict):
        if self.web_connection:
            await self.send_to_web(message)
        if self.pi_connection:
            await self.send_to_pi(message)

    def is_web_connected(self) -> bool:
        return self.web_connection is not None

    def is_pi_connected(self) -> bool:
        return self.pi_connection is not None

manager = ConnectionManager()
