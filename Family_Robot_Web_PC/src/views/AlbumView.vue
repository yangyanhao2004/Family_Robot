<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import { Download, Trash2, Check } from 'lucide-vue-next'
import type { AlbumPhoto } from '@/types'

const PYTHON_BACKEND = import.meta.env.VITE_BACKEND_HTTP_URL || 'http://localhost:8080'

function fullUrl(url: string) {
  return url.startsWith('http') ? url : `${PYTHON_BACKEND}${url}`
}

const photos = ref<AlbumPhoto[]>([])
const selected = ref<string[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    photos.value = await api.getPhotos()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
})

function toggleSelect(id: string) {
  const idx = selected.value.indexOf(id)
  if (idx >= 0) selected.value.splice(idx, 1)
  else selected.value.push(id)
}

function deleteSelected() {
  photos.value = photos.value.filter((p) => !selected.value.includes(p.id))
  selected.value = []
}

function selectAll() {
  if (selected.value.length === photos.value.length) {
    selected.value = []
  } else {
    selected.value = photos.value.map((p) => p.id)
  }
}

function downloadPhoto(url: string) {
  window.open(url, '_blank')
}
</script>

<template>
  <div class="p-4">
    <div class="sticky top-0 bg-[#1A1A1A] pb-3 mb-3 border-b border-[#2A2A2A] z-10">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-neutral-300 uppercase tracking-wider">
          Photo Album
          <span v-if="selected.length" class="ml-2 text-blue-400">({{ selected.length }} selected)</span>
        </h3>
        <div class="flex gap-2">
          <button
            class="px-3 py-1.5 text-xs text-neutral-400 hover:text-white border border-[#2A2A2A] rounded transition-colors"
            @click="selectAll"
          >
            {{ selected.length === photos.length ? 'Deselect All' : 'Select All' }}
          </button>
          <button
            v-if="selected.length"
            class="px-3 py-1.5 text-xs text-red-400 hover:text-red-300 border border-red-500/30 rounded flex items-center gap-1 transition-colors"
            @click="deleteSelected"
          >
            <Trash2 class="w-3 h-3" /> Delete
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16 text-neutral-500">Loading...</div>

    <div v-else-if="error" class="flex flex-col items-center gap-3 py-16 text-neutral-500">
      <p>Failed to load photos</p>
      <p class="text-xs text-red-400">{{ error }}</p>
    </div>

    <div v-else class="grid grid-cols-2 gap-3">
      <div
        v-for="photo in photos"
        :key="photo.id"
        class="group relative aspect-square rounded-lg overflow-hidden cursor-pointer bg-[#141414]"
        @click="toggleSelect(photo.id)"
      >
        <img
          :src="fullUrl(photo.url)"
          class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
          alt=""
        />
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors" />
        <p class="absolute bottom-2 left-2 text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity">
          {{ photo.date }}
        </p>

        <!-- Select badge -->
        <div
          :class="[
            'absolute top-2 right-2 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors',
            selected.includes(photo.id)
              ? 'bg-blue-600 border-blue-600'
              : 'border-white/40 group-hover:border-white/80',
          ]"
        >
          <Check v-if="selected.includes(photo.id)" class="w-3.5 h-3.5 text-white" />
        </div>

        <button
          class="absolute top-2 left-2 w-7 h-7 rounded-full bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          @click.stop="downloadPhoto(fullUrl(photo.url))"
        >
          <Download class="w-3.5 h-3.5 text-white" />
        </button>
      </div>
    </div>
  </div>
</template>
