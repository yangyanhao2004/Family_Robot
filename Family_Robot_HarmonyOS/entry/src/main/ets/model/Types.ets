/**
 * 类型定义 — 与 Vue Web 前端 types/index.ts 保持一致
 */

// 连接状态
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

// 通知
export interface Notification {
  id: string
  message: string
  type: 'info' | 'success' | 'error'
}

// 用户资料
export interface UserProfile {
  name: string
  email: string
  role: string
  avatar: string
  lastLogin: string
}

// 相册照片
export interface AlbumPhoto {
  id: string
  url: string
  date: string
}

// 机器人设置
export interface RobotSettings {
  firmwareVersion: string
  serialNumber: string
}

// 机器人指令类型
export type RobotCommand =
  | 'forward' | 'backward' | 'left' | 'right' | 'stop'
  | 'take_photo' | 'servo1' | 'servo2'
  | 'speed_low' | 'speed_medium' | 'speed_high'

// 聊天消息
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  action?: 'chat_reply' | 'control_robot' | 'set_reminder'
  data?: Record<string, Object>
  timestamp: number
}

// AI 聊天回复
export interface AIChatResponse {
  text: string
  action: 'chat_reply' | 'control_robot' | 'set_reminder'
  data?: Record<string, Object>
}

// 提醒 DTO
export interface ReminderDto {
  id: number
  text: string
  scheduledTime: string
  method: 'EMAIL' | 'VOICE'
  email: string | null
  enabled: boolean
  sent: boolean
}

// WebSocket 消息
export interface WebSocketMessage {
  type: string
  payload?: Record<string, Object>
  data?: Record<string, Object>
  message?: string
  role?: string
}

// WebRTC 信令（一期暂不使用，保留类型定义）
export interface WebRTCSignalPayload {
  type: 'offer' | 'answer' | 'candidate'
  offer?: Record<string, Object>
  answer?: Record<string, Object>
  candidate?: Record<string, Object>
}

// 机器人状态
export interface RobotStatus {
  battery: number | null
  isRunning: boolean
  temperature: number | null
  signalStrength: number | null
}
