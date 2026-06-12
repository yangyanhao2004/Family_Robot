<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import type { RobotSettings } from '@/types'
import { ShieldAlert, UserRound, Mail, Save, CheckCircle } from 'lucide-vue-next'

const settings = ref<RobotSettings>({
  firmwareVersion: '',
  serialNumber: '',
})
const loading = ref(true)
const error = ref<string | null>(null)
const saving = ref(false)
const saved = ref(false)

const ecName = ref('')
const ecEmail = ref('')

onMounted(async () => {
  try {
    settings.value = await api.getSettings()
    ecName.value = settings.value.emergencyContactName || ''
    ecEmail.value = settings.value.emergencyContactEmail || ''
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
})

async function saveEmergencyContact() {
  saving.value = true
  saved.value = false
  try {
    settings.value = await api.updateEmergencyContact(ecName.value, ecEmail.value)
    saved.value = true
    setTimeout(() => saved.value = false, 2000)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
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

      <!-- Emergency Contact -->
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <ShieldAlert class="w-4 h-4 text-red-400" />
          <h4 class="text-xs font-semibold text-neutral-400 uppercase tracking-wider">紧急联系人</h4>
        </div>
        <div class="bg-[#141414] rounded-lg p-4 space-y-3">
          <div class="relative">
            <label class="text-xs text-neutral-500 mb-1 block">姓名</label>
            <div class="relative">
              <UserRound class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input v-model="ecName" type="text" placeholder="紧急联系人姓名"
                class="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white rounded-lg py-2.5 pl-9 pr-4 outline-none focus:border-red-500 transition-colors text-sm" />
            </div>
          </div>
          <div class="relative">
            <label class="text-xs text-neutral-500 mb-1 block">邮箱</label>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input v-model="ecEmail" type="email" placeholder="紧急联系人邮箱"
                class="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white rounded-lg py-2.5 pl-9 pr-4 outline-none focus:border-red-500 transition-colors text-sm" />
            </div>
          </div>
          <button @click="saveEmergencyContact" :disabled="saving"
            class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
            :class="saved ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400 hover:bg-red-600/30'">
            <CheckCircle v-if="saved" class="w-4 h-4" />
            <Save v-else class="w-4 h-4" />
            {{ saved ? '已保存' : saving ? '保存中...' : '保存紧急联系人' }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
