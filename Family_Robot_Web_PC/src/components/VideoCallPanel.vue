<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import webRTCService from '../services/webrtc';

const remoteAudio = ref<HTMLAudioElement | null>(null);
const isCallConnected = ref(false);
const callStatus = ref('Not connected');
const isConnecting = ref(false);

const toggleCall = async () => {
  if (isCallConnected.value || isConnecting.value) {
    webRTCService.close();
    isCallConnected.value = false;
    isConnecting.value = false;
    callStatus.value = 'Closed';
    return;
  }

  isConnecting.value = true;
  callStatus.value = 'Connecting...';
  try {
    await webRTCService.startCall();
  } catch (error) {
    console.error('Call start failed:', error);
    callStatus.value = 'Start failed';
    isConnecting.value = false;
  }
};

const bindRemoteAudio = () => {
  const stream = webRTCService.getRemoteStream();
  if (!remoteAudio.value || !stream) return;
  if (remoteAudio.value.srcObject !== stream) {
    remoteAudio.value.srcObject = stream;
    remoteAudio.value.play().catch(() => {
      // Browser autoplay policy may block until user interacts.
    });
  }
};

const updateCallStatus = () => {
  const state = webRTCService.getConnectionState();
  isCallConnected.value = state === 'connected';
  if (state === 'connected') {
    isConnecting.value = false;
    callStatus.value = 'Connected';
  } else if (state === 'connecting') {
    callStatus.value = 'Connecting...';
  } else if (state === 'failed') {
    isConnecting.value = false;
    callStatus.value = 'Failed';
  } else if (!isConnecting.value) {
    callStatus.value = 'Not connected';
  }
};

const statusUpdateInterval = setInterval(() => {
  updateCallStatus();
  bindRemoteAudio();
}, 400);

onMounted(() => {
  updateCallStatus();
});

onUnmounted(() => {
  clearInterval(statusUpdateInterval);
});
</script>

<template>
  <div class="video-call-panel">
    <div class="call-control-simple">
      <div
        class="status-indicator"
        :class="{
          connected: isCallConnected,
          connecting: isConnecting,
          disconnected: !isCallConnected && !isConnecting
        }"
      >
        <span class="status-dot"></span>
        <span class="status-text">{{ callStatus }}</span>
      </div>

      <div class="call-buttons">
        <button
          class="call-button"
          :class="{ connected: isCallConnected || isConnecting }"
          @click="toggleCall"
        >
          {{ isCallConnected || isConnecting ? 'End Call' : 'Start Call' }}
        </button>
      </div>
    </div>

    <audio ref="remoteAudio" autoplay playsinline></audio>
  </div>
</template>

<style scoped>
.video-call-panel {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
}

.call-control-simple {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ccc;
  transition: all 0.3s ease;
}

.status-indicator.connected .status-dot {
  background-color: #4caf50;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.6);
  animation: pulse 2s infinite;
}

.status-indicator.connecting .status-dot {
  background-color: #ff9800;
  animation: pulse 1s infinite;
}

.status-indicator.disconnected .status-dot {
  background-color: #f44336;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.call-buttons {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.call-button {
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #2196f3;
  color: white;
  text-align: center;
}

.call-button:hover:not(:disabled) {
  background-color: #1976d2;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.call-button.connected {
  background-color: #f44336;
}

.call-button.connected:hover:not(:disabled) {
  background-color: #d32f2f;
}

@media (max-width: 768px) {
  .video-call-panel {
    padding: 1rem;
  }
}
</style>
