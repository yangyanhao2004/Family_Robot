<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import { getUserIdFromToken } from '@/services/websocket'
import { Bell, Mail, Volume2, Pencil, Trash2, ToggleLeft, ToggleRight, Plus } from 'lucide-vue-next'
import type { ReminderDto } from '@/types'

const reminders = ref<ReminderDto[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const editingId = ref<number | null>(null)
const editForm = ref({
  text: '',
  scheduledTime: '',
  method: 'EMAIL' as 'EMAIL' | 'VOICE',
  email: '',
  enabled: true,
})

const deleteConfirmId = ref<number | null>(null)
const showCreateForm = ref(false)
const creating = ref(false)

const userId = getUserIdFromToken()

function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function getDefaultTime(): string {
  const d = new Date(Date.now() + 5 * 60000)
  d.setSeconds(0, 0)
  return d.toISOString().substring(0, 16)
}

function openCreateForm() {
  editForm.value = {
    text: '',
    scheduledTime: getDefaultTime(),
    method: 'EMAIL',
    email: '',
    enabled: true,
  }
  showCreateForm.value = true
}

function cancelCreate() {
  showCreateForm.value = false
}

async function handleCreate() {
  const data: any = {
    userId,
    text: editForm.value.text,
    scheduledTime: editForm.value.scheduledTime,
    method: editForm.value.method,
    email: editForm.value.method === 'EMAIL' ? editForm.value.email : null,
  }
  creating.value = true
  try {
    const created = await api.createReminder(data)
    reminders.value.unshift(created)
    showCreateForm.value = false
  } catch (e) {
    alert((e as Error).message)
  } finally {
    creating.value = false
  }
}

async function loadReminders() {
  loading.value = true
  error.value = null
  try {
    reminders.value = await api.getReminders(userId)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function startEdit(r: ReminderDto) {
  editingId.value = r.id
  editForm.value = {
    text: r.text,
    scheduledTime: r.scheduledTime ? r.scheduledTime.substring(0, 16) : '',
    method: r.method,
    email: r.email || '',
    enabled: r.enabled,
  }
}

function cancelEdit() {
  editingId.value = null
}

function isFutureTime(iso: string): boolean {
  if (!iso) return false
  return new Date(iso).getTime() > Date.now()
}

async function saveEdit(id: number) {
  const data: any = {
    text: editForm.value.text,
    scheduledTime: editForm.value.scheduledTime,
    method: editForm.value.method,
    email: editForm.value.method === 'EMAIL' ? editForm.value.email : null,
    enabled: editForm.value.enabled,
  }
  try {
    await api.updateReminder(id, data)
    const idx = reminders.value.findIndex((r) => r.id === id)
    if (idx !== -1) {
      reminders.value[idx] = { ...reminders.value[idx], ...data }
      if (data.scheduledTime && isFutureTime(data.scheduledTime)) {
        reminders.value[idx].sent = false
      }
    }
    editingId.value = null
  } catch (e) {
    alert((e as Error).message)
  }
}

async function toggleEnabled(r: ReminderDto) {
  try {
    await api.updateReminder(r.id, { enabled: !r.enabled })
    r.enabled = !r.enabled
  } catch (e) {
    alert((e as Error).message)
  }
}

async function deleteReminder(id: number) {
  try {
    await api.deleteReminder(id)
    reminders.value = reminders.value.filter((r) => r.id !== id)
    deleteConfirmId.value = null
  } catch (e) {
    alert((e as Error).message)
  }
}

onMounted(loadReminders)
</script>

<template>
  <div class="flex flex-col h-full bg-[#0D0D0D]">
    <!-- Header -->
    <div class="flex items-center gap-3 px-5 py-4 border-b border-[#1F1F1F] shrink-0">
      <Bell class="w-5 h-5 text-blue-400" />
      <div class="flex-1">
        <p class="text-sm font-medium text-white">查看提醒</p>
        <p class="text-xs text-neutral-500">管理和配置你的提醒</p>
      </div>
      <button
        v-if="!showCreateForm"
        @click="openCreateForm"
        class="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-lg transition-colors"
      >
        <Plus class="w-3.5 h-3.5" />
        创建提醒
      </button>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto px-5 py-4">
      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center h-32">
        <div class="w-5 h-5 border-2 border-neutral-600 border-t-blue-500 rounded-full animate-spin" />
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-8">
        <p class="text-red-400 text-sm">{{ error }}</p>
        <button @click="loadReminders" class="mt-3 text-sm text-blue-400 hover:text-blue-300">重试</button>
      </div>

      <!-- Create form -->
      <div v-if="showCreateForm" class="mb-4 rounded-xl border border-blue-500/30 bg-[#141414] p-4 space-y-3">
        <p class="text-sm font-medium text-white">创建新提醒</p>
        <div>
          <label class="text-xs text-neutral-500 block mb-1">提醒内容</label>
          <input
            v-model="editForm.text"
            class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
            placeholder="例如：该喝水了"
          />
        </div>
        <div>
          <label class="text-xs text-neutral-500 block mb-1">提醒时间</label>
          <input
            v-model="editForm.scheduledTime"
            type="datetime-local"
            class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
          />
        </div>
        <div>
          <label class="text-xs text-neutral-500 block mb-1">提醒方式</label>
          <select
            v-model="editForm.method"
            class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
          >
            <option value="EMAIL">📧 邮件</option>
            <option value="VOICE">🔊 语音</option>
          </select>
        </div>
        <div v-if="editForm.method === 'EMAIL'">
          <label class="text-xs text-neutral-500 block mb-1">邮箱地址</label>
          <input
            v-model="editForm.email"
            type="email"
            class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
            placeholder="your@email.com"
          />
        </div>
        <div class="flex items-center gap-2 pt-1">
          <button
            @click="handleCreate"
            :disabled="creating || !editForm.text.trim()"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
          >
            {{ creating ? '创建中...' : '创建' }}
          </button>
          <button
            @click="cancelCreate"
            class="px-4 py-2 bg-[#2A2A2A] hover:bg-[#333] text-neutral-300 text-sm rounded-lg transition-colors"
          >
            取消
          </button>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="reminders.length === 0 && !showCreateForm" class="flex flex-col items-center justify-center h-48 text-neutral-600 gap-3">
        <Bell class="w-10 h-10" />
        <p class="text-sm">暂无提醒</p>
        <p class="text-xs">去 AI 对话中让 Jarvis 帮你设置提醒吧</p>
      </div>

      <!-- Reminders list -->
      <div v-else class="space-y-3">
        <div
          v-for="r in reminders"
          :key="r.id"
          :class="[
            'rounded-xl border p-4 transition-colors',
            r.enabled ? 'bg-[#141414] border-[#2A2A2A]' : 'bg-[#0D0D0D] border-[#1F1F1F] opacity-60',
          ]"
        >
          <!-- View mode -->
          <div v-if="editingId !== r.id">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <p :class="['text-sm font-medium', r.enabled ? 'text-white' : 'text-neutral-500']">
                  {{ r.text }}
                </p>
                <div class="flex items-center gap-3 mt-2 text-xs text-neutral-500">
                  <span>{{ formatTime(r.scheduledTime) }}</span>
                  <span class="flex items-center gap-1">
                    <Mail v-if="r.method === 'EMAIL'" class="w-3 h-3" />
                    <Volume2 v-else class="w-3 h-3" />
                    {{ r.method === 'EMAIL' ? '邮件' : '语音' }}
                  </span>
                  <span v-if="r.sent" class="text-green-500">已发送</span>
                </div>
              </div>

              <div class="flex items-center gap-1 shrink-0">
                <!-- Enable/disable toggle -->
                <button
                  @click="toggleEnabled(r)"
                  class="p-1.5 rounded-lg hover:bg-[#2A2A2A] transition-colors"
                  :title="r.enabled ? '关闭提醒' : '开启提醒'"
                >
                  <ToggleRight v-if="r.enabled" class="w-5 h-5 text-blue-400" />
                  <ToggleLeft v-else class="w-5 h-5 text-neutral-600" />
                </button>

                <!-- Edit -->
                <button
                  @click="startEdit(r)"
                  class="p-1.5 rounded-lg hover:bg-[#2A2A2A] text-neutral-500 hover:text-white transition-colors"
                  title="编辑"
                >
                  <Pencil class="w-4 h-4" />
                </button>

                <!-- Delete -->
                <button
                  @click="deleteConfirmId = r.id"
                  class="p-1.5 rounded-lg hover:bg-red-600/20 text-neutral-500 hover:text-red-400 transition-colors"
                  title="删除"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Delete confirmation -->
            <div v-if="deleteConfirmId === r.id" class="mt-3 flex items-center gap-2 text-xs">
              <span class="text-neutral-400">确定删除？</span>
              <button @click="deleteReminder(r.id)" class="text-red-400 hover:text-red-300 font-medium">删除</button>
              <button @click="deleteConfirmId = null" class="text-neutral-500 hover:text-neutral-400">取消</button>
            </div>
          </div>

          <!-- Edit mode -->
          <div v-else class="space-y-3">
            <div>
              <label class="text-xs text-neutral-500 block mb-1">提醒内容</label>
              <input
                v-model="editForm.text"
                class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
              />
            </div>
            <div>
              <label class="text-xs text-neutral-500 block mb-1">提醒时间</label>
              <input
                v-model="editForm.scheduledTime"
                type="datetime-local"
                class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
              />
            </div>
            <div>
              <label class="text-xs text-neutral-500 block mb-1">提醒方式</label>
              <select
                v-model="editForm.method"
                class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
              >
                <option value="EMAIL">📧 邮件</option>
                <option value="VOICE">🔊 语音</option>
              </select>
            </div>
            <div v-if="editForm.method === 'EMAIL'">
              <label class="text-xs text-neutral-500 block mb-1">邮箱地址</label>
              <input
                v-model="editForm.email"
                type="email"
                class="w-full bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
              />
            </div>
            <div class="flex items-center gap-2 pt-1">
              <button
                @click="saveEdit(r.id)"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
              >
                保存
              </button>
              <button
                @click="cancelEdit"
                class="px-4 py-2 bg-[#2A2A2A] hover:bg-[#333] text-neutral-300 text-sm rounded-lg transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
