<script setup lang="ts">
// components/VideoCallPanel.vue - 视频通话面板组件
// 设计意图：提供机器人视频通话界面，支持单向视频和双向音频

import { ref, onMounted, onUnmounted } from 'vue';
import webRTCService from '../services/webrtc';

// 响应式数据
const remoteVideo = ref<HTMLVideoElement | null>(null);
const isCallConnected = ref(false);
const callStatus = ref('未连接');
const isConnecting = ref(false);

// 连接/断开通话
const toggleCall = async () => {
  if (isCallConnected.value) {
    // 断开通话
    webRTCService.close();
    // 立即更新状态
    isCallConnected.value = false;
    callStatus.value = '已关闭';
  } else {
    // 连接通话
    isConnecting.value = true;
    try {
      await webRTCService.createOffer();
      // 立即更新状态，不等待 WebSocket 响应
      isCallConnected.value = true;
      callStatus.value = '通话已连接';
    } catch (error) {
      console.error('连接通话失败:', error);
      callStatus.value = '连接失败';
    } finally {
      isConnecting.value = false;
    }
  }
};



// 更新通话状态
const updateCallStatus = () => {
  const state = webRTCService.getConnectionState();
  isCallConnected.value = state === 'connected';
  
  switch (state) {
    case 'connected':
      callStatus.value = '通话已连接';
      break;
    case 'connecting':
      callStatus.value = '正在连接...';
      break;
    case 'disconnected':
      callStatus.value = '未连接';
      break;
    case 'failed':
      callStatus.value = '连接失败';
      break;
    case 'closed':
      callStatus.value = '已关闭';
      break;
    default:
      callStatus.value = `状态: ${state}`;
  }
};

// 绑定远端视频流
const bindRemoteStream = () => {
  const stream = webRTCService.getRemoteStream();
  if (remoteVideo.value && stream) {
    remoteVideo.value.srcObject = stream;
    console.log('[VideoCallPanel] 绑定远端视频流成功');
  }
};

// 监听通话状态变化
const statusUpdateInterval = setInterval(() => {
  updateCallStatus();
  bindRemoteStream();
}, 1000);

// 生命周期钩子
onMounted(() => {
  updateCallStatus();
});

onUnmounted(() => {
  // 清理定时器
  clearInterval(statusUpdateInterval);
  
  // 组件卸载时不自动关闭通话，以便在其他页面继续使用
});
</script>

<template>
  <div class="video-call-panel">
    <!-- 通话控制 -->
    <div class="call-control-simple">
      <div class="status-indicator" :class="{
        'connected': isCallConnected,
        'connecting': isConnecting,
        'disconnected': !isCallConnected && !isConnecting
      }">
        <span class="status-dot"></span>
        <span class="status-text">{{ callStatus }}</span>
      </div>
      
      <div class="call-buttons">
        <button 
          class="call-button" 
          :class="{ 'connected': isCallConnected }"
          @click="toggleCall"
          :disabled="isConnecting"
        >
          {{ isCallConnected ? '结束通话' : '开始通话' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 视频通话面板容器 */
.video-call-panel {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 100%;
}

/* 简单通话控制布局 */
.call-control-simple {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 状态指示器 */
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
  background-color: #4CAF50;
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

/* 通话按钮容器 */
.call-buttons {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* 通话按钮 */
.call-button {
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #2196F3;
  color: white;
  text-align: center;
}

.call-button:hover:not(:disabled) {
  background-color: #1976D2;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.call-button.connected {
  background-color: #f44336;
}

.call-button.connected:hover:not(:disabled) {
  background-color: #d32f2f;
}

.call-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  transform: none;
}

/* 控制按钮 */
.control-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #e0e0e0;
  color: #333;
}

.control-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.control-button:disabled {
  background-color: #f0f0f0;
  color: #999;
  cursor: not-allowed;
  transform: none;
}

/* 麦克风按钮 */
.mic-button {
  background-color: #4CAF50;
  color: white;
}

.mic-button.muted {
  background-color: #f44336;
}

.mic-button:hover:not(:disabled) {
  transform: translateY(-2px);
}

.button-icon {
  font-size: 1.25rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .video-call-panel {
    padding: 1rem;
  }

  .call-buttons {
    gap: 0.75rem;
  }

  .call-button {
    padding: 0.875rem 1.5rem;
  }

  .control-button {
    padding: 0.625rem 1.25rem;
  }
}
</style>