<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'
import { Bot, Mail, Lock, Cpu, KeyRound, ChevronRight, ArrowLeft, UserRound, Phone } from 'lucide-vue-next'

const router = useRouter()

const step = ref<1 | 2>(1)
const email = ref('')
const password = ref('')
const serialNumber = ref('')
const emergencyContactName = ref('')
const emergencyContactEmail = ref('')
const code = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

async function handleSendCode() {
  if (!email.value || !password.value || !serialNumber.value) return
  isLoading.value = true
  errorMsg.value = ''
  try {
    await api.register(email.value, password.value, serialNumber.value,
      emergencyContactName.value || undefined, emergencyContactEmail.value || undefined)
    step.value = 2
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    isLoading.value = false
  }
}

async function handleVerify() {
  if (!code.value) return
  isLoading.value = true
  errorMsg.value = ''
  try {
    await api.verify(email.value, code.value)
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
      <div class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-emerald-600/20 blur-[120px] rounded-full" />
      <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600/20 blur-[120px] rounded-full" />

      <div class="relative z-10 flex flex-col items-center gap-6">
        <div class="w-24 h-24 bg-gradient-to-br from-emerald-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-emerald-500/20">
          <Bot class="w-12 h-12 text-white" />
        </div>
        <div class="text-center space-y-2">
          <h1 class="text-3xl font-bold tracking-tight">Create Account</h1>
          <p class="text-neutral-400 max-w-sm">注册新账户，绑定您的机器人设备</p>
        </div>
      </div>
    </div>

    <!-- Right panel - Registration Form -->
    <div class="flex-1 flex items-center justify-center p-8">
      <div class="w-full max-w-md space-y-8">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/login')"
            class="p-2 hover:bg-[#222] rounded-lg transition-colors text-neutral-400 hover:text-white"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div>
            <h2 class="text-2xl font-semibold">注册账户</h2>
            <p class="text-sm text-neutral-400">步骤 {{ step }}/2</p>
          </div>
        </div>

        <!-- Step indicators -->
        <div class="flex gap-2">
          <div :class="['h-1 flex-1 rounded-full transition-colors', step >= 1 ? 'bg-emerald-500' : 'bg-[#2A2A2A]']" />
          <div :class="['h-1 flex-1 rounded-full transition-colors', step >= 2 ? 'bg-emerald-500' : 'bg-[#2A2A2A]']" />
        </div>

        <!-- Error -->
        <div v-if="errorMsg" class="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl p-3">
          {{ errorMsg }}
        </div>

        <!-- Step 1: Email + Password + Serial -->
        <form v-if="step === 1" @submit.prevent="handleSendCode" class="space-y-5">
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
                  class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
            </div>

            <div class="space-y-1">
              <label class="text-xs font-medium text-neutral-400 px-1">登录密码</label>
              <div class="relative">
                <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                <input
                  v-model="password"
                  type="password"
                  required
                  placeholder="请设置密码"
                  class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
            </div>

            <div class="space-y-1">
              <label class="text-xs font-medium text-neutral-400 px-1">机器人序列号</label>
              <div class="relative">
                <Cpu class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                <input
                  v-model="serialNumber"
                  type="text"
                  required
                  placeholder="请输入产品序列号"
                  class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-emerald-500 transition-colors"
                />
              </div>
            </div>

            <!-- Emergency Contact -->
            <div class="pt-2 border-t border-[#2A2A2A]">
              <p class="text-xs text-neutral-500 mb-3 px-1">紧急联系人（可选，用于摔倒等紧急情况通知）</p>
              <div class="space-y-3">
                <div class="relative">
                  <UserRound class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                  <input
                    v-model="emergencyContactName"
                    type="text"
                    placeholder="紧急联系人姓名"
                    class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-red-500 transition-colors"
                  />
                </div>
                <div class="relative">
                  <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                  <input
                    v-model="emergencyContactEmail"
                    type="email"
                    placeholder="紧急联系人邮箱"
                    class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-red-500 transition-colors"
                  />
                </div>
              </div>
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading || !email || !password || !serialNumber"
            class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3.5 rounded-xl transition-all shadow-[0_4px_12px_rgba(16,185,129,0.2)] hover:shadow-[0_4px_16px_rgba(16,185,129,0.4)] flex items-center justify-center gap-2 group disabled:opacity-50"
          >
            {{ isLoading ? '发送中...' : '发送验证码' }}
            <ChevronRight class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </form>

        <!-- Step 2: Verification Code -->
        <form v-else @submit.prevent="handleVerify" class="space-y-5">
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
                class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-xl py-3 pl-10 pr-4 outline-none focus:border-emerald-500 transition-colors tracking-[8px] text-center text-lg"
              />
            </div>
            <p class="text-xs text-neutral-500 px-1 pt-1">验证码已发送至 <span class="text-emerald-400">{{ email }}</span>，5分钟内有效</p>
          </div>

          <button
            type="submit"
            :disabled="isLoading || code.length < 6"
            class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3.5 rounded-xl transition-all shadow-[0_4px_12px_rgba(16,185,129,0.2)] hover:shadow-[0_4px_16px_rgba(16,185,129,0.4)] flex items-center justify-center gap-2 group disabled:opacity-50"
          >
            {{ isLoading ? '验证中...' : '验证并注册' }}
            <ChevronRight class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            type="button"
            @click="step = 1; errorMsg = ''"
            class="w-full text-neutral-400 hover:text-white text-sm py-2 transition-colors"
          >
            返回修改信息
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
