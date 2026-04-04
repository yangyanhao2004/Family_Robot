// src/services/websocket.ts
// WebSocket 通信服务（毕业设计工程最终版）
// 兼容：Vue 3 + Vite 5 + Node 18

import { useRobotStore } from '../store/robotStore';

/* ===========================
   类型定义
=========================== */

// 机器人控制指令
export type RobotCommand =
  | 'forward'
  | 'backward'
  | 'left'
  | 'right'
  | 'stop'
  | 'light_on'
  | 'light_off';

// 后端消息格式（可扩展）
interface WebSocketMessage {
  type: 'command' | 'status' | 'error' | 'success' | 'register' | 'register_success' | 'heartbeat';
  payload?: any;
  message?: string;
  role?: string;
}

/* ===========================
   WebSocket Service
=========================== */

class WebSocketService {
  private socket: WebSocket | null = null;
  private url: string;

  // 重连控制
  private reconnectCount = 0;
  private readonly maxReconnect = 5;
  private readonly reconnectDelay = 1500;
  private manualClose = false;

  // 注册状态
  private isRegistered = false;

  // 心跳控制
  private heartbeatInterval: number | null = null;
  private readonly HEARTBEAT_INTERVAL = 30000; // 30秒

  constructor(url = 'ws://localhost:8080/ws') {
    this.url = url;
  }

  /* ===========================
     连接管理
  =========================== */

  connect(customUrl?: string): void {
    if (customUrl) this.url = customUrl;

    if (this.socket) return;

    this.manualClose = false;
    const store = useRobotStore();

    try {
      console.log('[WebSocket] connecting to:', this.url);
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this.reconnectCount = 0;
        this.isRegistered = false;
        store.updateConnectionStatus(true, null);
        console.log('[WebSocket] connected');
        
        // 连接建立后立即发送注册消息
        const registerMsg = JSON.stringify({
          type: 'register',
          role: 'web'
        });
        console.log('[WebSocket] sending register message:', registerMsg);
        if (this.socket) {
          this.socket.send(registerMsg);
        }
        
        // 启动心跳
        this.startHeartbeat();
      };

      this.socket.onmessage = (event) => {
        console.log('[WebSocket] received message:', event.data);
        this.handleMessage(event.data);
      };

      this.socket.onerror = (error) => {
        console.error('[WebSocket] error:', error);
        store.updateConnectionStatus(false, 'WebSocket 连接错误');
      };

      this.socket.onclose = (event) => {
        console.log('[WebSocket] connection closed:', event.code, event.reason);
        store.updateConnectionStatus(false, `连接已断开 (${event.code}: ${event.reason})`);
        this.socket = null;
        
        // 清除心跳
        if (this.heartbeatInterval) {
          clearInterval(this.heartbeatInterval);
          this.heartbeatInterval = null;
        }

        if (!this.manualClose) {
          console.log('[WebSocket] attempting to reconnect...');
          this.attemptReconnect();
        }
      };
    } catch (err) {
      console.error('[WebSocket] connection failed:', err);
      store.updateConnectionStatus(false, 'WebSocket 初始化失败');
    }
  }

  disconnect(): void {
    this.manualClose = true;

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    // 清除心跳
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    const store = useRobotStore();
    store.updateConnectionStatus(false, '已手动断开');
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  /* ===========================
     指令发送
  =========================== */

  sendCommand(command: RobotCommand): void {
    if (!this.isConnected() || !this.socket) return;

    // 确保只有在注册成功后才发送命令消息
    if (!this.isRegistered) {
      console.warn('[WebSocket] Not registered, cannot send command');
      return;
    }

    const msg: WebSocketMessage = {
      type: 'command',
      payload: { command },
    };

    this.socket.send(JSON.stringify(msg));
  }

  /* ===========================
     内部方法（⚠ 必须存在）
  =========================== */

  // 启动心跳
  private startHeartbeat(): void {
    console.log('[WebSocket] starting heartbeat');
    this.heartbeatInterval = window.setInterval(() => {
      if (this.isConnected() && this.socket) {
        const heartbeatMsg = JSON.stringify({ type: 'heartbeat' });
        console.log('[WebSocket] sending heartbeat:', heartbeatMsg);
        this.socket.send(heartbeatMsg);
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  // ✅ 修复：handleMessage 不存在
  private handleMessage(raw: string): void {
    const store = useRobotStore();

    try {
      const data = JSON.parse(raw);

      // 处理注册成功响应
      if (data.type === 'register_success') {
        this.isRegistered = true;
        console.log('[WebSocket] 注册成功');
      }

      if (data.type === 'status' && data.payload) {
        store.updateRobotStatus(data.payload);
      }

      if (data.type === 'error') {
        store.updateConnectionStatus(false, data.message || '后端错误');
      }
    } catch {
      console.warn('[WebSocket] 非 JSON 消息:', raw);
    }
  }

  // ✅ 修复：attemptReconnect 不存在
  private attemptReconnect(): void {
    if (this.reconnectCount >= this.maxReconnect) return;

    this.reconnectCount++;
    console.log(`[WebSocket] 重连中 (${this.reconnectCount})`);

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
  }
}

/* ===========================
   单例导出
=========================== */

const webSocketService = new WebSocketService();
export default webSocketService;