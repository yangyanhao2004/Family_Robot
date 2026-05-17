<script setup lang="ts">
import { computed } from 'vue'
import { useRobotStore } from '@/stores/robotStore'
import webSocketService from '@/services/websocket'
import { Battery, Signal, Gauge } from 'lucide-vue-next'

const store = useRobotStore()

const pillText = computed(() => {
  if (store.connectionStatus === 'connected') return '已连接'
  if (store.connectionStatus === 'connecting') return '连接中'
  return '机器人未连接'
})

const pillClass = computed(() => {
  if (store.connectionStatus === 'connected') return 'bg-green-500/10 text-green-500 border-green-500/20'
  if (store.connectionStatus === 'connecting') return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
  return 'bg-neutral-200 text-neutral-500 border-neutral-300'
})

const barBg = computed(() =>
  store.connectionStatus === 'connected' ? 'bg-[#222] border-neutral-800' : 'bg-[#F5F5F5] border-neutral-300 text-neutral-800'
)

const textMuted = computed(() =>
  store.connectionStatus === 'connected' ? 'text-neutral-400' : 'text-neutral-500'
)

const speedLabel = computed(() => {
  if (store.speedLevel === 'low') return '低速'
  if (store.speedLevel === 'high') return '高速'
  return '中速'
})

function setSpeed(level: 'low' | 'medium' | 'high') {
  store.speedLevel = level
  webSocketService.sendCommand(`speed_${level}` as any)
}
</script>

<template>
  <header
    :class="['h-[50px] border-b transition-colors duration-300 flex items-center px-6 justify-between shrink-0 text-sm', barBg]"
  >
    <div class="flex items-center gap-3">
      <div :class="['flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border', pillClass]">
        <span
          v-if="store.connectionStatus === 'connected'"
          class="w-2 h-2 rounded-full bg-green-500 animate-pulse"
        />
        <span
          v-else-if="store.connectionStatus === 'connecting'"
          class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"
        />
        <span v-else class="w-2 h-2 rounded-full bg-neutral-400" />
        {{ pillText }}
      </div>
    </div>

    <div :class="['flex items-center gap-8', textMuted]">
      <div class="flex items-center gap-2">
        <Gauge class="w-4 h-4" />
        <span>速度:</span>
        <select
          :disabled="store.connectionStatus !== 'connected'"
          :value="store.speedLevel"
          @change="setSpeed(($event.target as HTMLSelectElement).value as 'low' | 'medium' | 'high')"
          class="bg-transparent border border-neutral-700 rounded px-2 py-0.5 text-xs cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:border-blue-500"
          :class="store.connectionStatus === 'connected' ? 'text-white' : ''"
        >
          <option value="low" class="bg-[#1A1A1A]">低速</option>
          <option value="medium" class="bg-[#1A1A1A]">中速</option>
          <option value="high" class="bg-[#1A1A1A]">高速</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <Battery class="w-4 h-4" />
        <span>电量: <span :class="store.connectionStatus === 'connected' ? 'text-white' : ''">{{ store.battery !== null ? `${store.battery}%` : '--' }}</span></span>
      </div>
      <div class="flex items-center gap-2">
        <Signal class="w-4 h-4" />
        <span>信号: <span :class="store.connectionStatus === 'connected' ? 'text-white' : ''">{{ store.signalStrength !== null ? `${store.signalStrength}/5` : '--' }}</span></span>
      </div>
    </div>
  </header>
</template>
