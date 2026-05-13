<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRobotStore } from '@/stores/robotStore'
import { api } from '@/services/api'
import webRTCService from '@/services/webrtc'
import webSocketService, { type RobotCommand, type WebSocketMessage } from '@/services/websocket'
import { Mic, Camera, ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-vue-next'

const store = useRobotStore()
const isConnected = () => store.connectionStatus === 'connected'

const callStatus = ref<'idle' | 'connecting' | 'connected'>('idle')
const activeKeys = ref<Record<string, boolean>>({})
const pressedDir = ref<string | null>(null)

function sendCommand(cmd: RobotCommand) {
  if (isConnected()) webSocketService.sendCommand(cmd)
}

function handleCallClick() {
  if (callStatus.value === 'idle') {
    callStatus.value = 'connecting'
    webRTCService.startCall().catch(() => {})
    const check = setInterval(() => {
      const state = webRTCService.getConnectionState()
      if (state === 'connected') {
        callStatus.value = 'connected'
        clearInterval(check)
      } else if (state === 'failed' || state === 'closed' || state === 'disconnected') {
        callStatus.value = 'idle'
        clearInterval(check)
      }
    }, 500)
  } else {
    webRTCService.close()
    callStatus.value = 'idle'
  }
}

const PYTHON_BACKEND = import.meta.env.VITE_BACKEND_HTTP_URL || 'http://localhost:8080'
const isTakingPhoto = ref(false)

function handleTakePhotos() {
  if (!isConnected() || isTakingPhoto.value) return
  isTakingPhoto.value = true
  webSocketService.sendCommand('take_photo')
}

function onPhotoCaptured(msg: WebSocketMessage) {
  if (msg.type !== 'photo_captured') return
  isTakingPhoto.value = false
  const payload = msg.payload as { url: string; filename: string; date: string }
  const fullUrl = payload.url.startsWith('http') ? payload.url : `${PYTHON_BACKEND}${payload.url}`
  api.addPhoto(fullUrl, payload.filename)
    .then(() => {
      store.addNotification('拍照成功，已保存至相册', 'success')
    })
    .catch(() => {
      store.addNotification('拍照成功但保存失败，请刷新相册', 'error')
    })
}

function dirToCommand(dir: string): RobotCommand {
  if (dir === 'up') return 'forward'
  if (dir === 'down') return 'backward'
  if (dir === 'left') return 'left'
  if (dir === 'right') return 'right'
  return 'stop'
}

function handleDirDown(dir: string) {
  if (!isConnected()) return
  pressedDir.value = dir
  sendCommand(dirToCommand(dir))
}

function handleDirUp() {
  if (pressedDir.value) {
    sendCommand('stop')
    pressedDir.value = null
  }
}

function handlePadLeave() {
  if (pressedDir.value) {
    sendCommand('stop')
    pressedDir.value = null
  }
}

// Keyboard
function onKeyDown(e: KeyboardEvent) {
  if (!isConnected() || e.repeat) return
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) e.preventDefault()
  const key = e.key.toLowerCase()
  if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: true }
    if (key === 'w') pressedDir.value = 'w'
    if (key === 's') pressedDir.value = 's'
    if (key === 'a') pressedDir.value = 'a'
    if (key === 'd') pressedDir.value = 'd'
    if (key === 'arrowup') pressedDir.value = 'arrowup'
    if (key === 'arrowdown') pressedDir.value = 'arrowdown'
    if (key === 'arrowleft') pressedDir.value = 'arrowleft'
    if (key === 'arrowright') pressedDir.value = 'arrowright'
    const map: Record<string, string> = { w: 'up', a: 'left', s: 'down', d: 'right', arrowup: 'up', arrowdown: 'down', arrowleft: 'left', arrowright: 'right' }
    sendCommand(dirToCommand(map[key]))
  }
}

function onKeyUp(e: KeyboardEvent) {
  if (!isConnected()) return
  const key = e.key.toLowerCase()
  if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: false }
    pressedDir.value = null
    sendCommand('stop')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  webSocketService.addMessageListener(onPhotoCaptured)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  webSocketService.removeMessageListener(onPhotoCaptured)
  callStatus.value = 'idle'
  activeKeys.value = {}
})
</script>

<template>
  <div class="flex flex-col p-5 gap-6">
    <!-- Call + Photo buttons -->
    <div class="flex gap-3">
      <button
        :disabled="!isConnected()"
        @click="handleCallClick"
        :class="[
          'flex-1 py-4 rounded-xl flex flex-col items-center justify-center gap-2 transition-all disabled:opacity-30 disabled:bg-[#1A1A1A] select-none border border-transparent disabled:border-[#2A2A2A]',
          callStatus === 'idle' ? 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white' :
          callStatus === 'connecting' ? 'bg-blue-600/50 text-white' :
          'bg-green-600 text-white hover:bg-green-700',
        ]"
      >
        <div v-if="callStatus === 'connecting'" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        <Mic v-else :class="['w-5 h-5', callStatus === 'connected' ? 'animate-pulse' : '']" />
        <span class="text-sm font-medium">
          {{ callStatus === 'idle' ? '通话' : callStatus === 'connecting' ? '正在建立...' : '通话中 (点击挂断)' }}
        </span>
      </button>

      <button
        :disabled="!isConnected() || isTakingPhoto"
        @click="handleTakePhotos"
        class="flex-1 py-4 bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white rounded-xl flex flex-col items-center justify-center gap-2 transition-all disabled:opacity-30 disabled:bg-[#1A1A1A] select-none border border-transparent disabled:border-[#2A2A2A]"
      >
        <div v-if="isTakingPhoto" class="w-5 h-5 border-2 border-neutral-400 border-t-white rounded-full animate-spin" />
        <Camera v-else class="w-5 h-5" />
        <span class="text-sm font-medium">{{ isTakingPhoto ? '拍照中...' : '拍照' }}</span>
      </button>
    </div>

    <!-- Two Control Pads -->
    <div class="space-y-4">
      <!-- PTZ (WASD) -->
      <div class="flex flex-col items-center gap-3 p-5 bg-[#141414] rounded-2xl border border-[#2A2A2A]">
        <h3 class="text-[13px] font-medium text-neutral-400 w-full text-left">云台控制 (WSAD)</h3>
        <div class="grid grid-cols-3 gap-2 w-full max-w-[200px]" @mouseleave="handlePadLeave">
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['w'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('up')"
            @mouseup="handleDirUp"
          >W</button>
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['a'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('left')"
            @mouseup="handleDirUp"
          >A</button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['s'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('down')"
            @mouseup="handleDirUp"
          >S</button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['d'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('right')"
            @mouseup="handleDirUp"
          >D</button>
        </div>
      </div>

      <!-- Movement (Arrow Keys) -->
      <div class="flex flex-col items-center gap-3 p-5 bg-[#141414] rounded-2xl border border-[#2A2A2A]">
        <h3 class="text-[13px] font-medium text-neutral-400 w-full text-left">移动控制 (方向键)</h3>
        <div class="grid grid-cols-3 gap-2 w-full max-w-[200px]" @mouseleave="handlePadLeave">
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowup'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('up')"
            @mouseup="handleDirUp"
          >
            <ArrowUp class="w-5 h-5" />
          </button>
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowleft'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('left')"
            @mouseup="handleDirUp"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowdown'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('down')"
            @mouseup="handleDirUp"
          >
            <ArrowDown class="w-5 h-5" />
          </button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowright'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleDirDown('right')"
            @mouseup="handleDirUp"
          >
            <ArrowRight class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
