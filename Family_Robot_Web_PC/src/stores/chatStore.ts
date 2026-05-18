import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage, AIChatResponse } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])

  let _nextId = 0

  function addUserMessage(content: string) {
    messages.value = [...messages.value, {
      id: `msg-${++_nextId}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    }]
  }

  function addAssistantMessage(resp: AIChatResponse) {
    messages.value = [...messages.value, {
      id: `msg-${++_nextId}`,
      role: 'assistant',
      content: resp.text,
      action: resp.action,
      data: resp.data,
      timestamp: Date.now(),
    }]
  }

  function addRawAssistantMessage(text: string) {
    messages.value = [...messages.value, {
      id: `msg-${++_nextId}`,
      role: 'assistant',
      content: text,
      timestamp: Date.now(),
    }]
  }

  function clearMessages() {
    messages.value = []
  }

  return { messages, addUserMessage, addAssistantMessage, addRawAssistantMessage, clearMessages }
})
