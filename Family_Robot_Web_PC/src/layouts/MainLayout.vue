<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'
import { useRobotStore } from '@/stores/robotStore'
import webSocketService from '@/services/websocket'
import StatusBar from '@/components/StatusBar.vue'
import SideNav from '@/components/SideNav.vue'
import VideoStream from '@/components/VideoStream.vue'
import { MonitorPlay, WifiOff, CheckCircle2, AlertCircle } from 'lucide-vue-next'

const store = useRobotStore()
const isConnecting = ref(false)

const backendHttpBase = import.meta.env.VITE_BACKEND_HTTP_URL || 'http://localhost:8080'
const videoStreamUrl = computed(() =>
  store.connectionStatus === 'connected' ? `${backendHttpBase}/video/stream` : ''
)

function toggleConnection() {
  if (store.connectionStatus === 'connected') {
    webSocketService.disconnect()
    store.setDisconnected()
    return
  }
  if (isConnecting.value) return

  isConnecting.value = true
  store.setConnecting()
  webSocketService.connect()

  const check = setInterval(() => {
    if (store.connectionStatus !== 'connecting') {
      clearInterval(check)
      isConnecting.value = false
    }
  }, 200)
}

onMounted(() => {
  if (store.autoConnect) {
    toggleConnection()
  }
})

onUnmounted(() => {
  webSocketService.disconnect()
})
</script>

<template>
  <div class="flex flex-col h-screen bg-[#1A1A1A] text-white overflow-hidden font-sans">
    <StatusBar />

    <div class="flex flex-1 overflow-hidden">
      <SideNav />

      <!-- Center Video Area -->
      <main class="flex-1 bg-[#1A1A1A] relative flex items-center justify-center overflow-hidden">
        <!-- Notifications Overlay -->
        <div class="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex flex-col gap-2 w-full max-w-sm px-4 pointer-events-none">
          <div
            v-for="n in store.notifications"
            :key="n.id"
            :class="[
              'flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium',
              n.type === 'success' ? 'bg-green-500/90 text-white' : n.type === 'error' ? 'bg-red-500/90 text-white' : 'bg-blue-500/90 text-white',
            ]"
          >
            <CheckCircle2 v-if="n.type === 'success'" class="w-5 h-5 shrink-0" />
            <AlertCircle v-else class="w-5 h-5 shrink-0" />
            {{ n.message }}
          </div>
        </div>

        <VideoStream
          v-if="store.connectionStatus === 'connected'"
          :stream-url="videoStreamUrl"
          stream-type="mjpeg"
          autoplay
          muted
          class="absolute inset-0 w-full h-full"
        />
        <div v-else class="flex flex-col items-center justify-center text-neutral-500 gap-4">
          <div class="w-24 h-24 rounded-full bg-[#222] flex items-center justify-center mb-2">
            <MonitorPlay class="w-12 h-12 text-neutral-600" />
          </div>
          <p class="text-xl font-medium text-neutral-400 tracking-wide">未连接至机器人</p>
        </div>
      </main>

      <!-- Right Panel -->
      <aside class="w-[320px] bg-[#1A1A1A] border-l border-[#2A2A2A] flex flex-col shrink-0 z-10 shadow-[-8px_0_24px_rgba(0,0,0,0.2)]">
        <div class="p-5 border-b border-[#2A2A2A] bg-[#1E1E1E]">
          <!-- Disconnected state -->
          <button
            v-if="store.connectionStatus === 'disconnected'"
            @click="toggleConnection"
            class="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3.5 rounded-xl transition-all shadow-[0_4px_12px_rgba(37,99,235,0.2)] hover:shadow-[0_4px_16px_rgba(37,99,235,0.4)] flex items-center justify-center gap-2 text-sm"
          >
            连接至机器人
          </button>

          <!-- Connecting state -->
          <button
            v-else-if="store.connectionStatus === 'connecting'"
            disabled
            class="w-full bg-blue-600/60 text-white font-medium py-3.5 rounded-xl flex items-center justify-center gap-2 cursor-not-allowed text-sm"
          >
            <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            连接中...
          </button>

          <!-- Connected state -->
          <button
            v-else
            @click="toggleConnection"
            class="w-full bg-[#2A2A2A] hover:bg-[#333] text-white font-medium py-3.5 rounded-xl transition-colors flex items-center justify-center gap-2 group text-sm border border-[#3A3A3A]"
          >
            <span class="w-2.5 h-2.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse group-hover:hidden" />
            <WifiOff class="w-4 h-4 hidden group-hover:block text-red-400" />
            <span class="group-hover:hidden">已连接</span>
            <span class="hidden group-hover:block text-red-400">断开连接</span>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto bg-[#1A1A1A]">
          <RouterView />
        </div>
      </aside>
    </div>
  </div>
</template>
