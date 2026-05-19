<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useChatStore } from '@/stores/chatStore'
import webSocketService, { getUserIdFromToken } from '@/services/websocket'
import { api } from '@/services/api'
import { LogOut, Lock } from 'lucide-vue-next'
import type { UserProfile } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const chatStore = useChatStore()

const profile = ref<UserProfile>({
  name: '',
  email: '',
  avatar: '',
  role: '',
  lastLogin: '',
})
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const data = await api.getProfile()
    profile.value = { avatar: '', ...data }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
})

function handleLogout() {
  const userId = getUserIdFromToken()
  if (webSocketService.isConnected() && userId) {
    webSocketService.sendAISessionEnd(userId)
  }
  chatStore.clearMessages()
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h3 class="text-sm font-semibold text-neutral-300 uppercase tracking-wider">User Profile</h3>

    <div v-if="loading" class="text-neutral-500">Loading...</div>

    <div v-else-if="error" class="text-neutral-500">
      <p>Failed to load profile</p>
      <p class="text-xs text-red-400 mt-1">{{ error }}</p>
    </div>

    <template v-else>
      <!-- Avatar + name -->
      <div class="flex items-center gap-4">
        <div class="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center text-2xl font-bold text-white">
          {{ profile.name.charAt(0).toUpperCase() }}
        </div>
        <div>
          <p class="text-lg font-semibold text-white">{{ profile.name }}</p>
          <p class="text-sm text-neutral-400">{{ profile.email }}</p>
        </div>
      </div>

      <!-- Account info -->
      <div class="space-y-3">
        <div class="flex justify-between py-3 border-b border-[#2A2A2A]">
          <span class="text-sm text-neutral-400">Role</span>
          <span class="text-sm text-white font-medium">{{ profile.role }}</span>
        </div>
        <div class="flex justify-between py-3 border-b border-[#2A2A2A]">
          <span class="text-sm text-neutral-400">Last Login</span>
          <span class="text-sm text-white font-medium">{{ profile.lastLogin }}</span>
        </div>
      </div>

      <!-- Change Password -->
      <button
        class="w-full flex items-center justify-center gap-2 py-3 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 rounded-lg font-medium text-sm transition-colors border border-blue-500/20"
        @click="$router.push({ name: 'resetPassword' })"
      >
        <Lock class="w-4 h-4" />
        Change Password
      </button>

      <!-- Logout -->
      <button
        class="w-full flex items-center justify-center gap-2 py-3 bg-red-600/10 hover:bg-red-600/20 text-red-400 rounded-lg font-medium text-sm transition-colors border border-red-500/20"
        @click="handleLogout"
      >
        <LogOut class="w-4 h-4" />
        Sign Out
      </button>
    </template>
  </div>
</template>
