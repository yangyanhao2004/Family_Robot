/**
 * AI 对话页面 — 对齐 Web 前端 AIChatView.vue
 */
import router from '@ohos.router'
import { webSocketService } from '../services/WebSocketService'
import { authManager } from '../services/AuthManager'
import { ChatBubble } from '../components/ChatBubble'
import { ChatMessage, WebSocketMessage, AIChatResponse } from '../model/Types'

@Entry
@Component
struct AIChatPage {
  @State messages: ChatMessage[] = []
  @State inputText: string = ''
  @State isSending: boolean = false
  private scroller: Scroller = new Scroller()
  private msgCounter: number = 0
  private wsListener: (msg: WebSocketMessage) => void = (_msg: WebSocketMessage) => {}

  aboutToAppear(): void {
    this.wsListener = (msg: WebSocketMessage) => {
      if (msg.type === 'ai_chat_response' && msg.payload) {
        let payload: Record<string, Object> = msg.payload
        let response: AIChatResponse = {
          text: (payload['text'] as string) || '',
          action: (payload['action'] as 'chat_reply' | 'control_robot' | 'set_reminder') || 'chat_reply',
          data: payload['data'] as Record<string, Object> | undefined
        }
        this.addAssistantMessage(response)
        this.isSending = false
        // Check error flag and restore original message for retry
        let isError: boolean = (payload['error'] as boolean) ?? false
        if (isError && payload['originalMessage']) {
          this.inputText = payload['originalMessage'] as string
        }
      }
    }
    webSocketService.addMessageListener(this.wsListener)
  }

  aboutToDisappear(): void {
    webSocketService.removeMessageListener(this.wsListener)
    webSocketService.sendAISessionEnd(authManager.getUserIdFromToken())
  }

  build() {
    Column() {
      // 标题栏
      Row() {
        Button('← 返回').fontSize(14).fontColor('#71717A')
          .backgroundColor('transparent')
          .onClick(() => {
            webSocketService.sendAISessionEnd(authManager.getUserIdFromToken())
            router.back()
          })
        Blank()
        Text('AI 对话').fontSize(16).fontColor('#FFFFFF')
        Blank()
        Row().width(60)
      }
      .width('100%').padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .border({ width: { bottom: 1 }, color: '#1F1F1F' })

      // 消息列表
      List({ scroller: this.scroller }) {
        ForEach(this.messages, (item: ChatMessage) => {
          ListItem() { ChatBubble({ message: item }) }
        })
      }
      .layoutWeight(1).width('100%')
      .backgroundColor('#0D0D0D')

      // 输入区域
      Row({ space: 8 }) {
        TextArea({ placeholder: '输入消息...', text: this.inputText })
          .layoutWeight(1).height(44).maxLength(500)
          .backgroundColor('#141414').borderRadius(12)
          .border({ width: 1, color: '#2A2A2A' })
          .fontColor('#FFFFFF').placeholderColor('#52525B')
          .fontSize(14).padding({ left: 14, right: 14, top: 10, bottom: 10 })
          .onChange((v: string) => { this.inputText = v })
          .onKeyEvent((event) => {
            if (event.keyCode === 2054 && event.type === 0) { this.sendMessage() }
          })

        Button('发送')
          .fontSize(13).fontColor('#FFFFFF')
          .height(44).padding({ left: 16, right: 16 })
          .backgroundColor('#2563EB').borderRadius(10)
          .enabled(!this.isSending && this.inputText.trim().length > 0)
          .onClick(() => { this.sendMessage() })
      }
      .width('100%')
      .padding({ left: 12, right: 12, top: 8, bottom: 12 })
      .border({ width: { top: 1 }, color: '#1F1F1F' })
      .backgroundColor('#141414')
    }
    .width('100%').height('100%')
    .backgroundColor('#0D0D0D')
  }

  private sendMessage(): void {
    let text: string = this.inputText.trim()
    if (text.length === 0 || this.isSending) return
    this.msgCounter++
    this.messages = [...this.messages, {
      id: 'msg_' + this.msgCounter, role: 'user',
      content: text, timestamp: Date.now()
    }]
    this.inputText = ''
    this.isSending = true
    setTimeout(() => { this.scroller.scrollToIndex(this.messages.length - 1, true) }, 100)
    webSocketService.sendAIChat(authManager.getUserIdFromToken(), text)
  }

  private addAssistantMessage(response: AIChatResponse): void {
    this.msgCounter++
    this.messages = [...this.messages, {
      id: 'msg_' + this.msgCounter, role: 'assistant',
      content: response.text, action: response.action,
      data: response.data, timestamp: Date.now()
    }]
    setTimeout(() => { this.scroller.scrollToIndex(this.messages.length - 1, true) }, 100)
  }
}
