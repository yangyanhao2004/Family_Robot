<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue';

interface Props {
  streamUrl: string;
  streamType?: 'mjpeg' | 'http' | 'webrtc';
  autoplay?: boolean;
  muted?: boolean;
  width?: string;
  height?: string;
}

const props = withDefaults(defineProps<Props>(), {
  streamType: 'mjpeg',
  autoplay: true,
  muted: true,
  width: '100%',
  height: '100%',
});

const videoElement = ref<HTMLVideoElement | null>(null);
const imgElement = ref<HTMLImageElement | null>(null);
const isLoading = ref(true);
const errorMessage = ref<string | null>(null);

const loadStream = () => {
  if (!props.streamUrl) {
    isLoading.value = true;
    errorMessage.value = null;
    if (imgElement.value) {
      imgElement.value.src = '';
    }
    if (videoElement.value) {
      videoElement.value.pause();
      videoElement.value.src = '';
    }
    return;
  }

  isLoading.value = true;
  errorMessage.value = null;

  if (props.streamType === 'mjpeg') {
    loadMjpegStream();
    return;
  }

  if (props.streamType === 'http') {
    loadHttpStream();
    return;
  }

  isLoading.value = false;
  errorMessage.value = 'WebRTC mode is not implemented yet';
};

const loadMjpegStream = () => {
  if (!imgElement.value) {
    return;
  }

  imgElement.value.onload = () => {
    isLoading.value = false;
    errorMessage.value = null;
  };

  imgElement.value.onerror = () => {
    isLoading.value = false;
    errorMessage.value = 'Unable to load MJPEG stream';
  };

  imgElement.value.src = props.streamUrl;
};

const loadHttpStream = () => {
  if (!videoElement.value) {
    return;
  }

  videoElement.value.onloadedmetadata = () => {
    isLoading.value = false;
    errorMessage.value = null;
  };

  videoElement.value.onerror = () => {
    isLoading.value = false;
    errorMessage.value = 'Unable to load HTTP video stream';
  };

  videoElement.value.src = props.streamUrl;
};

watch(() => [props.streamUrl, props.streamType], loadStream);

onMounted(loadStream);

onUnmounted(() => {
  if (videoElement.value) {
    videoElement.value.pause();
    videoElement.value.src = '';
  }
  if (imgElement.value) {
    imgElement.value.src = '';
  }
});
</script>

<template>
  <div class="video-stream-container" :style="{ width: props.width, height: props.height }">
    <div v-if="isLoading" class="stream-loading">
      <p>Waiting for camera stream...</p>
    </div>

    <div v-else-if="errorMessage" class="stream-error">
      <div class="error-icon">!</div>
      <p>{{ errorMessage }}</p>
    </div>

    <img
      v-else-if="streamType === 'mjpeg'"
      ref="imgElement"
      class="video-stream"
      alt="MJPEG stream"
    />

    <video
      v-else-if="streamType === 'http'"
      ref="videoElement"
      class="video-stream"
      :autoplay="autoplay"
      :muted="muted"
      playsinline
    >
      Your browser does not support video playback.
    </video>

    <div v-else class="stream-placeholder">
      <p>WebRTC placeholder</p>
    </div>
  </div>
</template>

<style scoped>
.video-stream-container {
  position: relative;
  background-color: #000;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.video-stream {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stream-loading,
.stream-error,
.stream-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 10;
}

.stream-error {
  color: #ff7676;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}
</style>
