/**
 * 全局常量 — 对应 Vue 前端的 .env.local 配置
 */

// Python FastAPI 后端地址（Pi）— WebSocket + MJPEG
// 修改为你的 Pi 实际 IP 地址
export const BACKEND_HTTP_URL: string = 'http://192.168.137.90:8080'

// Java Spring Boot 后端地址（PC）— REST API
// 修改为你的 PC 实际 IP 地址
export const JAVA_API_URL: string = 'http://192.168.137.1:8090'

// WebSocket 路径
export function getWsUrl(): string {
  const wsBase: string = BACKEND_HTTP_URL.replace(/^http/, 'ws').replace(/\/$/, '')
  return wsBase + '/ws'
}

// 视频单帧快照路径（鸿蒙不支持 MJPEG 流，改用帧轮询）
export function getVideoStreamUrl(): string {
  return BACKEND_HTTP_URL.replace(/\/$/, '') + '/video/frame'
}

// 照片存储路径
export function getPhotoUrl(filename: string): string {
  return BACKEND_HTTP_URL.replace(/\/$/, '') + '/photos/' + filename
}

// WebSocket 配置
export const WS_HEARTBEAT_INTERVAL: number = 30000   // 心跳间隔 30s
export const WS_MAX_RECONNECT: number = 5             // 最大重连次数
export const WS_RECONNECT_DELAY: number = 1500        // 重连延迟 1.5s

// 控制配置
export const SERVO_STEP: number = 5                   // 舵机步进角度
export const COMMAND_INTERVAL: number = 100           // 持续指令发送间隔 100ms
