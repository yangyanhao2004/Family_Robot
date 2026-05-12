<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import { Eye, EyeOff } from 'lucide-vue-next'

interface AdminUser {
  userId: number
  email: string
  name: string
  role: string
  passwordHash: string
  robotSerialNumbers: string[]
}

const users = ref<AdminUser[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const visibleHashes = ref<Set<number>>(new Set())

onMounted(async () => {
  try {
    users.value = await api.getAdminUsers()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
})

function toggleHash(userId: number) {
  if (visibleHashes.value.has(userId)) {
    visibleHashes.value.delete(userId)
  } else {
    visibleHashes.value.add(userId)
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <div>
      <h2 class="text-lg font-semibold">Users &amp; Robots</h2>
      <p class="text-sm text-neutral-500 mt-1">View all registered users, their credentials, and assigned robots</p>
    </div>

    <div v-if="loading" class="text-neutral-500 py-8 text-center">Loading...</div>

    <div v-else-if="error" class="text-red-400 py-8 text-center">
      <p>Failed to load users</p>
      <p class="text-xs mt-1">{{ error }}</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="user in users"
        :key="user.userId"
        class="bg-[#141414] border border-[#2A2A2A] rounded-lg overflow-hidden"
      >
        <div class="p-4">
          <div class="flex items-center justify-between mb-3">
            <div>
              <span class="text-sm font-medium text-white">{{ user.name }}</span>
              <span class="text-xs text-neutral-400 ml-2">{{ user.email }}</span>
            </div>
            <span
              :class="[
                'px-2 py-0.5 rounded text-xs font-medium',
                user.role === 'Admin' ? 'bg-blue-600/20 text-blue-400' : 'bg-neutral-700 text-neutral-300',
              ]"
            >
              {{ user.role }}
            </span>
          </div>

          <!-- Password hash -->
          <div class="bg-[#0D0D0D] rounded p-3 mb-3">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-neutral-500 font-medium uppercase tracking-wider">Password Hash (BCrypt)</span>
              <button
                class="text-xs text-neutral-400 hover:text-white transition-colors flex items-center gap-1"
                @click="toggleHash(user.userId)"
              >
                <Eye v-if="!visibleHashes.has(user.userId)" class="w-3.5 h-3.5" />
                <EyeOff v-else class="w-3.5 h-3.5" />
                {{ visibleHashes.has(user.userId) ? 'Hide' : 'Show' }}
              </button>
            </div>
            <p class="text-xs text-neutral-300 font-mono break-all">
              {{ visibleHashes.has(user.userId) ? user.passwordHash : '••••••••••••••••••••••••••••••••••••••••••••••••' }}
            </p>
          </div>

          <!-- Robots -->
          <div>
            <span class="text-xs text-neutral-500 font-medium uppercase tracking-wider">Robots</span>
            <div class="mt-1.5 flex flex-wrap gap-1.5">
              <span
                v-if="user.robotSerialNumbers.length === 0"
                class="text-xs text-neutral-600 italic"
              >
                No robots assigned
              </span>
              <span
                v-for="serial in user.robotSerialNumbers"
                :key="serial"
                class="px-2 py-0.5 bg-blue-600/10 border border-blue-500/20 rounded text-xs text-blue-400 font-mono"
              >
                {{ serial }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
