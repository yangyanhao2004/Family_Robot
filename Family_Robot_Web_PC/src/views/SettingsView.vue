<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import type { RobotSettings } from '@/types'

const settings = ref<RobotSettings>({
  autoSave: true,
  firmwareVersion: '',
  serialNumber: '',
})
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    settings.value = await api.getSettings()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
})

async function toggleAutoSave() {
  settings.value.autoSave = !settings.value.autoSave
  await api.updateSettings({ autoSave: settings.value.autoSave })
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h3 class="text-sm font-semibold text-neutral-300 uppercase tracking-wider">Settings</h3>

    <div v-if="loading" class="text-neutral-500">Loading...</div>

    <div v-else-if="error" class="text-neutral-500">
      <p>Failed to load settings</p>
      <p class="text-xs text-red-400 mt-1">{{ error }}</p>
    </div>

    <template v-else>
      <!-- Auto-save toggle -->
      <div class="flex items-center justify-between py-3 border-b border-[#2A2A2A]">
        <div>
          <p class="text-sm text-white font-medium">Auto-save</p>
          <p class="text-xs text-neutral-500 mt-0.5">Automatically save captured photos</p>
        </div>
        <button
          :class="[
            'relative w-11 h-6 rounded-full transition-colors',
            settings.autoSave ? 'bg-blue-600' : 'bg-[#3A3A3A]',
          ]"
          @click="toggleAutoSave"
        >
          <span
            :class="[
              'absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform shadow',
              settings.autoSave ? 'translate-x-[22px]' : 'translate-x-0.5',
            ]"
          />
        </button>
      </div>

      <!-- Device info -->
      <div class="space-y-3">
        <h4 class="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Device Info</h4>
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-[#141414] rounded-lg p-4">
            <p class="text-xs text-neutral-500 mb-1">Firmware Version</p>
            <p class="text-sm text-white font-medium">{{ settings.firmwareVersion }}</p>
          </div>
          <div class="bg-[#141414] rounded-lg p-4">
            <p class="text-xs text-neutral-500 mb-1">Serial Number</p>
            <p class="text-sm text-white font-medium">{{ settings.serialNumber }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
