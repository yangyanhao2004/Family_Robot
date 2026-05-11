<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { LayoutDashboard, Image as ImageIcon, Settings as SettingsIcon, User } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

const navItems = [
  { path: '/home', icon: LayoutDashboard, label: '仪表板' },
  { path: '/home/album', icon: ImageIcon, label: '相册管理' },
  { path: '/home/settings', icon: SettingsIcon, label: '设置' },
  { path: '/home/user', icon: User, label: '用户' },
]

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
