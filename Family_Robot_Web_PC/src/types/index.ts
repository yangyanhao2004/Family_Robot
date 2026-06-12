export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

export interface Notification {
  id: string
  message: string
  type: 'info' | 'success' | 'error'
}

export interface UserProfile {
  name: string
  email: string
  avatar: string
  role: string
  lastLogin: string
}

export interface AlbumPhoto {
  id: string
  url: string
  date: string
}

export interface RobotSettings {
  firmwareVersion: string
  serialNumber: string
  emergencyContactName?: string
  emergencyContactEmail?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  action?: 'chat_reply' | 'control_robot' | 'set_reminder'
  data?: Record<string, any>
  timestamp: number
}

export interface AIChatResponse {
  text: string
  action: 'chat_reply' | 'control_robot' | 'set_reminder'
  data?: Record<string, any>
}

export interface ReminderDto {
  id: number
  text: string
  scheduledTime: string
  method: 'EMAIL' | 'VOICE'
  email: string | null
  enabled: boolean
  sent: boolean
}
