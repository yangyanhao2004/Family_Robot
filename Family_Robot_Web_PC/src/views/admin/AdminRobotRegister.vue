<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/api'
import { Cpu, PlusCircle, Search, ArrowUpDown, ArrowUp, ArrowDown, X } from 'lucide-vue-next'

interface AdminRobot {
  id: number
  serialNumber: string
  boundUserEmail: string | null
  createdAt: string
}

const robots = ref<AdminRobot[]>([])
const serialNumber = ref('')
const loading = ref(false)
const message = ref<string | null>(null)
const error = ref<string | null>(null)

// Search / Sort / Filter
const searchQuery = ref('')
const sortAsc = ref(true)
const filterStart = ref('')
const filterEnd = ref('')
const filterStartTime = ref('')
const filterEndTime = ref('')

const filteredRobots = computed(() => {
  let result = [...robots.value]

  // Search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(r => r.serialNumber.toLowerCase().includes(q))
  }

  // Time range filter
  if (filterStart.value) {
    const start = filterStartTime.value
      ? new Date(filterStart.value + 'T' + filterStartTime.value).getTime()
      : new Date(filterStart.value + 'T00:00:00').getTime()
    result = result.filter(r => new Date(r.createdAt).getTime() >= start)
  }
  if (filterEnd.value) {
    const end = filterEndTime.value
      ? new Date(filterEnd.value + 'T' + filterEndTime.value).getTime()
      : new Date(filterEnd.value + 'T23:59:59').getTime()
    result = result.filter(r => new Date(r.createdAt).getTime() <= end)
  }

  // Sort by createdAt
  result.sort((a, b) => {
    const cmp = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    return sortAsc.value ? cmp : -cmp
  })

  return result
})

function clearFilters() {
  searchQuery.value = ''
  filterStart.value = ''
  filterEnd.value = ''
  filterStartTime.value = ''
  filterEndTime.value = ''
  sortAsc.value = true
}

const hasFilters = computed(() =>
  searchQuery.value.trim() || filterStart.value || filterEnd.value || !sortAsc.value
)

onMounted(async () => {
  try {
    robots.value = await api.getAdminRobots()
  } catch {
    // ignore
  }
})

async function handleRegister() {
  if (!serialNumber.value.trim()) return
  loading.value = true
  error.value = null
  message.value = null
  try {
    await api.registerRobot(serialNumber.value.trim())
    message.value = `Robot "${serialNumber.value.trim()}" registered successfully`
    serialNumber.value = ''
    robots.value = await api.getAdminRobots()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="p-6 space-y-6">
    <div>
      <h2 class="text-lg font-semibold">Register Robot</h2>
      <p class="text-sm text-neutral-500 mt-1">Add a new robot serial number to the system</p>
    </div>

    <div class="bg-[#141414] border border-[#2A2A2A] rounded-lg p-6 max-w-lg">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center">
          <Cpu class="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <p class="text-sm font-medium text-white">New Robot Serial</p>
          <p class="text-xs text-neutral-500">Format: RBT-XXXXX-XXX</p>
        </div>
      </div>

      <div class="flex gap-3">
        <input
          v-model="serialNumber"
          type="text"
          placeholder="e.g. RBT-00001-ABC"
          class="flex-1 bg-[#0D0D0D] border border-[#2A2A2A] text-white rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-500 transition-colors font-mono"
          @keyup.enter="handleRegister"
        />
        <button
          :disabled="loading || !serialNumber.trim()"
          class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          @click="handleRegister"
        >
          <PlusCircle class="w-4 h-4" />
          {{ loading ? 'Registering...' : 'Register' }}
        </button>
      </div>

      <div v-if="message" class="mt-4 p-3 bg-green-600/10 border border-green-500/20 rounded-lg">
        <p class="text-sm text-green-400">{{ message }}</p>
      </div>

      <div v-if="error" class="mt-4 p-3 bg-red-600/10 border border-red-500/20 rounded-lg">
        <p class="text-sm text-red-400">{{ error }}</p>
      </div>
    </div>

    <!-- Robot list -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-white">All Robots ({{ filteredRobots.length }})</h3>
        <button
          v-if="hasFilters"
          @click="clearFilters"
          class="flex items-center gap-1 text-xs text-neutral-400 hover:text-white transition-colors"
        >
          <X class="w-3 h-3" />
          Clear filters
        </button>
      </div>

      <!-- Toolbar: Search + Sort + Filter -->
      <div class="flex flex-wrap items-center gap-3 mb-4">
        <!-- Search -->
        <div class="relative flex-1 min-w-[200px] max-w-xs">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search serial number..."
            class="w-full bg-[#141414] border border-[#2A2A2A] text-white rounded-lg pl-9 pr-4 py-2 text-sm outline-none focus:border-blue-500 transition-colors font-mono"
          />
        </div>

        <!-- Sort toggle -->
        <button
          @click="sortAsc = !sortAsc"
          class="flex items-center gap-1.5 px-3 py-2 bg-[#141414] border border-[#2A2A2A] rounded-lg text-sm text-neutral-300 hover:text-white hover:border-[#444] transition-colors"
          title="Toggle sort order"
        >
          <ArrowUpDown v-if="false" class="w-4 h-4" />
          <ArrowUp v-if="sortAsc" class="w-4 h-4 text-blue-400" />
          <ArrowDown v-else class="w-4 h-4 text-blue-400" />
          {{ sortAsc ? 'Oldest first' : 'Newest first' }}
        </button>

        <!-- Date range filter -->
        <div class="flex items-center gap-2">
          <input
            v-model="filterStart"
            type="date"
            class="bg-[#141414] border border-[#2A2A2A] text-white rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors w-[150px]"
            title="Start date"
          />
          <input
            v-model="filterStartTime"
            type="time"
            class="bg-[#141414] border border-[#2A2A2A] text-white rounded-lg px-2 py-2 text-sm outline-none focus:border-blue-500 transition-colors w-[110px]"
            title="Start time (optional)"
          />
          <span class="text-neutral-500 text-xs">—</span>
          <input
            v-model="filterEnd"
            type="date"
            class="bg-[#141414] border border-[#2A2A2A] text-white rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors w-[150px]"
            title="End date"
          />
          <input
            v-model="filterEndTime"
            type="time"
            class="bg-[#141414] border border-[#2A2A2A] text-white rounded-lg px-2 py-2 text-sm outline-none focus:border-blue-500 transition-colors w-[110px]"
            title="End time (optional)"
          />
        </div>
      </div>

      <div v-if="filteredRobots.length === 0" class="text-sm text-neutral-600 py-4">
        <span v-if="robots.length === 0">No robots registered yet</span>
        <span v-else>No robots match the current filters</span>
      </div>
      <div v-else class="space-y-2">
        <div
          v-for="r in filteredRobots"
          :key="r.id"
          class="bg-[#141414] border border-[#2A2A2A] rounded-lg p-4 flex items-center justify-between"
        >
          <div>
            <p class="text-sm font-mono text-white">{{ r.serialNumber }}</p>
            <p class="text-xs text-neutral-500 mt-1">
              Registered: {{ formatTime(r.createdAt) }}
              <span v-if="r.boundUserEmail" class="ml-3 text-blue-400">Bound to: {{ r.boundUserEmail }}</span>
              <span v-else class="ml-3 text-amber-400">Unbound</span>
            </p>
          </div>
          <span
            :class="[
              'px-2 py-0.5 rounded text-xs font-medium',
              r.boundUserEmail ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20' : 'bg-amber-600/10 text-amber-400 border border-amber-500/20',
            ]"
          >
            {{ r.boundUserEmail ? 'Bound' : 'Free' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
