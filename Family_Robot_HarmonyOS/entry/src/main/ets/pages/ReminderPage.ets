/**
 * 提醒页面 — 对齐 Web 前端 ReminderView.vue
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'
import { authManager } from '../services/AuthManager'
import { ReminderDto } from '../model/Types'

@Entry
@Component
struct ReminderPage {
  @State reminders: ReminderDto[] = []
  @State isLoading: boolean = false
  @State error: string = ''

  @State showForm: boolean = false
  @State editId: number = -1
  @State formText: string = ''
  @State formDate: string = ''
  @State formTime: string = ''
  @State formMethod: string = 'VOICE'
  @State formEmail: string = ''
  @State formEnabled: boolean = true

  aboutToAppear(): void { this.loadReminders() }

  build() {
    Column() {
      Row() {
        Button('← 返回').fontSize(14).fontColor('#71717A')
          .backgroundColor('transparent').onClick(() => router.back())
        Blank()
        Text('提醒').fontSize(18).fontColor('#FFFFFF')
        Blank()
        Button('+ 新建').fontSize(13).height(32).padding({ left: 12, right: 12 })
          .backgroundColor('#2563EB').borderRadius(8).fontColor('#FFFFFF')
          .onClick(() => this.openCreateForm())
      }.width('100%').padding(16)

      if (this.showForm) { this.BuildForm() }

      if (this.isLoading) {
        Column() {
          LoadingProgress().width(40).height(40).color('#3B82F6')
        }.width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else if (this.reminders.length === 0) {
        Column() {
          Text('⏰').fontSize(48).opacity(0.3)
          Text('暂无提醒').fontSize(14).fontColor('#A3A3A6').margin({ top: 8 })
        }.width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else {
        List() {
          ForEach(this.reminders, (item: ReminderDto) => {
            ListItem() { this.BuildReminderItem(item) }
          })
        }.layoutWeight(1).width('100%').backgroundColor('#1A1A1A')
      }
    }
    .width('100%').height('100%').backgroundColor('#1A1A1A')
  }

  @Builder
  BuildForm() {
    Column({ space: 12 }) {
      Text(this.editId === -1 ? '新建提醒' : '编辑提醒')
        .fontSize(16).fontColor('#FFFFFF')

      // 提醒内容
      TextInput({ placeholder: '提醒内容', text: this.formText })
        .width('100%').height(44)
        .backgroundColor('#141414').borderRadius(10)
        .border({ width: 1, color: '#2A2A2A' })
        .fontColor('#FFFFFF').placeholderColor('#52525B').fontSize(14)
        .onChange((v: string) => { this.formText = v })

      // 日期选择
      Row() {
        Text('日期').fontSize(14).fontColor('#A3A3A6').width(60)
        Text(this.formDate.length > 0 ? this.formDate : '请选择日期')
          .fontSize(14).fontColor(this.formDate.length > 0 ? '#FFFFFF' : '#52525B')
          .layoutWeight(1).textAlign(TextAlign.End)
        Text(' >').fontSize(14).fontColor('#52525B').margin({ left: 4 })
      }
      .width('100%').height(44).padding({ left: 14, right: 14 })
      .backgroundColor('#141414').borderRadius(10)
      .border({ width: 1, color: '#2A2A2A' })
      .onClick(() => this.showDatePicker())

      // 时间选择
      Row() {
        Text('时间').fontSize(14).fontColor('#A3A3A6').width(60)
        Text(this.formTime.length > 0 ? this.formTime : '请选择时间')
          .fontSize(14).fontColor(this.formTime.length > 0 ? '#FFFFFF' : '#52525B')
          .layoutWeight(1).textAlign(TextAlign.End)
        Text(' >').fontSize(14).fontColor('#52525B').margin({ left: 4 })
      }
      .width('100%').height(44).padding({ left: 14, right: 14 })
      .backgroundColor('#141414').borderRadius(10)
      .border({ width: 1, color: '#2A2A2A' })
      .onClick(() => this.showTimePicker())

      // 通知方式
      Row({ space: 16 }) {
        Text('通知方式:').fontSize(13).fontColor('#A3A3A6')
        Row() {
          Radio({ value: 'VOICE', group: 'method' })
            .checked(this.formMethod === 'VOICE')
            .onChange((_c: boolean) => { this.formMethod = 'VOICE' })
          Text('语音').fontSize(13).fontColor('#D1D5DB')
        }
        Row() {
          Radio({ value: 'EMAIL', group: 'method' })
            .checked(this.formMethod === 'EMAIL')
            .onChange((_c: boolean) => { this.formMethod = 'EMAIL' })
          Text('邮件').fontSize(13).fontColor('#D1D5DB')
        }
      }

      if (this.formMethod === 'EMAIL') {
        TextInput({ placeholder: '邮件地址', text: this.formEmail })
          .width('100%').height(44)
          .backgroundColor('#141414').borderRadius(10)
          .border({ width: 1, color: '#2A2A2A' })
          .fontColor('#FFFFFF').placeholderColor('#52525B').fontSize(14)
          .type(InputType.Email)
          .onChange((v: string) => { this.formEmail = v })
      }

      Row({ space: 10 }) {
        Button('取消')
          .fontSize(13).height(38).layoutWeight(1)
          .backgroundColor('#333333').borderRadius(10)
          .fontColor('#D1D5DB')
          .onClick(() => { this.showForm = false })
        Button('保存')
          .fontSize(13).height(38).layoutWeight(1)
          .backgroundColor('#2563EB').borderRadius(10)
          .fontColor('#FFFFFF')
          .onClick(() => this.saveReminder())
      }.width('100%')
    }
    .width('100%').padding(16)
    .backgroundColor('#141414').borderRadius(12)
  }

  @Builder
  BuildReminderItem(item: ReminderDto) {
    Row() {
      Column() {
        Text(item.text).fontSize(14).fontColor('#D1D5DB')
          .maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis })
        Row({ space: 8 }) {
          Text(this.formatDisplayTime(item.scheduledTime))
            .fontSize(11).fontColor('#71717A')
          Text(item.method === 'VOICE' ? '🔊语音' : '📧邮件')
            .fontSize(10).fontColor('#71717A')
          if (item.sent) {
            Text('已发送').fontSize(10).fontColor('#22C55E')
              .padding({ left: 6, right: 6, top: 1, bottom: 1 })
              .backgroundColor('#22C55E20').borderRadius(4)
          }
        }.margin({ top: 4 })
      }
      .alignItems(HorizontalAlign.Start).layoutWeight(1)

      Toggle({ type: ToggleType.Switch, isOn: item.enabled })
        .width(36).height(20)
        .margin({ right: 8 })
        .onChange((isOn: boolean) => { this.toggleReminder(item, isOn) })

      Button('编辑')
        .fontSize(11).height(30).padding({ left: 10, right: 10 })
        .backgroundColor('#222222').borderRadius(6)
        .border({ width: 1, color: '#2A2A2A' })
        .fontColor('#D1D5DB')
        .onClick(() => this.openEditForm(item))

      Button('删除')
        .fontSize(11).height(30).padding({ left: 10, right: 10 })
        .backgroundColor('#222222').borderRadius(6)
        .border({ width: 1, color: '#2A2A2A' })
        .fontColor('#EF4444')
        .margin({ left: 6 })
        .onClick(() => this.deleteReminder(item.id))
    }
    .width('100%')
    .padding({ left: 14, right: 10, top: 10, bottom: 10 })
    .border({ width: { bottom: 0.5 }, color: '#2A2A2A' })
  }

  private showDatePicker(): void {
    let now: Date = new Date()
    let defaultYear: number = now.getFullYear()
    let defaultMonth: number = now.getMonth()
    let defaultDay: number = now.getDate()
    if (this.formDate.length > 0) {
      let parts: string[] = this.formDate.split('-')
      if (parts.length === 3) {
        defaultYear = parseInt(parts[0])
        defaultMonth = parseInt(parts[1]) - 1
        defaultDay = parseInt(parts[2])
      }
    }
    DatePickerDialog.show({
      start: new Date('1970-01-01'),
      end: new Date('2100-12-31'),
      selected: new Date(defaultYear, defaultMonth, defaultDay),
      onAccept: (value: DatePickerResult) => {
        if (value.year === undefined || value.month === undefined || value.day === undefined) return
        let y: string = value.year.toString()
        let m: string = (value.month + 1).toString().padStart(2, '0')
        let d: string = value.day.toString().padStart(2, '0')
        this.formDate = y + '-' + m + '-' + d
      }
    })
  }

  private showTimePicker(): void {
    let defaultHour: number = 9
    let defaultMinute: number = 0
    if (this.formTime.length > 0) {
      let parts: string[] = this.formTime.split(':')
      if (parts.length >= 2) {
        defaultHour = parseInt(parts[0])
        defaultMinute = parseInt(parts[1])
      }
    }
    TimePickerDialog.show({
      selected: new Date(2026, 0, 1, defaultHour, defaultMinute),
      onAccept: (value: TimePickerResult) => {
        if (value.hour === undefined || value.minute === undefined) return
        let h: string = value.hour.toString().padStart(2, '0')
        let mi: string = value.minute.toString().padStart(2, '0')
        this.formTime = h + ':' + mi
      }
    })
  }

  private async loadReminders(): Promise<void> {
    this.isLoading = true
    try {
      let userId: number = authManager.getUserIdFromToken()
      let data: Array<Record<string, Object>> = await api.getReminders(userId)
      this.reminders = data.map((item: Record<string, Object>): ReminderDto => {
        return {
          id: item['id'] as number,
          text: item['text'] as string,
          scheduledTime: item['scheduledTime'] as string,
          method: item['method'] as 'EMAIL' | 'VOICE',
          email: item['email'] as string | null,
          enabled: item['enabled'] as boolean,
          sent: item['sent'] as boolean
        }
      })
    } catch (err) {
      this.error = (err as Error).message
    } finally { this.isLoading = false }
  }

  private openCreateForm(): void {
    this.editId = -1
    this.formText = ''
    let now: Date = new Date(Date.now() + 300000)
    this.formDate = this.dateToYMD(now)
    this.formTime = this.dateToHM(now)
    this.formMethod = 'VOICE'
    this.formEmail = ''
    this.formEnabled = true
    this.showForm = true
  }

  private openEditForm(item: ReminderDto): void {
    this.editId = item.id
    this.formText = item.text
    this.parseScheduledTime(item.scheduledTime)
    this.formMethod = item.method
    this.formEmail = item.email || ''
    this.formEnabled = item.enabled
    this.showForm = true
  }

  private parseScheduledTime(isoStr: string): void {
    if (isoStr.includes('T')) {
      let parts: string[] = isoStr.split('T')
      this.formDate = parts[0]
      if (parts.length > 1) {
        let timePart: string = parts[1]
        if (timePart.includes(':')) {
          let timeParts: string[] = timePart.split(':')
          this.formTime = timeParts[0] + ':' + timeParts[1]
        }
      }
    } else {
      this.formDate = isoStr
      this.formTime = '09:00'
    }
  }

  private buildIso(): string {
    if (this.formDate.length === 0 || this.formTime.length === 0) {
      return ''
    }
    return this.formDate + 'T' + this.formTime + ':00'
  }

  private async saveReminder(): Promise<void> {
    if (this.formText.trim().length === 0) return
    let isoStr: string = this.buildIso()
    if (isoStr.length === 0) return
    let data: Record<string, Object> = {
      'userId': authManager.getUserIdFromToken(),
      'text': this.formText.trim(),
      'scheduledTime': isoStr,
      'method': this.formMethod,
      'email': this.formMethod === 'EMAIL' ? this.formEmail : '',
      'enabled': this.formEnabled
    }
    try {
      if (this.editId === -1) {
        await api.createReminder(data)
      } else {
        await api.updateReminder(this.editId, data)
      }
      this.showForm = false
      this.loadReminders()
    } catch (err) { /* ignore */ }
  }

  private async toggleReminder(item: ReminderDto, isOn: boolean): Promise<void> {
    let data: Record<string, Object> = {
      'userId': authManager.getUserIdFromToken(),
      'text': item.text,
      'scheduledTime': item.scheduledTime,
      'method': item.method,
      'email': item.email || '',
      'enabled': isOn
    }
    try {
      await api.updateReminder(item.id, data)
      item.enabled = isOn
    } catch (_e) { }
  }

  private async deleteReminder(id: number): Promise<void> {
    try { await api.deleteReminder(id); this.loadReminders() } catch (_e) { }
  }

  private dateToYMD(date: Date): string {
    let y: string = date.getFullYear().toString()
    let m: string = (date.getMonth() + 1).toString().padStart(2, '0')
    let d: string = date.getDate().toString().padStart(2, '0')
    return y + '-' + m + '-' + d
  }

  private dateToHM(date: Date): string {
    let h: string = date.getHours().toString().padStart(2, '0')
    let mi: string = date.getMinutes().toString().padStart(2, '0')
    return h + ':' + mi
  }

  private formatDisplayTime(isoStr: string): string {
    if (isoStr.includes('T')) {
      let parts: string[] = isoStr.split('T')
      let d: string = parts[0]
      let t: string = parts[1]
      if (t.includes(':')) {
        let tp: string[] = t.split(':')
        return d + ' ' + tp[0] + ':' + tp[1]
      }
      return d + ' ' + t
    }
    return isoStr
  }
}
