/**
 * 状态栏 — 对齐 Web 前端 StatusBar.vue
 */
import { RobotStatus, RobotCommand } from '../model/Types'

@Component
export struct StatusBar {
  @Prop connectionStatus: string = 'disconnected'
  @Prop robotStatus: RobotStatus = {
    battery: null, isRunning: false, temperature: null, signalStrength: null
  }
  @Prop speedLevel: string = 'medium'
  onSpeedChange?: (command: RobotCommand) => void

  build() {
    Row() {
      this.ConnectionPill()
      Blank()
      this.SpeedButtons()
      Blank()
      this.SignalDisplay()
      this.BatteryDisplay()
    }
    .width('100%').height(50)
    .padding({ left: 12, right: 12 })
    .backgroundColor('#141414')
    .alignItems(VerticalAlign.Center)
  }

  @Builder
  ConnectionPill() {
    Row() {
      Circle({ width: 8, height: 8 })
        .fill(this.connectionStatus === 'connected' ? '#22C55E'
          : this.connectionStatus === 'connecting' ? '#3B82F6' : '#71717A')
        .margin({ right: 6 })
      Text(this.connectionStatus === 'connected' ? '已连接'
        : this.connectionStatus === 'connecting' ? '连接中' : '未连接')
        .fontSize(12).fontColor('#D1D5DB')
    }
    .padding({ left: 10, right: 10, top: 4, bottom: 4 })
    .borderRadius(20)
    .backgroundColor('#1E1E1E')
    .border({ width: 1, color: '#2A2A2A' })
  }

  @Builder
  SpeedButtons() {
    Row({ space: 2 }) {
      SpeedButton({
        label: '低', isActive: this.speedLevel === 'low',
        activeColor: '#10B981', isEnabled: this.connectionStatus === 'connected',
        onTap: () => { if (this.onSpeedChange) this.onSpeedChange('speed_low') }
      })
      SpeedButton({
        label: '中', isActive: this.speedLevel === 'medium',
        activeColor: '#F59E0B', isEnabled: this.connectionStatus === 'connected',
        onTap: () => { if (this.onSpeedChange) this.onSpeedChange('speed_medium') }
      })
      SpeedButton({
        label: '高', isActive: this.speedLevel === 'high',
        activeColor: '#EF4444', isEnabled: this.connectionStatus === 'connected',
        onTap: () => { if (this.onSpeedChange) this.onSpeedChange('speed_high') }
      })
    }
    .border({ width: 1, color: '#2A2A2A' })
    .borderRadius(6)
  }

  @Builder
  SignalDisplay() {
    Row() {
      Text(this.robotStatus.signalStrength !== null
        ? this.robotStatus.signalStrength!.toString() + '%' : '--')
        .fontSize(11).fontColor('#A3A3A6')
      Text(' 📶').fontSize(11)
    }.margin({ right: 12 })
  }

  @Builder
  BatteryDisplay() {
    Row() {
      Text(this.robotStatus.battery !== null
        ? this.robotStatus.battery!.toString() + '%' : '--')
        .fontSize(11).fontColor('#A3A3A6')
      Text(' 🔋').fontSize(11)
    }
  }
}

@Component
struct SpeedButton {
  @Prop label: string = ''
  @Prop isActive: boolean = false
  @Prop activeColor: string = '#10B981'
  @Prop isEnabled: boolean = true
  onTap?: () => void

  build() {
    Text(this.label)
      .fontSize(11).fontColor(this.isActive ? '#FFFFFF' : '#A3A3A6')
      .height(26).width(34)
      .textAlign(TextAlign.Center)
      .backgroundColor(this.isActive ? this.activeColor : '#222222')
      .enabled(this.isEnabled)
      .onClick(() => { if (this.onTap) this.onTap() })
  }
}
