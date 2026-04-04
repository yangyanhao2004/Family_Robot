<script setup lang="ts">
// VideoStream.vue - 视频流显示组件
// 设计意图：提供通用的视频流展示组件，支持 MJPEG/HTTP 视频流，预留 WebRTC 扩展接口

import { ref, onMounted, onUnmounted, watch } from 'vue';

// 组件属性
interface Props {
  // 视频流 URL
  streamUrl: string;
  // 视频流类型：'mjpeg' | 'http' | 'webrtc'
  streamType?: 'mjpeg' | 'http' | 'webrtc';
  // 是否自动播放
  autoplay?: boolean;
  // 是否静音
  muted?: boolean;
  // 视频宽度
  width?: string;
  // 视频高度
  height?: string;
}

const props = withDefaults(defineProps<Props>(), {
  streamType: 'mjpeg',
  autoplay: true,
  muted: true,
  width: '100%',
  height: '100%',
});

// 响应式数据
const videoElement = ref<HTMLVideoElement | null>(null);
const imgElement = ref<HTMLImageElement | null>(null);
const isLoading = ref(true);
const errorMessage = ref<string | null>(null);

// 加载视频流
const loadStream = () => {
  if (!props.streamUrl) {
    errorMessage.value = '视频流 URL 未设置';
    isLoading.value = false;
    return;
  }

  isLoading.value = true;
  errorMessage.value = null;

  try {
    switch (props.streamType) {
      case 'mjpeg':
        loadMjpegStream();
        break;
      case 'http':
        loadHttpStream();
        break;
      case 'webrtc':
        // 预留 WebRTC 实现
        errorMessage.value = 'WebRTC 模式暂未实现';
        isLoading.value = false;
        break;
      default:
        errorMessage.value = '不支持的视频流类型';
        isLoading.value = false;
    }
  } catch (error) {
    console.error('加载视频流失败:', error);
    errorMessage.value = '加载视频流失败';
    isLoading.value = false;
  }
};

// 加载 MJPEG 流（使用 img 标签）
const loadMjpegStream = () => {
  if (imgElement.value) {
    imgElement.value.src = props.streamUrl;
    imgElement.value.onload = () => {
      isLoading.value = false;
    };
    imgElement.value.onerror = () => {
      errorMessage.value = '无法加载 MJPEG 流';
      isLoading.value = false;
    };
  }
};

// 加载 HTTP 视频流（使用 video 标签）
const loadHttpStream = () => {
  if (videoElement.value) {
    videoElement.value.src = props.streamUrl;
    videoElement.value.onloadedmetadata = () => {
      isLoading.value = false;
    };
    videoElement.value.onerror = () => {
      errorMessage.value = '无法加载 HTTP 视频流';
      isLoading.value = false;
    };
  }
};

// 监听属性变化
watch(
  () => [props.streamUrl, props.streamType],
  () => {
    loadStream();
  },
  { deep: true }
);

// 生命周期钩子
onMounted(() => {
  loadStream();
});

onUnmounted(() => {
  // 清理资源
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
    <!-- 加载状态 -->
    <div v-if="isLoading" class="stream-loading">
      <p>未连接</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="errorMessage" class="stream-error">
      <div class="error-icon">⚠️</div>
      <p>{{ errorMessage }}</p>
    </div>

    <!-- MJPEG 流 -->
    <img
      v-else-if="streamType === 'mjpeg'"
      ref="imgElement"
      class="video-stream"
      alt="MJPEG 视频流"
    />

    <!-- HTTP 视频流 -->
    <video
      v-else-if="streamType === 'http'"
      ref="videoElement"
      class="video-stream"
      :autoplay="autoplay"
      :muted="muted"
      playsinline
    >
      您的浏览器不支持视频播放。
    </video>

    <!-- WebRTC 预留位置 -->
    <div v-else-if="streamType === 'webrtc'" class="stream-placeholder">
      <div class="placeholder-icon">📹</div>
      <p>WebRTC 视频流</p>
      <p class="placeholder-hint">后续实现</p>
    </div>

    <!-- 默认占位符 -->
    <div v-else class="stream-placeholder">
      <div class="placeholder-icon">🎥</div>
      <p>视频流显示区域</p>
      <p class="placeholder-hint">请设置有效的视频流 URL</p>
    </div>
  </div>
</template>

<style scoped>
/* 视频流容器 */
.video-stream-container {
  position: relative;
  background-color: #000;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 视频流元素 */
.video-stream {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 加载状态 */
.stream-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: #fff;
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 错误状态 */
.stream-error {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: #ff4444;
  z-index: 10;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

/* 占位符 */
.stream-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: #1a1a1a;
  color: #666;
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.placeholder-hint {
  font-size: 0.875rem;
  color: #999;
  margin-top: 0.5rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .video-stream-container {
    border-radius: 2px;
  }

  .stream-loading p,
  .stream-error p,
  .stream-placeholder p {
    font-size: 0.875rem;
  }
}
</style>