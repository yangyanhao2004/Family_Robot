<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { api } from '@/services/api'
import { Eye, EyeOff, Search, X, Trash2 } from 'lucide-vue-next'

interface AdminUser {
  userId: number
  email: string
  name: string
  role: string
  robotSerialNumbers: string[]
}

const users = ref<AdminUser[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const revealedPasswords = reactive<Record<number, string>>({})
const loadingPassword = ref<Record<number, boolean>>({})

const searchQuery = ref('')

let fetchTimer: ReturnType<typeof setTimeout> | null = null

async function fetchUsers() {
  loading.value = true
  error.value = null
  try {
    users.value = await api.getAdminUsers(searchQuery.value.trim() || undefined)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

watch(searchQuery, () => {
  if (fetchTimer) clearTimeout(fetchTimer)
  fetchTimer = setTimeout(fetchUsers, 300)
})

onMounted(() => {
  fetchUsers()
})

async function revealPassword(userId: number) {
  if (revealedPasswords[userId]) {
    delete revealedPasswords[userId]
    return
  }
  loadingPassword.value[userId] = true
  try {
    const res = await api.getUserPassword(userId)
    revealedPasswords[userId] = res.password
  } catch (e) {
    // ignore
  } finally {
    loadingPassword.value[userId] = false
  }
}

const deletingUserId = ref<number | null>(null)

async function deleteUser(userId: number) {
  if (!window.confirm('Delete this user and ALL related data (robots, photos, reminders, etc.)? This cannot be undone.')) return
  deletingUserId.value = userId
  try {
    await api.deleteAdminUser(userId)
    users.value = users.value.filter(u => u.userId !== userId)
  } catch (e) {
    alert((e as Error).message)
  } finally {
    deletingUserId.value = null
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold">Users &amp; Robots</h2>
        <p class="text-sm text-neutral-500 mt-1">View all registered users, their credentials, and assigned robots</p>
      </div>
    </div>

    <!-- Search -->
    <div class="relative max-w-sm">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search by name, email, or serial number..."
        class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-lg pl-9 pr-4 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
      />
      <button
        v-if="searchQuery"
        @click="searchQuery = ''"
        class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-neutral-500 hover:text-white"
      >
        <X class="w-3.5 h-3.5" />
      </button>
    </div>

    <div v-if="loading" class="text-neutral-500 py-8 text-center">
      <div class="w-5 h-5 border-2 border-neutral-600 border-t-blue-500 rounded-full animate-spin mx-auto" />
    </div>

    <div v-else-if="error" class="text-red-400 py-8 text-center">
      <p>Failed to load users</p>
      <p class="text-xs mt-1">{{ error }}</p>
    </div>

    <div v-else-if="users.length === 0" class="text-neutral-500 py-8 text-center">
      <span v-if="!searchQuery">No users found</span>
      <span v-else>No users match "{{ searchQuery }}"</span>
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
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'px-2 py-0.5 rounded text-xs font-medium',
                  user.role === 'Admin' ? 'bg-blue-600/20 text-blue-400' : 'bg-neutral-700 text-neutral-300',
                ]"
              >
                {{ user.role }}
              </span>
              <button
                v-if="user.role !== 'Admin'"
                @click="deleteUser(user.userId)"
                :disabled="deletingUserId === user.userId"
                class="p-1.5 text-neutral-500 hover:text-red-400 hover:bg-red-600/10 rounded transition-colors disabled:opacity-50"
                title="Delete user"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Password -->
          <div class="bg-[#0D0D0D] rounded p-3 mb-3">
            <div class="flex items-center justify-between">
              <span class="text-xs text-neutral-500 font-medium uppercase tracking-wider">Password</span>
              <button
                @click="revealPassword(user.userId)"
                :disabled="loadingPassword[user.userId]"
                class="flex items-center gap-1 text-xs text-neutral-400 hover:text-amber-400 transition-colors disabled:opacity-50"
              >
                <Eye v-if="!revealedPasswords[user.userId]" class="w-3.5 h-3.5" />
                <EyeOff v-else class="w-3.5 h-3.5" />
                {{ loadingPassword[user.userId] ? 'Loading...' : revealedPasswords[user.userId] ? 'Hide' : 'View' }}
              </button>
            </div>
            <p v-if="revealedPasswords[user.userId]" class="text-sm text-amber-400 font-mono mt-1">{{ revealedPasswords[user.userId] }}</p>
            <p v-else class="text-sm text-neutral-600 font-mono mt-1">••••••••</p>
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
