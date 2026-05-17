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

const speedOptions = [
  { value: 'low' as const, label: '低速', color: 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10', activeColor: 'bg-emerald-500 text-white border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]' },
  { value: 'medium' as const, label: '中速', color: 'border-amber-500/40 text-amber-400 bg-amber-500/10', activeColor: 'bg-amber-500 text-white border-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.3)]' },
  { value: 'high' as const, label: '高速', color: 'border-rose-500/40 text-rose-400 bg-rose-500/10', activeColor: 'bg-rose-500 text-white border-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.3)]' },
]

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
        <span>速度</span>
        <div class="flex rounded-md overflow-hidden border border-neutral-700/50">
          <button
            v-for="opt in speedOptions"
            :key="opt.value"
            :disabled="store.connectionStatus !== 'connected'"
            @click="setSpeed(opt.value)"
            class="px-2.5 py-0.5 text-xs font-medium transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed border-r border-neutral-700/50 last:border-r-0"
            :class="store.speedLevel === opt.value && store.connectionStatus === 'connected' ? opt.activeColor : opt.color"
          >
            {{ opt.label }}
          </button>
        </div>
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
