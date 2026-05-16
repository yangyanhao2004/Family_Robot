export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

export interface RobotStatus {
  battery: number
  isRunning: boolean
  signalStrength: number
}

export type RobotCommand =
  | 'forward'
  | 'backward'
  | 'left'
  | 'right'
  | 'stop'

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
  autoSave: boolean
  firmwareVersion: string
  serialNumber: string
}
