import logging
from typing import Dict, Any, Set
from fastapi import WebSocket

logger = logging.getLogger('rtc')

class RTCService:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"RTC client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"RTC client {client_id} disconnected")

        for room_id, clients in list(self.rooms.items()):
            if client_id in clients:
                clients.remove(client_id)
                if not clients:
                    del self.rooms[room_id]
                logger.info(f"RTC client {client_id} removed from room {room_id}")

    async def handle_signaling(self, client_id: str, data: Dict[str, Any]):
        try:
            signaling_type = data.get('type')
            room_id = data.get('room_id')
            target_id = data.get('target_id')

            if signaling_type == 'join_room':
                await self._handle_join_room(client_id, room_id)
            elif signaling_type in ('offer', 'answer', 'candidate'):
                await self._forward_signaling(client_id, data, room_id, target_id)
            elif signaling_type == 'leave_room':
                await self._handle_leave_room(client_id, room_id)
            else:
                if client_id in self.active_connections:
                    await self.active_connections[client_id].send_json({
                        "type": "error",
                        "message": f"Unknown signaling type: {signaling_type}"
                    })
        except Exception as e:
            logger.error(f"RTC signaling failed: {e}")
            if client_id in self.active_connections:
                await self.active_connections[client_id].send_json({
                    "type": "error",
                    "message": f"Signaling failed: {e}"
                })

    async def _handle_join_room(self, client_id: str, room_id: str):
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(client_id)

        for other_id in self.rooms[room_id]:
            if other_id != client_id and other_id in self.active_connections:
                await self.active_connections[other_id].send_json({
                    "type": "user_joined", "client_id": client_id, "room_id": room_id
                })

        await self.active_connections[client_id].send_json({
            "type": "join_success", "room_id": room_id, "clients": list(self.rooms[room_id])
        })

    async def _handle_leave_room(self, client_id: str, room_id: str):
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].remove(client_id)
            for other_id in self.rooms[room_id]:
                if other_id in self.active_connections:
                    await self.active_connections[other_id].send_json({
                        "type": "user_left", "client_id": client_id, "room_id": room_id
                    })
            if not self.rooms[room_id]:
                del self.rooms[room_id]

        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": "leave_success", "room_id": room_id
            })

    async def _forward_signaling(self, client_id: str, data: Dict[str, Any],
                                  room_id: str, target_id: str):
        if target_id:
            if target_id in self.active_connections:
                await self.active_connections[target_id].send_json({**data, "from_id": client_id})
            else:
                await self.active_connections[client_id].send_json({
                    "type": "error", "message": f"Target {target_id} not found"
                })
        elif room_id:
            if room_id in self.rooms:
                for other_id in self.rooms[room_id]:
                    if other_id != client_id and other_id in self.active_connections:
                        await self.active_connections[other_id].send_json({**data, "from_id": client_id})
            else:
                await self.active_connections[client_id].send_json({
                    "type": "error", "message": f"Room {room_id} not found"
                })
        else:
            await self.active_connections[client_id].send_json({
                "type": "error", "message": "Signaling missing target info"
            })

rtc_service = RTCService()
