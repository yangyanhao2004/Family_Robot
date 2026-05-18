<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { LayoutDashboard, Image as ImageIcon, Settings as SettingsIcon, User, MessageCircle, Bell } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const allNavItems = [
  { path: '/home', icon: LayoutDashboard, label: '仪表板', adminOnly: false },
  { path: '/home/ai-chat', icon: MessageCircle, label: 'AI对话', userOnly: true },
  { path: '/home/album', icon: ImageIcon, label: '相册管理', adminOnly: false },
  { path: '/home/reminders', icon: Bell, label: '查看提醒', userOnly: true },
  { path: '/home/settings', icon: SettingsIcon, label: '设置', adminOnly: false },
  { path: '/home/user', icon: User, label: '用户', adminOnly: false },
]

const navItems = allNavItems.filter((item) => {
  if (item.userOnly && authStore.isAdmin) return false
  return true
})

function isActive(path: string) {
  if (path === '/home') return route.path === '/home'
  return route.path.startsWith(path)
}

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <nav class="w-[88px] bg-[#141414] flex flex-col items-center py-8 gap-8 shrink-0 z-10 shadow-xl">
    <button
      v-for="item in navItems"
      :key="item.path"
      @click="navigate(item.path)"
      :class="[
        'flex flex-col items-center gap-2 p-3 w-full transition-colors relative',
        isActive(item.path)
          ? `text-white after:content-[''] after:absolute after:left-0 after:top-1/2 after:-translate-y-1/2 after:w-1 after:h-8 after:bg-blue-500 after:rounded-r`
          : 'text-neutral-500 hover:text-neutral-300',
      ]"
    >
      <component :is="item.icon" class="w-6 h-6" />
      <span class="text-[11px] font-medium">{{ item.label }}</span>
    </button>
  </nav>
</template>
