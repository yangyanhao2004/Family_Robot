<script setup lang="ts">
import { computed } from 'vue'
import { useRobotStore } from '@/stores/robotStore'
import { Battery, Signal, Activity } from 'lucide-vue-next'

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

const isRunning = computed(() => store.isRunning)
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
        <Activity class="w-4 h-4" />
        <span>状态: <span :class="store.connectionStatus === 'connected' ? 'text-white' : ''">{{ isRunning ? '运行中' : '待机' }}</span></span>
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
