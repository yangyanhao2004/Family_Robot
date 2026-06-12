/**
 * 主控面板 — 对齐 Web 前端 DashboardView.vue + MainLayout.vue
 */
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'
import { webSocketService, ConnectionCallback } from '../services/WebSocketService'
import { authManager } from '../services/AuthManager'
import { api } from '../services/ApiService'
import { StatusBar } from '../components/StatusBar'
import { VideoStream } from '../components/VideoStream'
import { DPadControl } from '../components/DPadControl'
import { PTZControl } from '../components/PTZControl'
import { RobotCommand, RobotStatus, WebSocketMessage } from '../model/Types'
import { getVideoStreamUrl } from '../common/Constants'

@Entry
@Component
struct DashboardPage {
  @State connectionStatus: string = 'disconnected'
  @State connectionError: string = ''
  @State robotStatus: RobotStatus = {
    battery: null,
    isRunning: false,
    temperature: null,
    signalStrength: null
  }
  @State speedLevel: string = 'medium'
  @State videoUrl: string = getVideoStreamUrl()
  @State isTriggeringFall: boolean = false
  private wsMsgListener: (msg: WebSocketMessage) => void = (_msg: WebSocketMessage) => {}

  aboutToAppear(): void {
    let cb: ConnectionCallback = {
      onStatusChanged: (status: string, error?: string) => {
        this.connectionStatus = status
        if (error) this.connectionError = error
      },
      onRobotStatusUpdated: (status: RobotStatus) => {
        this.robotStatus = status
      },
      onError: (message: string) => {}
    }
    webSocketService.setCallback(cb)

    this.wsMsgListener = (msg: WebSocketMessage) => {
      if (msg.type === 'photo_captured' && msg.payload) {
        let payload: Record<string, Object> = msg.payload
        let filename: string = (payload['filename'] as string) || ''
        let url: string = (payload['url'] as string) || ''
        this.onPhotoCaptured(url, filename)
      }
    }
    webSocketService.addMessageListener(this.wsMsgListener)
    webSocketService.connect()
  }

  aboutToDisappear(): void {
    webSocketService.removeMessageListener(this.wsMsgListener)
    webSocketService.disconnect()
  }

  build() {
    Column() {
      // 顶部状态栏
      StatusBar({
        connectionStatus: this.connectionStatus,
        robotStatus: this.robotStatus,
        speedLevel: this.speedLevel,
        onSpeedChange: (cmd: RobotCommand) => {
          this.speedLevel = cmd === 'speed_low' ? 'low'
            : cmd === 'speed_medium' ? 'medium' : 'high'
          webSocketService.sendCommand(cmd)
        }
      })

      // 主区域：视频 + 控制面板
      Row() {
        // 左侧：视频区域
        Stack() {
          VideoStream({ streamUrl: this.videoUrl })
            .width('100%').height('100%')

          // 拍照按钮（悬浮）
          Button() { Text('📷').fontSize(20) }
            .width(48).height(48)
            .backgroundColor('#2563EB').borderRadius(24)
            .position({ right: 16, bottom: 16 })
            .onClick(() => {
              if (webSocketService.isConnected()) {
                webSocketService.sendCommand('take_photo')
              }
            })
        }
        .layoutWeight(1)
        .backgroundColor('#0D0D0D')

        // 右侧：控制面板
        Column({ space: 16 }) {
          // 连接按钮
          this.ConnectionButton()

          // 运动方向键
          DPadControl({
            disabled: this.connectionStatus !== 'connected',
            onCommand: (cmd: RobotCommand, angle?: number) => {
              webSocketService.sendCommand(cmd, angle)
            }
          })

          // 云台控制
          PTZControl({
            disabled: this.connectionStatus !== 'connected',
            onCommand: (cmd: RobotCommand, angle: number) => {
              webSocketService.sendCommand(cmd, angle)
            }
          })

          // 🏥 模拟摔倒
          Button(this.isTriggeringFall ? '🏥 触发中...' : '🏥 模拟摔倒检测')
            .fontSize(13).fontColor('#FFFFFF')
            .width('100%').height(40)
            .backgroundColor('#dc2626').borderRadius(12)
            .enabled(!this.isTriggeringFall)
            .onClick(() => { this.triggerFallAlert() })

          // AI对话 + 相册
          Row({ space: 8 }) {
            Button('💬 AI对话')
              .fontSize(13).fontColor('#FFFFFF')
              .layoutWeight(1).height(40)
              .backgroundColor('#222222').borderRadius(12)
              .onClick(() => router.pushUrl({ url: 'pages/AIChatPage' }))
            Button('🖼 相册')
              .fontSize(13).fontColor('#FFFFFF')
              .layoutWeight(1).height(40)
              .backgroundColor('#222222').borderRadius(12)
              .onClick(() => router.pushUrl({ url: 'pages/AlbumPage' }))
          }.width('100%')

          // 提醒 + 设置 + 个人
          Row({ space: 8 }) {
            Button('⏰').fontSize(16)
              .layoutWeight(1).height(36)
              .backgroundColor('#222222').borderRadius(10)
              .onClick(() => router.pushUrl({ url: 'pages/ReminderPage' }))
            Button('⚙️').fontSize(16)
              .layoutWeight(1).height(36)
              .backgroundColor('#222222').borderRadius(10)
              .onClick(() => router.pushUrl({ url: 'pages/SettingsPage' }))
            Button('👤').fontSize(16)
              .layoutWeight(1).height(36)
              .backgroundColor('#222222').borderRadius(10)
              .onClick(() => router.pushUrl({ url: 'pages/ProfilePage' }))
          }.width('100%')
        }
        .width(320).padding(12)
        .backgroundColor('#141414')
        .border({ width: { left: 1 }, color: '#2A2A2A' })
      }
      .layoutWeight(1)
    }
    .width('100%').height('100%')
    .backgroundColor('#1A1A1A')
  }

  @Builder
  ConnectionButton() {
    Row() {
      // 连接状态圆点
      Circle({ width: 8, height: 8 })
        .fill(this.connectionStatus === 'connected' ? '#22C55E'
          : this.connectionStatus === 'connecting' ? '#3B82F6' : '#71717A')
        .margin({ right: 8 })

      Text(this.connectionStatus === 'connected' ? '已连接'
        : this.connectionStatus === 'connecting' ? '连接中...' : '未连接')
        .fontSize(13).fontColor('#D1D5DB')

      Blank()

      Button(this.connectionStatus === 'connected' ? '断开' : '连接')
        .fontSize(12).height(30).padding({ left: 14, right: 14 })
        .fontColor('#FFFFFF')
        .backgroundColor(this.connectionStatus === 'connected' ? '#DC2626' : '#2563EB')
        .borderRadius(10)
        .enabled(this.connectionStatus !== 'connecting')
        .onClick(() => {
          if (this.connectionStatus === 'connected') {
            webSocketService.disconnect()
          } else {
            webSocketService.connect()
          }
        })
    }
    .width('100%').height(40)
    .padding({ left: 12, right: 12 })
    .borderRadius(12)
    .backgroundColor('#1E1E1E')
  }

  private async triggerFallAlert(): Promise<void> {
    this.isTriggeringFall = true
    try {
      let userId: number = authManager.getUserIdFromToken() || 1
      await api.triggerFallAlert(userId, '用户')
      promptAction.showToast({ message: '已触发摔倒告警！邮件已发送', duration: 3000 })
    } catch (err) {
      promptAction.showToast({ message: '触发失败: ' + (err as Error).message, duration: 2000 })
    } finally {
      this.isTriggeringFall = false
    }
  }

  private async onPhotoCaptured(url: string, filename: string): Promise<void> {
    try {
      await api.addPhoto(url, filename)
    } catch (_err) {}
  }
}
