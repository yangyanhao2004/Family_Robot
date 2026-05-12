<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/services/api'
import { Cpu, PlusCircle } from 'lucide-vue-next'

const serialNumber = ref('')
const loading = ref(false)
const message = ref<string | null>(null)
const error = ref<string | null>(null)

async function handleRegister() {
  if (!serialNumber.value.trim()) return
  loading.value = true
  error.value = null
  message.value = null
  try {
    await api.registerRobot(serialNumber.value.trim())
    message.value = `Robot "${serialNumber.value.trim()}" registered successfully`
    serialNumber.value = ''
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <div>
      <h2 class="text-lg font-semibold">Register Robot</h2>
      <p class="text-sm text-neutral-500 mt-1">Add a new robot serial number to the system</p>
    </div>

    <div class="bg-[#141414] border border-[#2A2A2A] rounded-lg p-6 max-w-lg">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center">
          <Cpu class="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <p class="text-sm font-medium text-white">New Robot Serial</p>
          <p class="text-xs text-neutral-500">Format: RBT-XXXXX-XXX</p>
        </div>
      </div>

      <div class="flex gap-3">
        <input
          v-model="serialNumber"
          type="text"
          placeholder="e.g. RBT-00001-ABC"
          class="flex-1 bg-[#0D0D0D] border border-[#2A2A2A] text-white rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-500 transition-colors font-mono"
          @keyup.enter="handleRegister"
        />
        <button
          :disabled="loading || !serialNumber.trim()"
          class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          @click="handleRegister"
        >
          <PlusCircle class="w-4 h-4" />
          {{ loading ? 'Registering...' : 'Register' }}
        </button>
      </div>

      <div v-if="message" class="mt-4 p-3 bg-green-600/10 border border-green-500/20 rounded-lg">
        <p class="text-sm text-green-400">{{ message }}</p>
      </div>

      <div v-if="error" class="mt-4 p-3 bg-red-600/10 border border-red-500/20 rounded-lg">
        <p class="text-sm text-red-400">{{ error }}</p>
      </div>
    </div>
  </div>
</template>
