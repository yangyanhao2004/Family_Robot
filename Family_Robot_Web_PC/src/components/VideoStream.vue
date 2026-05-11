<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

interface Props {
  streamUrl: string
  streamType?: 'mjpeg' | 'http'
  autoplay?: boolean
  muted?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  streamType: 'mjpeg',
  autoplay: true,
  muted: true,
})

const imgRef = ref<HTMLImageElement | null>(null)
const isLoading = ref(true)
const errorMsg = ref<string | null>(null)

function clear() {
  if (imgRef.value) imgRef.value.src = ''
  isLoading.value = true
  errorMsg.value = null
}

function load() {
  clear()
  if (!props.streamUrl) return

  if (!imgRef.value) return
  imgRef.value.onload = () => {
    isLoading.value = false
    errorMsg.value = null
  }
  imgRef.value.onerror = () => {
    isLoading.value = false
    errorMsg.value = 'Failed to load MJPEG stream'
  }
  imgRef.value.src = props.streamUrl
}

watch(() => props.streamUrl, load)
onMounted(load)
onUnmounted(clear)
</script>

<template>
  <div class="relative w-full h-full bg-black overflow-hidden">
    <img
      v-if="streamType === 'mjpeg'"
      ref="imgRef"
      class="w-full h-full object-contain"
      alt="Camera stream"
    />

    <div
      v-if="isLoading && !errorMsg"
      class="absolute inset-0 flex flex-col items-center justify-center bg-black/80 z-10"
    >
      <div class="w-8 h-8 border-2 border-neutral-600 border-t-blue-500 rounded-full animate-spin mb-3" />
      <p class="text-sm text-neutral-400">Waiting for camera...</p>
    </div>

    <div
      v-if="errorMsg"
      class="absolute inset-0 flex flex-col items-center justify-center bg-black/80 z-10"
    >
      <span class="text-3xl mb-2">!</span>
      <p class="text-sm text-red-400">{{ errorMsg }}</p>
    </div>
  </div>
</template>
