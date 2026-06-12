<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRobotStore } from '@/stores/robotStore'
import { api } from '@/services/api'
import webRTCService from '@/services/webrtc'
import webSocketService, { type RobotCommand, type WebSocketMessage } from '@/services/websocket'
import { Mic, Camera, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, AlertTriangle } from 'lucide-vue-next'

const store = useRobotStore()
const isConnected = () => store.connectionStatus === 'connected'

const callStatus = ref<'idle' | 'connecting' | 'connected'>('idle')
const mics = ref<MediaDeviceInfo[]>([])
const selectedMic = ref('')

async function refreshMics() {
  try {
    mics.value = await webRTCService.enumerateMics()
    if (!selectedMic.value && mics.value.length > 0) {
      selectedMic.value = mics.value[0].deviceId
    }
  } catch { /* no mics */ }
}

function onMicChange() {
  webRTCService.setMicrophone(selectedMic.value)
}

const activeKeys = ref<Record<string, boolean>>({})
const pressedDir = ref<string | null>(null)
const servo1Angle = ref(90)
const servo2Angle = ref(90)
const PTZ_STEP = 5
let ptzInterval: ReturnType<typeof setInterval> | null = null

function sendCommand(cmd: RobotCommand, angle?: number) {
  if (isConnected()) webSocketService.sendCommand(cmd, angle)
}

function onCallStateChange(state: 'idle' | 'connecting' | 'connected' | 'failed') {
  callStatus.value = state === 'failed' ? 'idle' : state
}

function handleCallClick() {
  if (callStatus.value === 'idle') {
    callStatus.value = 'connecting'
    webRTCService.startCall().catch(() => {
      callStatus.value = 'idle'
    })
  } else {
    webRTCService.close()
  }
}

const PYTHON_BACKEND = import.meta.env.VITE_BACKEND_HTTP_URL || 'http://localhost:8080'
const isTakingPhoto = ref(false)

// Fall simulation
const isTriggeringFall = ref(false)
const fallAlert = ref<{ message: string; visible: boolean }>({ message: '', visible: false })

async function triggerFall() {
  if (isTriggeringFall.value) return
  isTriggeringFall.value = true
  try {
    await api.triggerFallAlert(1, '用户')
    store.addNotification('摔倒告警已触发！喇叭播报 + 邮件已发送', 'success')
  } catch (e) {
    store.addNotification('触发失败: ' + (e as Error).message, 'error')
  }
  isTriggeringFall.value = false
}

function onFallAlert(msg: WebSocketMessage) {
  if (msg.type !== 'fall_alert') return
  const payload = msg.payload as { message: string }
  fallAlert.value = { message: payload.message, visible: true }
  store.addNotification(payload.message, 'error')
  setTimeout(() => fallAlert.value.visible = false, 10000)
}

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

// PTZ servo control (WASD / on-screen buttons)
function ptzAdjust(dir: string) {
  if (dir === 'up' || dir === 'w') {
    servo2Angle.value = Math.max(0, servo2Angle.value - PTZ_STEP)
    sendCommand('servo2', servo2Angle.value)
  } else if (dir === 'down' || dir === 's') {
    servo2Angle.value = Math.min(180, servo2Angle.value + PTZ_STEP)
    sendCommand('servo2', servo2Angle.value)
  } else if (dir === 'left' || dir === 'a') {
    servo1Angle.value = Math.min(180, servo1Angle.value + PTZ_STEP)
    sendCommand('servo1', servo1Angle.value)
  } else if (dir === 'right' || dir === 'd') {
    servo1Angle.value = Math.max(0, servo1Angle.value - PTZ_STEP)
    sendCommand('servo1', servo1Angle.value)
  }
}

function handlePtzDown(dir: string) {
  if (!isConnected()) return
  ptzAdjust(dir)
  if (ptzInterval) clearInterval(ptzInterval)
  ptzInterval = setInterval(() => ptzAdjust(dir), 100)
}

function handlePtzUp() {
  if (ptzInterval) {
    clearInterval(ptzInterval)
    ptzInterval = null
  }
}

// Movement control (Arrow keys / on-screen buttons)
function handleMoveDown(dir: string) {
  if (!isConnected()) return
  pressedDir.value = dir
  sendCommand(dirToCommand(dir))
}

function handleMoveUp() {
  if (pressedDir.value) {
    sendCommand('stop')
    pressedDir.value = null
  }
}

function handleMoveLeave() {
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

  // WASD → PTZ servo control
  if (['w', 'a', 's', 'd'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: true }
    ptzAdjust(key)
    if (ptzInterval) clearInterval(ptzInterval)
    ptzInterval = setInterval(() => ptzAdjust(key), 100)
  }
  // Arrow keys → motor movement
  else if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: true }
    const map: Record<string, string> = { arrowup: 'up', arrowdown: 'down', arrowleft: 'left', arrowright: 'right' }
    pressedDir.value = map[key]
    sendCommand(dirToCommand(map[key]))
  }
}

function onKeyUp(e: KeyboardEvent) {
  if (!isConnected()) return
  const key = e.key.toLowerCase()

  // WASD → stop PTZ if no WASD keys held
  if (['w', 'a', 's', 'd'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: false }
    const anyPtzHeld = ['w', 'a', 's', 'd'].some(k => activeKeys.value[k])
    if (!anyPtzHeld && ptzInterval) {
      clearInterval(ptzInterval)
      ptzInterval = null
    }
  }
  // Arrow keys → stop motor
  else if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
    activeKeys.value = { ...activeKeys.value, [key]: false }
    pressedDir.value = null
    sendCommand('stop')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  webSocketService.addMessageListener(onPhotoCaptured)
  webSocketService.addMessageListener(onFallAlert)
  webRTCService.onCallStateChange(onCallStateChange)
  webRTCService.preAcquireMic()
  refreshMics()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  webSocketService.removeMessageListener(onPhotoCaptured)
  webSocketService.removeMessageListener(onFallAlert)
  webRTCService.onCallStateChange(null)
  webRTCService.close()
  callStatus.value = 'idle'
  activeKeys.value = {}
})
</script>

<template>
  <div class="flex flex-col p-5 gap-6">
    <!-- Fall Alert Banner -->
    <div v-if="fallAlert.visible"
      class="bg-red-600/15 border border-red-500/30 rounded-xl p-4 flex items-center gap-3 animate-pulse">
      <AlertTriangle class="w-6 h-6 text-red-400 shrink-0" />
      <div class="flex-1">
        <p class="text-red-400 font-semibold text-sm">{{ fallAlert.message }}</p>
        <p class="text-red-400/60 text-xs mt-1">紧急邮件已发送，请尽快确认安全</p>
      </div>
    </div>

    <!-- Mic selector -->
    <div v-if="mics.length > 1" class="flex items-center gap-2">
      <label class="text-xs text-neutral-400">Mic:</label>
      <select
        v-model="selectedMic"
        @change="onMicChange()"
        class="bg-[#222] border border-[#2A2A2A] rounded-lg px-3 py-1.5 text-sm text-neutral-300 outline-none"
      >
        <option v-for="mic in mics" :key="mic.deviceId" :value="mic.deviceId">
          {{ mic.label.includes('Comm') || mic.label.includes('通讯') ? '蓝牙耳机 (通话)' :
             mic.label.includes('Bluetooth') || mic.label.includes('蓝牙') ? '蓝牙耳机 (立体声)' :
             mic.label.includes('Array') || mic.label.includes('阵列') ? '电脑麦克风' :
             mic.label.length > 25 ? mic.label.slice(0, 25) + '…' : mic.label }}
        </option>
      </select>
    </div>

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
        <div class="grid grid-cols-3 gap-2 w-full max-w-[200px]" @mouseleave="handlePtzUp">
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['w'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtzDown('w')"
            @mouseup="handlePtzUp"
          >W</button>
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['a'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtzDown('a')"
            @mouseup="handlePtzUp"
          >A</button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['s'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtzDown('s')"
            @mouseup="handlePtzUp"
          >S</button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border text-lg font-bold font-mono',
              activeKeys['d'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handlePtzDown('d')"
            @mouseup="handlePtzUp"
          >D</button>
        </div>
      </div>

      <!-- Movement (Arrow Keys) -->
      <div class="flex flex-col items-center gap-3 p-5 bg-[#141414] rounded-2xl border border-[#2A2A2A]">
        <h3 class="text-[13px] font-medium text-neutral-400 w-full text-left">移动控制 (方向键)</h3>
        <div class="grid grid-cols-3 gap-2 w-full max-w-[200px]" @mouseleave="handleMoveLeave">
          <div />
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowup'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleMoveDown('up')"
            @mouseup="handleMoveUp"
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
            @mousedown="handleMoveDown('left')"
            @mouseup="handleMoveUp"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowdown'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleMoveDown('down')"
            @mouseup="handleMoveUp"
          >
            <ArrowDown class="w-5 h-5" />
          </button>
          <button
            :disabled="!isConnected()"
            :class="[
              'w-full aspect-square rounded-xl flex items-center justify-center transition-all select-none border',
              activeKeys['arrowright'] ? 'bg-blue-600 text-white border-transparent' : 'bg-[#222] hover:bg-[#333] active:bg-blue-600 active:text-white disabled:opacity-30 disabled:bg-[#1A1A1A] disabled:text-neutral-600 disabled:border-[#2A2A2A] border-transparent text-neutral-300',
            ]"
            @mousedown="handleMoveDown('right')"
            @mouseup="handleMoveUp"
          >
            <ArrowRight class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Fall Simulation -->
    <div class="border-t border-[#2A2A2A] pt-4">
      <button
        @click="triggerFall"
        :disabled="isTriggeringFall"
        class="w-full bg-red-600/10 hover:bg-red-600/20 border border-red-500/30 rounded-xl py-4 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
      >
        <AlertTriangle class="w-5 h-5 text-red-400" />
        <span class="text-red-400 font-semibold text-sm">{{ isTriggeringFall ? '触发中...' : '🏥 模拟摔倒检测' }}</span>
      </button>
      <p class="text-xs text-neutral-500 text-center mt-2">点击模拟摔倒事件，测试紧急告警流程</p>
    </div>
  </div>
</template>
