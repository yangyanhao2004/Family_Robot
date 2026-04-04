import logging
import json
from typing import Dict, Any, Set
from fastapi import WebSocket

logger = logging.getLogger('rtc')

class RTCService:
    def __init__(self):
        """
        初始化RTC服务
        """
        # 存储活跃的WebSocket连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储房间信息
        self.rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        接受WebSocket连接
        
        Args:
            websocket: WebSocket连接
            client_id: 客户端ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"RTC客户端 {client_id} 已连接")
    
    def disconnect(self, client_id: str):
        """
        断开WebSocket连接
        
        Args:
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"RTC客户端 {client_id} 已断开")
        
        # 从所有房间中移除
        for room_id, clients in list(self.rooms.items()):
            if client_id in clients:
                clients.remove(client_id)
                if not clients:
                    del self.rooms[room_id]
                logger.info(f"RTC客户端 {client_id} 已从房间 {room_id} 移除")
    
    async def handle_signaling(self, client_id: str, data: Dict[str, Any]):
        """
        处理RTC信令消息
        
        Args:
            client_id: 客户端ID
            data: 信令数据
        """
        try:
            signaling_type = data.get('type')
            room_id = data.get('room_id')
            target_id = data.get('target_id')
            
            logger.info(f"处理RTC信令: {signaling_type} 来自 {client_id} 到房间 {room_id}")
            
            if signaling_type == 'join_room':
                # 加入房间
                await self._handle_join_room(client_id, room_id)
            elif signaling_type == 'offer' or signaling_type == 'answer' or signaling_type == 'candidate':
                # 转发信令
                await self._forward_signaling(client_id, data, room_id, target_id)
            elif signaling_type == 'leave_room':
                # 离开房间
                await self._handle_leave_room(client_id, room_id)
            else:
                logger.warning(f"未知的信令类型: {signaling_type}")
                await self.active_connections[client_id].send_json({
                    "type": "error",
                    "message": f"未知的信令类型: {signaling_type}"
                })
        
        except Exception as e:
            logger.error(f"处理RTC信令失败: {str(e)}")
            if client_id in self.active_connections:
                await self.active_connections[client_id].send_json({
                    "type": "error",
                    "message": f"处理信令失败: {str(e)}"
                })
    
    async def _handle_join_room(self, client_id: str, room_id: str):
        """
        处理加入房间请求
        
        Args:
            client_id: 客户端ID
            room_id: 房间ID
        """
        # 确保房间存在
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        # 添加客户端到房间
        self.rooms[room_id].add(client_id)
        logger.info(f"RTC客户端 {client_id} 加入房间 {room_id}")
        
        # 通知房间内其他客户端
        for other_client_id in self.rooms[room_id]:
            if other_client_id != client_id and other_client_id in self.active_connections:
                await self.active_connections[other_client_id].send_json({
                    "type": "user_joined",
                    "client_id": client_id,
                    "room_id": room_id
                })
        
        # 发送加入成功消息
        await self.active_connections[client_id].send_json({
            "type": "join_success",
            "room_id": room_id,
            "clients": list(self.rooms[room_id])
        })
    
    async def _handle_leave_room(self, client_id: str, room_id: str):
        """
        处理离开房间请求
        
        Args:
            client_id: 客户端ID
            room_id: 房间ID
        """
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].remove(client_id)
            logger.info(f"RTC客户端 {client_id} 离开房间 {room_id}")
            
            # 通知房间内其他客户端
            for other_client_id in self.rooms[room_id]:
                if other_client_id in self.active_connections:
                    await self.active_connections[other_client_id].send_json({
                        "type": "user_left",
                        "client_id": client_id,
                        "room_id": room_id
                    })
            
            # 如果房间为空，删除房间
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        # 发送离开成功消息
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": "leave_success",
                "room_id": room_id
            })
    
    async def _forward_signaling(self, client_id: str, data: Dict[str, Any], room_id: str, target_id: str):
        """
        转发信令消息
        
        Args:
            client_id: 客户端ID
            data: 信令数据
            room_id: 房间ID
            target_id: 目标客户端ID
        """
        if target_id:
            # 定向转发
            if target_id in self.active_connections:
                await self.active_connections[target_id].send_json({
                    **data,
                    "from_id": client_id
                })
                logger.info(f"RTC信令从 {client_id} 转发到 {target_id}")
            else:
                logger.warning(f"目标客户端 {target_id} 不存在")
                await self.active_connections[client_id].send_json({
                    "type": "error",
                    "message": f"目标客户端 {target_id} 不存在"
                })
        elif room_id:
            # 转发给房间内所有其他客户端
            if room_id in self.rooms:
                for other_client_id in self.rooms[room_id]:
                    if other_client_id != client_id and other_client_id in self.active_connections:
                        await self.active_connections[other_client_id].send_json({
                            **data,
                            "from_id": client_id
                        })
                logger.info(f"RTC信令从 {client_id} 广播到房间 {room_id}")
            else:
                logger.warning(f"房间 {room_id} 不存在")
                await self.active_connections[client_id].send_json({
                    "type": "error",
                    "message": f"房间 {room_id} 不存在"
                })
        else:
            logger.warning("信令缺少目标信息")
            await self.active_connections[client_id].send_json({
                "type": "error",
                "message": "信令缺少目标信息"
            })

# 全局RTC服务实例
rtc_service = RTCService()