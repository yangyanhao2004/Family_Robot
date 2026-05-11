<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRobotStore } from '@/stores/robotStore'
import webRTCService from '@/services/webrtc'
import webSocketService, { type RobotCommand } from '@/services/websocket'
import { Mic, Camera, ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-vue-next'

const store = useRobotStore()
const isConnected = () => store.connectionStatus === 'connected'

const callStatus = ref<'idle' | 'connecting' | 'connected'>('idle')
const activeKeys = ref<Record<string, boolean>>({})

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

function handleTakePhotos() {
  if (!isConnected()) return
  const isSuccess = Math.random() > 0.2
  if (isSuccess) {
    store.addNotification('拍照成功，已保存至相册', 'success')
  } else {
    store.addNotification('拍照失败，请重试', 'error')
  }
}

function handlePtz(dir: string) {
  if (!isConnected()) return
  if (dir === 'up') sendCommand('forward')
  else if (dir === 'down') sendCommand('backward')
  else if (dir === 'left') sendCommand('left')
  else if (dir === 'right') sendCommand('right')
  else sendCommand('stop')
}

function handleMove(dir: string) {
  if (!isConnected()) return
  if (dir === 'up') sendCommand('forward')
  else if (dir === 'down') sendCommand('backward')
  else if (dir === 'left') sendCommand('left')
  else if (dir === 'right') sendCommand('right')
  else sendCommand('stop')
}

// Keyboard
function onKeyDown(e: KeyboardEvent) {
  if (!isConnected() || e.repeat) return
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) e.preventDefault()
  const key = e.key.toLowerCase()
  if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: true }
    if (key === 'w') handlePtz('up')
    if (key === 's') handlePtz('down')
    if (key === 'a') handlePtz('left')
    if (key === 'd') handlePtz('right')
    if (key === 'arrowup') handleMove('up')
    if (key === 'arrowdown') handleMove('down')
    if (key === 'arrowleft') handleMove('left')
    if (key === 'arrowright') handleMove('right')
  }
}

function onKeyUp(e: KeyboardEvent) {
  if (!isConnected()) return
  const key = e.key.toLowerCase()
  if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: false }
    if (['w', 'a', 's', 'd'].includes(key)) handlePtz('stop')
    if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) handleMove('stop')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
})

onUnmounted(() => {
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
        :disabled="!isConnected()"
        @click="handleTakePhotos"
        class="flex-1 py-4 bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white rounded-xl flex flex-col items-center justify-center gap-2 transition-all disabled:opacity-30 disabled:bg-[#1A1A1A] select-none border border-transparent disabled:border-[#2A2A2A]"
      >
        <Camera class="w-5 h-5" />
        <span class="text-sm font-medium">拍照</span>
      </button>
    </div>

    <!-- Two Control Pads -->
    <div class="space-y-4">
      <!-- PTZ (WASD) -->
      <div class="flex flex-col items-center gap-3 p-5 bg-[#141414] rounded-2xl border border-[#2A2A2A]">
        <h3 class="text-[13px] font-medium text-neutral-400 w-full text-left">云台控制 (WSAD)</h3>
        <div class="grid grid-cols-3 gap-2 w-full max-w-[200px]">
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['w'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtz('up')"
            @mouseup="handlePtz('stop')"
            @mouseleave="handlePtz('stop')"
          >W</button>
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['a'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtz('left')"
            @mouseup="handlePtz('stop')"
            @mouseleave="handlePtz('stop')"
          >A</button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['s'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtz('down')"
            @mouseup="handlePtz('stop')"
            @mouseleave="handlePtz('stop')"
          >S</button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['d'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtz('right')"
            @mouseup="handlePtz('stop')"
            @mouseleave="handlePtz('stop')"
          >D</button>
        </div>
      </div>

      <!-- Movement (Arrow Keys) -->
      <div class="flex flex-col items-center gap-3 p-5 bg-[#141414] rounded-2xl border border-[#2A2A2A]">
        <h3 class="text-[13px] font-medium text-neutral-400 w-full text-left">移动控制 (方向键)</h3>
        <div class="grid grid-cols-3 gap-2 w-full max-w-[200px]">
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowup'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleMove('up')"
            @mouseup="handleMove('stop')"
            @mouseleave="handleMove('stop')"
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
            @mousedown="handleMove('left')"
            @mouseup="handleMove('stop')"
            @mouseleave="handleMove('stop')"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowdown'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleMove('down')"
            @mouseup="handleMove('stop')"
            @mouseleave="handleMove('stop')"
          >
            <ArrowDown class="w-5 h-5" />
          </button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowright'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleMove('right')"
            @mouseup="handleMove('stop')"
            @mouseleave="handleMove('stop')"
          >
            <ArrowRight class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
