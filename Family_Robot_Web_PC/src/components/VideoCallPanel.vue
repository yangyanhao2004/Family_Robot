<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import webRTCService from '@/services/webrtc'
import { Phone, Mic, MicOff } from 'lucide-vue-next'

const remoteAudio = ref<HTMLAudioElement | null>(null)
const isCallConnected = ref(false)
const callStatus = ref('Not connected')
const isConnecting = ref(false)
const isMuted = ref(false)

const statusColor = computed(() => {
  if (isCallConnected.value) return 'text-green-400'
  if (isConnecting.value) return 'text-amber-400'
  return 'text-neutral-400'
})

async function toggleCall() {
  if (isCallConnected.value || isConnecting.value) {
    webRTCService.close()
    isCallConnected.value = false
    isConnecting.value = false
    callStatus.value = 'Closed'
    return
  }

  isConnecting.value = true
  callStatus.value = 'Connecting...'
  try {
    await webRTCService.startCall()
  } catch (error) {
    console.error('Call start failed:', error)
    callStatus.value = 'Start failed'
    isConnecting.value = false
  }
}

function toggleMic() {
  isMuted.value = webRTCService.toggleMicrophone()
}

function bindRemoteAudio() {
  const stream = webRTCService.getRemoteStream()
  if (!remoteAudio.value || !stream) return
  if (remoteAudio.value.srcObject !== stream) {
    remoteAudio.value.srcObject = stream
    remoteAudio.value.play().catch(() => {})
  }
}

function updateCallStatus() {
  const state = webRTCService.getConnectionState()
  isCallConnected.value = state === 'connected'
  if (state === 'connected') {
    isConnecting.value = false
    callStatus.value = 'Connected'
  } else if (state === 'connecting') {
    callStatus.value = 'Connecting...'
  } else if (state === 'failed') {
    isConnecting.value = false
    callStatus.value = 'Failed'
  } else if (!isConnecting.value) {
    callStatus.value = 'Not connected'
  }
}

const statusInterval = setInterval(() => {
  updateCallStatus()
  bindRemoteAudio()
}, 400)

onMounted(() => {
  updateCallStatus()
  webRTCService.preAcquireMic()
})

onUnmounted(() => {
  clearInterval(statusInterval)
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <span :class="['w-2.5 h-2.5 rounded-full transition-colors', statusColor]" />
      <span class="text-sm font-medium text-neutral-300">{{ callStatus }}</span>
    </div>

    <div class="flex gap-3">
      <button
        :class="[
          'flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-300',
          isCallConnected || isConnecting
            ? 'bg-red-600/10 hover:bg-red-600/20 text-red-400 border border-red-500/20'
            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_4px_12px_rgba(37,99,235,0.3)]',
        ]"
        @click="toggleCall"
      >
        <Phone class="w-4 h-4" />
        {{ isCallConnected || isConnecting ? 'End Call' : 'Start Call' }}
      </button>

      <button
        v-if="isCallConnected"
        :class="[
          'flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm border transition-colors',
          isMuted
            ? 'bg-red-600/10 border-red-500/20 text-red-400'
            : 'bg-[#2A2A2A] border-[#3A3A3A] text-neutral-300 hover:border-neutral-500',
        ]"
        @click="toggleMic"
      >
        <MicOff v-if="isMuted" class="w-4 h-4" />
        <Mic v-else class="w-4 h-4" />
        {{ isMuted ? 'Unmute' : 'Mute' }}
      </button>
    </div>

    <audio ref="remoteAudio" autoplay playsinline />
  </div>
</template>
