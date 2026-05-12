<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { Shield, Users, Cpu, LogOut } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex h-screen bg-[#1A1A1A] text-white">
    <!-- Sidebar -->
    <aside class="w-60 bg-[#141414] border-r border-[#2A2A2A] flex flex-col">
      <div class="p-5 border-b border-[#2A2A2A]">
        <div class="flex items-center gap-3">
          <Shield class="w-6 h-6 text-blue-500" />
          <div>
            <p class="text-sm font-semibold">Admin Panel</p>
            <p class="text-xs text-neutral-500">Robot Management</p>
          </div>
        </div>
      </div>

      <nav class="flex-1 p-3 space-y-1">
        <router-link
          to="/admin"
          exact
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-neutral-400 hover:text-white hover:bg-[#222] transition-colors"
          active-class="bg-[#222] text-white"
        >
          <Users class="w-4 h-4" />
          Users &amp; Robots
        </router-link>
        <router-link
          to="/admin/robots"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-neutral-400 hover:text-white hover:bg-[#222] transition-colors"
          active-class="bg-[#222] text-white"
        >
          <Cpu class="w-4 h-4" />
          Register Robot
        </router-link>
      </nav>

      <div class="p-3 border-t border-[#2A2A2A]">
        <button
          class="w-full flex items-center justify-center gap-2 py-2.5 bg-red-600/10 hover:bg-red-600/20 text-red-400 rounded-lg text-sm transition-colors border border-red-500/20"
          @click="handleLogout"
        >
          <LogOut class="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>

    <!-- Content -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>
</template>
