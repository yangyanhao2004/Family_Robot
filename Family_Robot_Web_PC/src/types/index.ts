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
}
