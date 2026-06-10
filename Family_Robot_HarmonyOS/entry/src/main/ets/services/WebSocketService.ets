/**
 * WebSocket 服务 — 对应 Vue 前端 websocket.ts
 * 对接 Python FastAPI 后端 (Port 8080) /ws
 */
import webSocket from '@ohos.net.webSocket'
import { authManager } from './AuthManager'
import { getWsUrl, WS_HEARTBEAT_INTERVAL, WS_MAX_RECONNECT, WS_RECONNECT_DELAY } from '../common/Constants'
import {
  WebSocketMessage,
  RobotCommand,
  WebRTCSignalPayload,
  RobotStatus
} from '../model/Types'

// 内部消息类型
interface WsRawMessage {
  type: string
  role?: string
  user_id?: number
  payload?: Record<string, Object>
  data?: Record<string, Object>
}

// 消息监听器类型
type MessageListener = (msg: WebSocketMessage) => void

// 回调接口
export interface ConnectionCallback {
  onStatusChanged: (status: string, error?: string) => void
  onRobotStatusUpdated: (status: RobotStatus) => void
  onError: (message: string) => void
}

class WebSocketService {
  private ws: webSocket.WebSocket | null = null
  private url: string
  private reconnectCount: number = 0
  private manualClose: boolean = false
  private isRegistered: boolean = false
  private heartbeatTimer: number | null = null
  private listeners: Set<MessageListener> = new Set()
  private callback: ConnectionCallback | null = null
  private connecting: boolean = false

  constructor(url?: string) {
    if (url) {
      this.url = url
    } else {
      this.url = getWsUrl()
    }
  }

  setCallback(cb: ConnectionCallback): void {
    this.callback = cb
  }

  /**
   * 连接到后端
   */
  connect(customUrl?: string): void {
    if (customUrl) {
      this.url = customUrl
    }
    if (this.ws !== null) {
      return
    }
    if (this.connecting) {
      return
    }

    this.manualClose = false
    this.connecting = true

    // 通知状态变更
    if (this.callback) {
      this.callback.onStatusChanged('connecting')
    }

    try {
      this.ws = webSocket.createWebSocket()

      // 连接打开
      this.ws.on('open', (err: Object, _value: Object) => {
        if (err) {
          this.connecting = false
          if (this.callback) {
            this.callback.onStatusChanged('disconnected', 'WebSocket 连接失败')
          }
          return
        }
        this.connecting = false
        this.reconnectCount = 0
        this.isRegistered = false

        // 注册为 web 客户端
        let userId: number = authManager.getUserIdFromToken()
        let regMsg: WsRawMessage = {
          type: 'register',
          role: 'web',
          user_id: userId
        }
        this.sendRaw(regMsg)

        // 启动心跳
        this.startHeartbeat()

        if (this.callback) {
          this.callback.onStatusChanged('connected')
        }
      })

      // 收到消息
      this.ws.on('message', (err: Object, value: Object) => {
        if (err) {
          return
        }
        if (typeof value === 'string') {
          this.handleMessage(value)
        }
      })

      // 连接关闭
      this.ws.on('close', (err: Object, _value: Object) => {
        this.connecting = false
        this.ws = null
        this.isRegistered = false
        this.stopHeartbeat()

        if (this.callback) {
          this.callback.onStatusChanged('disconnected', '连接已断开')
        }

        if (!this.manualClose) {
          this.attemptReconnect()
        }
      })

      // 发起连接
      let wsOptions: webSocket.WebSocketRequestOptions = {
        header: { 'User-Agent': 'FamilyRobot-HarmonyOS' }
      }
      this.ws.connect(this.url, wsOptions, (err: Object, _value: Object) => {
        if (err) {
          this.connecting = false
          this.ws = null
          if (this.callback) {
            this.callback.onStatusChanged('disconnected', '无法连接到服务器')
          }
          if (!this.manualClose) {
            this.attemptReconnect()
          }
        }
      })
    } catch (_err) {
      this.connecting = false
      if (this.callback) {
        this.callback.onStatusChanged('disconnected', 'WebSocket 初始化失败')
      }
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.manualClose = true
    this.stopHeartbeat()
    if (this.ws) {
      let closeOpts: Record<string, Object> = {}
      closeOpts['code'] = 1000 as Object
      closeOpts['reason'] = 'User disconnect' as Object
      this.ws.close(closeOpts, (_err: Object, _value: Object) => {
        // 忽略关闭结果
      })
      this.ws = null
    }
    this.isRegistered = false
    if (this.callback) {
      this.callback.onStatusChanged('disconnected', '手动断开')
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.isRegistered
  }

  // ==================== 消息监听器 ====================

  addMessageListener(listener: MessageListener): void {
    this.listeners.add(listener)
  }

  removeMessageListener(listener: MessageListener): void {
    this.listeners.delete(listener)
  }

  // ==================== 发送方法 ====================

  sendCommand(command: RobotCommand, angle?: number): void {
    if (!this.isConnected()) {
      return
    }
    let payload: Record<string, Object> = {
      'command': command
    }
    if (angle !== undefined) {
      payload['angle'] = angle
    }
    let msg: WsRawMessage = { type: 'command', payload: payload }
    this.sendRaw(msg)
  }

  sendAIChat(userId: number, message: string, email?: string): void {
    if (!this.isConnected()) {
      return
    }
    let payload: Record<string, Object> = {
      'user_id': userId,
      'message': message
    }
    if (email) {
      payload['email'] = email
    } else {
      payload['email'] = authManager.getUserEmailFromToken()
    }
    let msg: WsRawMessage = { type: 'ai_chat', payload: payload }
    this.sendRaw(msg)
  }

  sendAISessionEnd(userId: number): void {
    if (!this.isConnected()) {
      return
    }
    let payload: Record<string, Object> = { 'user_id': userId }
    let msg: WsRawMessage = { type: 'ai_session_end', payload: payload }
    this.sendRaw(msg)
  }

  sendWebRTCSignaling(data: WebRTCSignalPayload): void {
    if (!this.isConnected()) {
      return
    }
    let signalData: Record<string, Object> = {
      'type': data.type
    }
    if (data.offer) {
      signalData['offer'] = data.offer
    }
    if (data.answer) {
      signalData['answer'] = data.answer
    }
    if (data.candidate) {
      signalData['candidate'] = data.candidate
    }
    let msg: WsRawMessage = { type: 'webrtc_signaling', data: signalData }
    this.sendRaw(msg)
  }

  // ==================== 内部方法 ====================

  private sendRaw(message: WsRawMessage): void {
    if (!this.ws) {
      return
    }
    let jsonStr: string = JSON.stringify(message)
    this.ws.send(jsonStr, (err: Object, _value: Object) => {
      if (err) {
        // 发送失败，忽略
      }
    })
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws !== null) {
        let hbMsg: WsRawMessage = { type: 'heartbeat' }
        this.sendRaw(hbMsg)
      }
    }, WS_HEARTBEAT_INTERVAL)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private handleMessage(raw: string): void {
    let data: WebSocketMessage
    try {
      data = JSON.parse(raw) as WebSocketMessage
    } catch (_err) {
      return
    }

    // 内置消息路由
    if (data.type === 'register_success') {
      this.isRegistered = true
    } else if (data.type === 'status' && data.payload) {
      if (this.callback) {
        let payload: Record<string, Object> = data.payload
        this.callback.onRobotStatusUpdated({
          battery: payload['battery'] as number | null,
          isRunning: (payload['isRunning'] as boolean) ?? false,
          temperature: payload['temperature'] as number | null,
          signalStrength: payload['signalStrength'] as number | null
        })
      }
    } else if (data.type === 'error' && data.message) {
      if (this.callback) {
        this.callback.onError(data.message)
      }
    }

    // 通知所有外部监听器
    this.listeners.forEach((listener: MessageListener) => {
      try {
        listener(data)
      } catch (_err) {
        // 监听器异常不应中断消息处理
      }
    })
  }

  private attemptReconnect(): void {
    if (this.reconnectCount >= WS_MAX_RECONNECT) {
      return
    }
    this.reconnectCount++
    setTimeout(() => {
      this.connect()
    }, WS_RECONNECT_DELAY)
  }
}

// 全局单例
export const webSocketService: WebSocketService = new WebSocketService()
