/**
 * 云台控制 — 对齐 Web 前端 DashboardView.vue PTZ (WASD)
 */
import { RobotCommand } from '../model/Types'
import { SERVO_STEP, COMMAND_INTERVAL } from '../common/Constants'

@Component
export struct PTZControl {
  onCommand?: (command: RobotCommand, angle: number) => void
  @Prop disabled: boolean = false
  @State servo1Angle: number = 90
  @State servo2Angle: number = 90
  @State private activeServo: string = ''
  private commandTimer: number | null = null

  aboutToDisappear(): void { this.stopContinuous() }

  build() {
    Column({ space: 8 }) {
      Text('云台控制')
        .fontSize(13).fontColor('#A3A3A6')
        .margin({ bottom: 2 })

      Row() {
        Text('H:' + this.servo1Angle.toFixed(0) + '°')
          .fontSize(11).fontColor('#71717A')
        Blank()
        Text('V:' + this.servo2Angle.toFixed(0) + '°')
          .fontSize(11).fontColor('#71717A')
      }.width('100%')

      // ▲ servo2 up (angle-)
      PTZButton({
        symbol: '▲', label: '上',
        disabled: this.disabled, active: this.activeServo === 'servo2_up',
        onPress: () => this.startAdjust('servo2', -1, 'servo2_up'),
        onRelease: () => this.stopContinuous()
      })

      Row({ space: 8 }) {
        // ◀ servo1 left (angle+)
        PTZButton({
          symbol: '◀', label: '左',
          disabled: this.disabled, active: this.activeServo === 'servo1_left',
          onPress: () => this.startAdjust('servo1', 1, 'servo1_left'),
          onRelease: () => this.stopContinuous()
        })

        Column() {
          Circle({ width: 6, height: 6 }).fill('#71717A')
        }
        .width(36).height(44).justifyContent(FlexAlign.Center)
        .borderRadius(8).backgroundColor('#1E1E1E')

        // ▶ servo1 right (angle-)
        PTZButton({
          symbol: '▶', label: '右',
          disabled: this.disabled, active: this.activeServo === 'servo1_right',
          onPress: () => this.startAdjust('servo1', -1, 'servo1_right'),
          onRelease: () => this.stopContinuous()
        })
      }

      // ▼ servo2 down (angle+)
      PTZButton({
        symbol: '▼', label: '下',
        disabled: this.disabled, active: this.activeServo === 'servo2_down',
        onPress: () => this.startAdjust('servo2', 1, 'servo2_down'),
        onRelease: () => this.stopContinuous()
      })
    }
    .padding(16).borderRadius(16)
    .backgroundColor('#141414')
    .border({ width: 1, color: '#2A2A2A' })
    .alignItems(HorizontalAlign.Center)
  }

  private startAdjust(servo: string, direction: number, activeName: string): void {
    if (this.disabled) return
    this.activeServo = activeName
    let step: number = SERVO_STEP * direction
    this.adjustAndSend(servo, step)
    this.commandTimer = setInterval(() => { this.adjustAndSend(servo, step) }, COMMAND_INTERVAL)
  }

  private stopContinuous(): void {
    this.activeServo = ''
    if (this.commandTimer !== null) { clearInterval(this.commandTimer); this.commandTimer = null }
  }

  private adjustAndSend(servo: string, step: number): void {
    let command: RobotCommand = servo === 'servo1' ? 'servo1' : 'servo2'
    if (servo === 'servo1') {
      this.servo1Angle = Math.max(0, Math.min(180, this.servo1Angle + step))
      if (this.onCommand) this.onCommand(command, this.servo1Angle)
    } else {
      this.servo2Angle = Math.max(0, Math.min(180, this.servo2Angle + step))
      if (this.onCommand) this.onCommand(command, this.servo2Angle)
    }
  }
}

@Component
struct PTZButton {
  @Prop symbol: string = ''
  @Prop label: string = ''
  @Prop disabled: boolean = false
  @Prop active: boolean = false
  onPress: () => void = () => {}
  onRelease: () => void = () => {}

  build() {
    Button() {
      Column({ space: 0 }) {
        Text(this.symbol).fontSize(16)
        Text(this.label).fontSize(9)
      }
    }
    .width(44).height(44).padding(0)
    .fontColor(this.active ? '#FFFFFF' : '#D1D5DB')
    .backgroundColor(this.active ? '#2563EB' : '#222222')
    .borderRadius(10)
    .border({ width: 1, color: this.active ? '#3B82F6' : '#2A2A2A' })
    .enabled(!this.disabled)
    .onTouch((event: TouchEvent) => {
      if (event.type === TouchType.Down) this.onPress()
      else if (event.type === TouchType.Up || event.type === TouchType.Cancel) this.onRelease()
    })
  }
}
