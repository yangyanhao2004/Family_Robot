/**
 * 速度选择器组件（独立使用版本）
 * 可在 DashboardPage 以外的地方使用
 */
import { RobotCommand } from '../model/Types'

@Component
export struct SpeedSelector {
  @Link speedLevel: string
  @Prop disabled: boolean = false
  onSpeedChange?: (command: RobotCommand) => void

  build() {
    Row({ space: 6 }) {
      SpeedSelButton({
        label: '低',
        active: this.speedLevel === 'low',
        activeColor: '#10b981',
        disabled: this.disabled,
        onClick: () => {
          this.speedLevel = 'low'
          if (this.onSpeedChange) this.onSpeedChange('speed_low')
        }
      })
      SpeedSelButton({
        label: '中',
        active: this.speedLevel === 'medium',
        activeColor: '#f59e0b',
        disabled: this.disabled,
        onClick: () => {
          this.speedLevel = 'medium'
          if (this.onSpeedChange) this.onSpeedChange('speed_medium')
        }
      })
      SpeedSelButton({
        label: '高',
        active: this.speedLevel === 'high',
        activeColor: '#ef4444',
        disabled: this.disabled,
        onClick: () => {
          this.speedLevel = 'high'
          if (this.onSpeedChange) this.onSpeedChange('speed_high')
        }
      })
    }
  }
}

@Component
struct SpeedSelButton {
  @Prop label: string = ''
  @Prop active: boolean = false
  @Prop activeColor: string = '#10b981'
  @Prop disabled: boolean = false
  onClick?: () => void

  build() {
    Button(this.label)
      .fontSize(12)
      .fontColor(this.active ? '#fff' : '#888')
      .height(30)
      .width(38)
      .padding(0)
      .backgroundColor(this.active ? this.activeColor : 'transparent')
      .borderRadius(6)
      .border({ width: 1, color: this.active ? this.activeColor : '#444' })
      .enabled(!this.disabled)
      .onClick(() => { if (this.onClick) this.onClick() })
  }
}
