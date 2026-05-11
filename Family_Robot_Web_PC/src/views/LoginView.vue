<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { Bot, Mail, Lock, KeyRound, ChevronRight } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()

const loginMethod = ref<'password' | 'code'>('password')
const email = ref('')
const password = ref('')
const code = ref('')
const isSendingCode = ref(false)

function handleSendCode() {
  if (!email.value) return
  isSendingCode.value = true
  setTimeout(() => {
    isSendingCode.value = false
    alert('验证码已发送至邮箱')
  }, 1000)
}

async function handleLogin(e: Event) {
  e.preventDefault()
  try {
    await auth.login(email.value, password.value || 'demo')
    router.push('/home')
  } catch {
    // ignore
  }
}
</script>

<template>
  <div class="flex h-screen bg-[#1A1A1A] text-white">
    <!-- Left panel - Decorative/Branding -->
    <div class="hidden lg:flex flex-1 bg-[#141414] relative items-center justify-center border-r border-[#2A2A2A] overflow-hidden">
      <div class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 blur-[120px] rounded-full" />
      <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-600/20 blur-[120px] rounded-full" />

      <div class="relative z-10 flex flex-col items-center gap-6">
        <div class="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/20">
          <Bot class="w-12 h-12 text-white" />
        </div>
        <div class="text-center space-y-2">
          <h1 class="text-3xl font-bold tracking-tight">Robot Control Panel</h1>
          <p class="text-neutral-400 max-w-sm">专业的工业级远程控制终端，实时监控、精准操作</p>
        </div>
      </div>
    </div>

    <!-- Right panel - Login Form -->
    <div class="flex-1 flex items-center justify-center p-8">
      <div class="w-full max-w-md space-y-8">
        <div class="text-center lg:text-left space-y-2">
          <h2 class="text-2xl font-semibold">欢迎回来</h2>
          <p class="text-sm text-neutral-400">请选择登录方式进入控制面板</p>
        </div>

        <div class="flex p-1 bg-[#222] rounded-xl">
          <button
            :class="['flex-1 py-2 text-sm font-medium rounded-lg transition-all', loginMethod === 'password' ? 'bg-[#333] text-white shadow' : 'text-neutral-400 hover:text-white']"
            @click="loginMethod = 'password'"
          >
            密码登录
          </button>
          <button
            :class="['flex-1 py-2 text-sm font-medium rounded-lg transition-all', loginMethod === 'code' ? 'bg-[#333] text-white shadow' : 'text-neutral-400 hover:text-white']"
            @click="loginMethod = 'code'"
          >
            验证码登录
          </button>
        </div>

        <form @submit="handleLogin" class="space-y-5">
          <div class="space-y-4">
            <div class="space-y-1">
              <label class="text-xs font-medium text-neutral-400 px-1">邮箱地址</label>
              <div class="relative">
                <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                <input
                  v-model="email"
                  type="email"
                  required
                  placeholder="请输入邮箱"
                  class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            <template v-if="loginMethod === 'password'">
              <div class="space-y-1">
                <label class="text-xs font-medium text-neutral-400 px-1">登录密码</label>
                <div class="relative">
                  <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                  <input
                    v-model="password"
                    type="password"
                    required
                    placeholder="请输入密码"
                    class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-blue-500 transition-colors"
                  />
                </div>
              </div>
            </template>
            <template v-else>
              <div class="space-y-1">
                <label class="text-xs font-medium text-neutral-400 px-1">验证码</label>
                <div class="flex gap-3">
                  <div class="relative flex-1">
                    <KeyRound class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                    <input
                      v-model="code"
                      type="text"
                      required
                      placeholder="请输入验证码"
                      class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-blue-500 transition-colors"
                    />
                  </div>
                  <button
                    type="button"
                    @click="handleSendCode"
                    :disabled="isSendingCode || !email"
                    class="px-4 py-3 bg-[#222] hover:bg-[#333] border border-[#2A2A2A] rounded-xl text-sm font-medium transition-colors disabled:opacity-50 whitespace-nowrap"
                  >
                    {{ isSendingCode ? '发送中...' : '获取验证码' }}
                  </button>
                </div>
              </div>
            </template>
          </div>

          <button
            type="submit"
            :disabled="auth.isLoading"
            class="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3.5 rounded-xl transition-all shadow-[0_4px_12px_rgba(37,99,235,0.2)] hover:shadow-[0_4px_16px_rgba(37,99,235,0.4)] flex items-center justify-center gap-2 group mt-6 disabled:opacity-50"
          >
            {{ auth.isLoading ? '登录中...' : '登录控制台' }}
            <ChevronRight class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
