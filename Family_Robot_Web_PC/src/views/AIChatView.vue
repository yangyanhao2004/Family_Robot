<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import webSocketService, { type WebSocketMessage, getUserIdFromToken } from '@/services/websocket'
import { Send, Bot, User } from 'lucide-vue-next'

const chatStore = useChatStore()

const inputText = ref('')
const isSending = ref(false)
const chatContainer = ref<HTMLElement | null>(null)

const userId = getUserIdFromToken()

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

watch(() => chatStore.messages.length, scrollToBottom)

function onAIResponse(msg: WebSocketMessage) {
  if (msg.type !== 'ai_chat_response') return
  const payload = msg.payload as { text: string; action: string; data?: any; error?: boolean; originalMessage?: string }
  if (!payload) return
  isSending.value = false
  chatStore.addAssistantMessage({
    text: payload.text,
    action: (payload.action as any) || 'chat_reply',
    data: payload.data,
  })
  // Auto-fill input on error for one-click retry
  if (payload.error && payload.originalMessage) {
    inputText.value = payload.originalMessage
  }
}

function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isSending.value || !webSocketService.isConnected()) return

  chatStore.addUserMessage(text)
  inputText.value = ''
  isSending.value = true

  webSocketService.sendAIChat(userId, text)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

onMounted(() => {
  webSocketService.addMessageListener(onAIResponse)
  scrollToBottom()
})

onUnmounted(() => {
  webSocketService.removeMessageListener(onAIResponse)
})
</script>

<template>
  <div class="flex flex-col h-full bg-[#0D0D0D]">
    <!-- Header -->
    <div class="flex items-center gap-3 px-5 py-4 border-b border-[#1F1F1F] shrink-0">
      <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
        <Bot class="w-4 h-4 text-white" />
      </div>
      <div>
        <p class="text-sm font-medium text-white">AI 对话</p>
        <p class="text-xs text-neutral-500">Kimi K2.5</p>
      </div>
    </div>

    <!-- Messages -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
      <div v-if="chatStore.messages.length === 0" class="flex flex-col items-center justify-center h-full text-neutral-600 gap-3">
        <Bot class="w-12 h-12" />
        <p class="text-sm">开始和 Jarvis 对话吧</p>
        <p class="text-xs">可以让我控制机器人、设置提醒，或者随便聊聊</p>
      </div>

      <div
        v-for="msg in chatStore.messages"
        :key="msg.id"
        :class="['flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <!-- Assistant avatar -->
        <div v-if="msg.role === 'assistant'" class="w-7 h-7 rounded-full bg-blue-600/20 flex items-center justify-center shrink-0 mt-0.5">
          <Bot class="w-3.5 h-3.5 text-blue-400" />
        </div>

        <div
          :class="[
            'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
            msg.role === 'user'
              ? 'bg-blue-600 text-white rounded-br-md'
              : 'bg-[#1A1A1A] text-neutral-200 rounded-bl-md border border-[#2A2A2A]',
          ]"
        >
          <p>{{ msg.content }}</p>
          <!-- Retry button for error messages -->
          <button
            v-if="msg.content?.startsWith('⚠️')"
            @click="sendMessage"
            class="mt-2 text-xs px-3 py-1 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-colors"
          >
            🔄 点此重发（已自动回填）
          </button>
          <!-- Action indicator -->
          <div
            v-if="msg.action && msg.action !== 'chat_reply'"
            class="flex items-center gap-1.5 mt-1.5 pt-1.5 border-t border-neutral-700/50"
          >
            <span class="text-[11px] px-2 py-0.5 rounded-full bg-blue-600/20 text-blue-400 font-medium">
              {{ msg.action === 'control_robot' ? '🤖 机器人控制' : '⏰ 设置提醒' }}
            </span>
          </div>
        </div>

        <!-- User avatar -->
        <div v-if="msg.role === 'user'" class="w-7 h-7 rounded-full bg-neutral-700 flex items-center justify-center shrink-0 mt-0.5">
          <User class="w-3.5 h-3.5 text-neutral-300" />
        </div>
      </div>

      <!-- Sending indicator -->
      <div v-if="isSending" class="flex gap-3 justify-start">
        <div class="w-7 h-7 rounded-full bg-blue-600/20 flex items-center justify-center shrink-0">
          <Bot class="w-3.5 h-3.5 text-blue-400" />
        </div>
        <div class="bg-[#1A1A1A] rounded-2xl rounded-bl-md border border-[#2A2A2A] px-4 py-3">
          <div class="flex gap-1">
            <span class="w-2 h-2 bg-neutral-600 rounded-full animate-bounce" style="animation-delay: 0ms" />
            <span class="w-2 h-2 bg-neutral-600 rounded-full animate-bounce" style="animation-delay: 150ms" />
            <span class="w-2 h-2 bg-neutral-600 rounded-full animate-bounce" style="animation-delay: 300ms" />
          </div>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="p-4 border-t border-[#1F1F1F] shrink-0">
      <div class="flex items-center gap-2 bg-[#141414] rounded-xl border border-[#2A2A2A] px-4 py-2 focus-within:border-blue-500/50 transition-colors">
        <input
          v-model="inputText"
          type="text"
          placeholder="输入消息..."
          :disabled="isSending"
          class="flex-1 bg-transparent text-sm text-white placeholder-neutral-600 outline-none"
          @keydown="handleKeydown"
        />
        <button
          :disabled="!inputText.trim() || isSending"
          @click="sendMessage"
          class="w-8 h-8 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-[#2A2A2A] disabled:text-neutral-600 text-white flex items-center justify-center transition-colors shrink-0"
        >
          <Send class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  </div>
</template>
