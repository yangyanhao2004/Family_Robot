/**
 * 聊天气泡 — 对齐 Web 前端 AIChatView.vue
 */
import { ChatMessage } from '../model/Types'

@Component
export struct ChatBubble {
  @Prop message: ChatMessage = {
    id: '', role: 'user', content: '', timestamp: 0
  }

  build() {
    Row() {
      if (this.message.role === 'user') Blank()

      Column() {
        Text(this.message.content)
          .fontSize(14).fontColor(this.message.role === 'user' ? '#FFFFFF' : '#D1D5DB')
          .padding({ left: 16, right: 16, top: 10, bottom: 10 })
          .borderRadius(this.message.role === 'user'
            ? { topLeft: 16, topRight: 16, bottomLeft: 16, bottomRight: 6 }
            : { topLeft: 16, topRight: 16, bottomLeft: 6, bottomRight: 16 })
          .backgroundColor(this.message.role === 'user' ? '#2563EB' : '#1A1A1A')
          .constraintSize({ maxWidth: '75%' })

        if (this.message.action && this.message.action !== 'chat_reply') {
          Text(this.message.action === 'control_robot' ? '🤖 已操控' : '⏰ 已设提醒')
            .fontSize(11).fontColor('#60A5FA')
            .padding({ left: 8, right: 8, top: 2, bottom: 2 })
            .borderRadius(20)
            .backgroundColor('rgba(37,99,235,0.15)')
            .margin({ top: 4 })
        }

        Text(this.formatTime(this.message.timestamp))
          .fontSize(10).fontColor('#52525B')
          .margin({ top: 4 })
      }
      .alignItems(this.message.role === 'user' ? HorizontalAlign.End : HorizontalAlign.Start)

      if (this.message.role === 'assistant') Blank()
    }
    .width('100%')
    .padding({ left: 12, right: 12, top: 4, bottom: 4 })
  }

  private formatTime(timestamp: number): string {
    let date: Date = new Date(timestamp)
    let h: string = date.getHours().toString().padStart(2, '0')
    let m: string = date.getMinutes().toString().padStart(2, '0')
    return h + ':' + m
  }
}
