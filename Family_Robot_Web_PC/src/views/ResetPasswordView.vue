<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'
import { Bot, Mail, Lock, KeyRound, ChevronRight, ArrowLeft } from 'lucide-vue-next'

const router = useRouter()

const step = ref<1 | 2>(1)
const email = ref('')
const code = ref('')
const newPassword = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

function goBack() {
  const token = localStorage.getItem('auth_token')
  if (token) {
    router.push({ name: 'dashboard' })
  } else {
    router.push({ name: 'login' })
  }
}

async function handleSendCode() {
  if (!email.value) return
  isLoading.value = true
  errorMsg.value = ''
  try {
    await api.sendResetPasswordCode(email.value)
    step.value = 2
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    isLoading.value = false
  }
}

async function handleReset() {
  if (!code.value || !newPassword.value) return
  isLoading.value = true
  errorMsg.value = ''
  try {
    await api.resetPassword(email.value, code.value, newPassword.value)
    router.push('/login')
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="flex h-screen bg-[#1A1A1A] text-white">
    <!-- Left panel -->
    <div class="hidden lg:flex flex-1 bg-[#141414] relative items-center justify-center border-r border-[#2A2A2A] overflow-hidden">
      <div class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-amber-600/20 blur-[120px] rounded-full" />
      <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-orange-600/20 blur-[120px] rounded-full" />

      <div class="relative z-10 flex flex-col items-center gap-6">
        <div class="w-24 h-24 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-amber-500/20">
          <Bot class="w-12 h-12 text-white" />
        </div>
        <div class="text-center space-y-2">
          <h1 class="text-3xl font-bold tracking-tight">Reset Password</h1>
          <p class="text-neutral-400 max-w-sm">通过邮箱验证码重置您的登录密码</p>
        </div>
      </div>
    </div>

    <!-- Right panel - Reset Form -->
    <div class="flex-1 flex items-center justify-center p-8">
      <div class="w-full max-w-md space-y-8">
        <div class="flex items-center gap-3">
          <button
            @click="goBack"
            class="p-2 hover:bg-[#222] rounded-lg transition-colors text-neutral-400 hover:text-white"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div>
            <h2 class="text-2xl font-semibold">重置密码</h2>
            <p class="text-sm text-neutral-400">步骤 {{ step }}/2</p>
          </div>
        </div>

        <!-- Step indicators -->
        <div class="flex gap-2">
          <div :class="['h-1 flex-1 rounded-full transition-colors', step >= 1 ? 'bg-amber-500' : 'bg-[#2A2A2A]']" />
          <div :class="['h-1 flex-1 rounded-full transition-colors', step >= 2 ? 'bg-amber-500' : 'bg-[#2A2A2A]']" />
        </div>

        <!-- Error -->
        <div v-if="errorMsg" class="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl p-3">
          {{ errorMsg }}
        </div>

        <!-- Step 1: Email -->
        <form v-if="step === 1" @submit.prevent="handleSendCode" class="space-y-5">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-400 px-1">邮箱地址</label>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
              <input
                v-model="email"
                type="email"
                required
                placeholder="请输入注册邮箱"
                class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-amber-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading || !email"
            class="w-full bg-amber-600 hover:bg-amber-500 text-white font-medium py-3.5 rounded-xl transition-all shadow-[0_4px_12px_rgba(217,119,6,0.2)] hover:shadow-[0_4px_16px_rgba(217,119,6,0.4)] flex items-center justify-center gap-2 group disabled:opacity-50"
          >
            {{ isLoading ? '发送中...' : '发送验证码' }}
            <ChevronRight class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </form>

        <!-- Step 2: Code + New Password -->
        <form v-else @submit.prevent="handleReset" class="space-y-5">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-400 px-1">验证码</label>
            <div class="relative">
              <KeyRound class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
              <input
                v-model="code"
                type="text"
                required
                maxlength="6"
                placeholder="请输入6位验证码"
                class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-amber-500 transition-colors tracking-[8px] text-center text-lg"
              />
            </div>
            <p class="text-xs text-neutral-500 px-1 pt-1">验证码已发送至 <span class="text-amber-400">{{ email }}</span></p>
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-400 px-1">新密码</label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
              <input
                v-model="newPassword"
                type="password"
                required
                placeholder="请设置新密码"
                class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-amber-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading || code.length < 6 || !newPassword"
            class="w-full bg-amber-600 hover:bg-amber-500 text-white font-medium py-3.5 rounded-xl transition-all shadow-[0_4px_12px_rgba(217,119,6,0.2)] hover:shadow-[0_4px_16px_rgba(217,119,6,0.4)] flex items-center justify-center gap-2 group disabled:opacity-50"
          >
            {{ isLoading ? '重置中...' : '重置密码' }}
            <ChevronRight class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            type="button"
            @click="step = 1; errorMsg = ''"
            class="w-full text-neutral-400 hover:text-white text-sm py-2 transition-colors"
          >
            返回修改邮箱
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
