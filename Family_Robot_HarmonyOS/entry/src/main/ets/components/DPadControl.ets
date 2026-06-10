/**
 * 方向键控制盘 — 对齐 Web 前端 DashboardView.vue
 */
import { RobotCommand } from '../model/Types'
import { COMMAND_INTERVAL } from '../common/Constants'

@Component
export struct DPadControl {
  onCommand?: (command: RobotCommand, angle?: number) => void
  @Prop disabled: boolean = false
  @State private activeDirection: string = ''
  private commandTimer: number | null = null

  aboutToDisappear(): void { this.stopContinuousCommand() }

  build() {
    Column({ space: 8 }) {
      Text('移动控制')
        .fontSize(13).fontColor('#A3A3A6')
        .margin({ bottom: 2 })

      // ▲ forward
      DPadButton({
        symbol: '▲', btnDirection: 'forward',
        active: this.activeDirection === 'forward',
        disabled: this.disabled,
        onPress: () => this.startCommand('forward'),
        onRelease: () => this.stopCommand()
      })

      Row({ space: 8 }) {
        // ◀ left
        DPadButton({
          symbol: '◀', btnDirection: 'left',
          active: this.activeDirection === 'left',
          disabled: this.disabled,
          onPress: () => this.startCommand('left'),
          onRelease: () => this.stopCommand()
        })
        // ⏹ stop
        DPadButton({
          symbol: '⏹', btnDirection: 'stop',
          active: false, disabled: this.disabled, isStop: true,
          onPress: () => this.emitCommand('stop'),
          onRelease: () => {}
        })
        // ▶ right
        DPadButton({
          symbol: '▶', btnDirection: 'right',
          active: this.activeDirection === 'right',
          disabled: this.disabled,
          onPress: () => this.startCommand('right'),
          onRelease: () => this.stopCommand()
        })
      }

      // ▼ backward
      DPadButton({
        symbol: '▼', btnDirection: 'backward',
        active: this.activeDirection === 'backward',
        disabled: this.disabled,
        onPress: () => this.startCommand('backward'),
        onRelease: () => this.stopCommand()
      })
    }
    .padding(16).borderRadius(16)
    .backgroundColor('#141414')
    .border({ width: 1, color: '#2A2A2A' })
    .alignItems(HorizontalAlign.Center)
  }

  private startCommand(direction: string): void {
    if (this.disabled) return
    this.activeDirection = direction
    this.emitCommand(direction as RobotCommand)
    this.commandTimer = setInterval(() => {
      this.emitCommand(direction as RobotCommand)
    }, COMMAND_INTERVAL)
  }

  private stopCommand(): void {
    this.stopContinuousCommand()
    this.emitCommand('stop')
  }

  private stopContinuousCommand(): void {
    this.activeDirection = ''
    if (this.commandTimer !== null) { clearInterval(this.commandTimer); this.commandTimer = null }
  }

  private emitCommand(command: RobotCommand): void {
    if (this.onCommand) this.onCommand(command)
  }
}

@Component
struct DPadButton {
  @Prop symbol: string = ''
  @Prop btnDirection: string = ''
  @Prop active: boolean = false
  @Prop disabled: boolean = false
  @Prop isStop: boolean = false
  onPress: () => void = () => {}
  onRelease: () => void = () => {}

  build() {
    Button(this.symbol)
      .fontSize(this.isStop ? 16 : 22)
      .width(52).height(52)
      .fontColor(this.active ? '#FFFFFF' : '#D1D5DB')
      .backgroundColor(this.isStop
        ? '#1C1C1C'
        : (this.active ? '#2563EB' : '#222222'))
      .borderRadius(12)
      .border({ width: 1, color: this.active ? '#3B82F6' : '#2A2A2A' })
      .enabled(!this.disabled)
      .padding(0)
      .onTouch((event: TouchEvent) => {
        if (event.type === TouchType.Down) this.onPress()
        else if (event.type === TouchType.Up || event.type === TouchType.Cancel) this.onRelease()
      })
  }
}
