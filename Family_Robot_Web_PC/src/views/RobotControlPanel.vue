<script setup lang="ts">
// RobotControlPanel.vue

import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRobotStore } from '../store/robotStore';
import webSocketService, { RobotCommand } from '../services/websocket';
import VideoStream from '../components/VideoStream.vue';
import VideoCallPanel from '../components/VideoCallPanel.vue';

// Pinia Store
const robotStore = useRobotStore();

// 长按控制变量
const pressTimers = {
  forward: null as number | null,
  backward: null as number | null,
  left: null as number | null,
  right: null as number | null
};

// 长按时间间隔（毫秒）
const PRESS_INTERVAL = 100;



/* ===========================
   计算属性（响应式）
=========================== */

// 是否已连接
const isConnected = computed(() => robotStore.connection.isConnected);

// 连接状态文本
const connectionMessage = computed(() => {
  if (robotStore.connection.isConnected) return '已连接';
  return robotStore.connection.error || '未连接';
});

// 状态样式
const connectionStatusClass = computed(() =>
  robotStore.connection.isConnected ? 'connected' : 'disconnected'
);

// 是否需要充电
const needsCharging = computed(() => robotStore.needsCharging);

// 灯光状态
const isLightOn = ref(false);

/* ===========================
   行为函数
=========================== */

// 发送控制指令
const sendCommand = (command: RobotCommand) => {
  if (isConnected.value) {
    webSocketService.sendCommand(command);
  }
};

// 处理长按开始
const handleButtonDown = (command: RobotCommand) => {
  // 清除可能存在的定时器
  if (pressTimers[command as keyof typeof pressTimers]) {
    clearInterval(pressTimers[command as keyof typeof pressTimers]!);
  }
  
  // 立即发送一次指令
  sendCommand(command);
  
  // 设置定时器，持续发送指令
  pressTimers[command as keyof typeof pressTimers] = window.setInterval(() => {
    sendCommand(command);
  }, PRESS_INTERVAL);
};

// 添加防抖变量
let stopCommandTimeout: number | null = null;

// 处理长按结束
const handleButtonUp = (command: RobotCommand) => {
  // 清除定时器
  const timerId = pressTimers[command as keyof typeof pressTimers];
  if (timerId !== null) {
    clearInterval(timerId);
    pressTimers[command as keyof typeof pressTimers] = null;
  }
  
  // 防抖处理，避免频繁发送 stop 指令
  if (stopCommandTimeout) {
    clearTimeout(stopCommandTimeout);
  }
  
  stopCommandTimeout = window.setTimeout(() => {
    sendCommand('stop');
  }, 50); // 50ms 防抖
};

// 连接 / 断开
const toggleConnection = () => {
  if (isConnected.value) {
    webSocketService.disconnect();
  } else {
    webSocketService.connect();
  }
};

// 切换灯光状态
const toggleLight = () => {
  isLightOn.value = !isLightOn.value;
  // 发送灯光控制指令
  webSocketService.sendCommand(isLightOn.value ? 'light_on' : 'light_off');
};

/* ===========================
   生命周期
=========================== */

onMounted(() => {
  // 可选：支持自动连接
  if (robotStore.settings.autoConnect) {
    webSocketService.connect();
  }
});

onUnmounted(() => {
  // 页面销毁时不强制断开（便于多页面复用）
});
</script>

<template>
  <div class="robot-control-panel">
    <h1 class="panel-title">机器人远程控制面板</h1>

    <!-- 连接状态 -->
    <div class="connection-status">
      <div class="status-indicator" :class="connectionStatusClass">
        <span class="status-dot"></span>
        <span class="status-text">{{ connectionMessage }}</span>
      </div>

      <button
        class="connection-button"
        :class="{ connected: isConnected }"
        @click="toggleConnection"
      >
        {{ isConnected ? '断开连接' : '连接服务器' }}
      </button>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 视频和状态区域 -->
      <div class="video-status-container">
        <!-- 视频区域（中间） -->
        <div class="video-section">
          <!-- 视频框上方的机器人状态 -->
          <div class="video-top-status">
            <div class="status-item">
              <span class="status-label">电池:</span>
              <span class="status-value" :class="{ 'low': needsCharging }">{{ robotStore.status.battery }}%</span>
            </div>
            <div class="status-item">
              <span class="status-label">状态:</span>
              <span class="status-value" :class="{ 'running': robotStore.status.isRunning }">{{ robotStore.status.isRunning ? '运行中' : '待机' }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">温度:</span>
              <span class="status-value" :class="{ 'high': robotStore.status.temperature > 40 }">{{ robotStore.status.temperature }}°C</span>
            </div>
            <div class="status-item">
              <span class="status-label">信号:</span>
              <div class="signal-bars-small">
                <span v-for="i in 5" :key="i" class="signal-bar" :class="{ 'active': i <= robotStore.status.signalStrength }"></span>
              </div>
            </div>
          </div>

          <!-- 视频容器 -->
          <div class="video-container">
            <!-- 视频流组件 -->
            <VideoStream 
              streamUrl="https://samplelib.com/lib/preview/mp4/sample-5s.mp4" 
              streamType="http"
              autoplay
              muted
            />
          </div>

          <!-- 视频框下方的控制 -->
          <div class="video-bottom-controls">
            <div class="controls-container">
              <!-- 方向控制 -->
              <div class="control-section">
                <h3 class="control-section-title">方向控制</h3>
                <div class="control-pad">
                  <div class="control-row">
                    <button
                      class="control-button forward"
                      :disabled="!isConnected"
                      @mousedown="handleButtonDown('forward')"
                      @mouseup="handleButtonUp('forward')"
                      @mouseleave="handleButtonUp('forward')"
                      @touchstart="handleButtonDown('forward')"
                      @touchend="handleButtonUp('forward')"
                      @touchcancel="handleButtonUp('forward')"
                    >
                      ↑ 前进
                    </button>
                  </div>

                  <div class="control-row">
                    <button
                      class="control-button left"
                      :disabled="!isConnected"
                      @mousedown="handleButtonDown('left')"
                      @mouseup="handleButtonUp('left')"
                      @mouseleave="handleButtonUp('left')"
                      @touchstart="handleButtonDown('left')"
                      @touchend="handleButtonUp('left')"
                      @touchcancel="handleButtonUp('left')"
                    >
                      ← 左转
                    </button>

                    <button
                      class="control-button light"
                      :class="{ 'active': isLightOn }"
                      :disabled="!isConnected"
                      @click="toggleLight"
                    >
                      💡 {{ isLightOn ? '关灯' : '开灯' }}
                    </button>

                    <button
                      class="control-button right"
                      :disabled="!isConnected"
                      @mousedown="handleButtonDown('right')"
                      @mouseup="handleButtonUp('right')"
                      @mouseleave="handleButtonUp('right')"
                      @touchstart="handleButtonDown('right')"
                      @touchend="handleButtonUp('right')"
                      @touchcancel="handleButtonUp('right')"
                    >
                      → 右转
                    </button>
                  </div>

                  <div class="control-row">
                    <button
                      class="control-button backward"
                      :disabled="!isConnected"
                      @mousedown="handleButtonDown('backward')"
                      @mouseup="handleButtonUp('backward')"
                      @mouseleave="handleButtonUp('backward')"
                      @touchstart="handleButtonDown('backward')"
                      @touchend="handleButtonUp('backward')"
                      @touchcancel="handleButtonUp('backward')"
                    >
                      ↓ 后退
                    </button>
                  </div>
                </div>
              </div>

              <!-- 语音通话控制 -->
              <div class="call-control-section">
                <h3 class="control-section-title">语音通话</h3>
                <div class="call-control-content">
                  <VideoCallPanel />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 主面板样式 */
.robot-control-panel {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 2rem;
  background-color: #f5f5f5;
}

/* 面板标题 */
.panel-title {
  color: #333;
  font-size: 2rem;
  margin-bottom: 1.5rem;
  text-align: center;
  border-bottom: 3px solid #4CAF50;
  padding-bottom: 1rem;
}

/* 连接状态 */
.connection-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ffffff;
  padding: 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.1rem;
  font-weight: 500;
}

.status-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background-color: #ccc;
  transition: all 0.3s ease;
}

.status-indicator.connected .status-dot {
  background-color: #4CAF50;
  box-shadow: 0 0 12px rgba(76, 175, 80, 0.6);
  animation: pulse 2s infinite;
}

.status-indicator.disconnected .status-dot {
  background-color: #f44336;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.connection-button {
  padding: 0.875rem 2rem;
  border: none;
  border-radius: 6px;
  font-size: 1.1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #2196F3;
  color: white;
}

.connection-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.connection-button.connected {
  background-color: #f44336;
}

.connection-button.connected:hover:not(:disabled) {
  background-color: #d32f2f;
}

.connection-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  transform: none;
}

/* 主要内容区域 */
.main-content {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 视频和状态容器 */
.video-status-container {
  width: 100%;
  max-width: 1000px;
}

/* 视频区域 */
.video-section {
  background-color: #ffffff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 视频上方的状态栏 */
.video-top-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f9f9f9;
  padding: 0.75rem 1rem;
  border-radius: 6px 6px 0 0;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 0;
}

.video-top-status .status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.video-top-status .status-label {
  font-size: 0.875rem;
  color: #666;
  font-weight: 500;
}

.video-top-status .status-value {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.video-top-status .status-value.low {
  color: #f44336;
}

.video-top-status .status-value.running {
  color: #4CAF50;
}

.video-top-status .status-value.high {
  color: #ff9800;
}

/* 小尺寸信号强度 */
.signal-bars-small {
  display: flex;
  gap: 3px;
  align-items: flex-end;
  height: 16px;
}

.signal-bars-small .signal-bar {
  width: 5px;
  background-color: #e0e0e0;
  border-radius: 1px;
  transition: all 0.3s ease;
}

.signal-bars-small .signal-bar:nth-child(1) { height: 6px; }
.signal-bars-small .signal-bar:nth-child(2) { height: 8px; }
.signal-bars-small .signal-bar:nth-child(3) { height: 10px; }
.signal-bars-small .signal-bar:nth-child(4) { height: 12px; }
.signal-bars-small .signal-bar:nth-child(5) { height: 14px; }

.signal-bars-small .signal-bar.active {
  background-color: #4CAF50;
}

/* 视频容器 */
.video-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background-color: #000;
  border-radius: 0 0 6px 6px;
  overflow: hidden;
}

/* 视频流 */
.video-container :deep(.video-stream) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 视频下方的控制 */
.video-bottom-controls {
  margin-top: 2rem;
  width: 100%;
}

/* 控制容器 */
.controls-container {
  display: flex;
  gap: 2rem;
  justify-content: center;
  align-items: flex-start;
}

/* 控制区域 */
.control-section {
  background-color: #ffffff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex: 1;
  max-width: 400px;
}

.call-control-section {
  flex: 1;
  max-width: 500px;
  display: flex;
  flex-direction: column;
}

.call-control-content {
  flex: 1;
}

.control-section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e0e0e0;
}

/* 方向控制区域 */
.control-pad {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.control-row {
  display: flex;
  gap: 0.75rem;
}

.control-button {
  width: 100px;
  height: 100px;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #2196F3;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.control-button:disabled {
  background-color: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  transform: none;
}

.control-button.stop {
  background-color: #f44336;
}

.control-button.light {
  background-color: #ff9800;
}

.control-button.light.active {
  background-color: #ff5722;
}

.control-button.light:hover:not(:disabled) {
  background-color: #f57c00;
}

.control-button.light.active:hover:not(:disabled) {
  background-color: #e64a19;
}

.control-button.stop:hover:not(:disabled) {
  background-color: #d32f2f;
}

/* 语音通话控制内容 */
.call-control-content {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .controls-container {
    flex-direction: column;
    align-items: center;
  }

  .control-section,
  .call-control-section {
    max-width: 100%;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .robot-control-panel {
    padding: 1rem;
  }

  .panel-title {
    font-size: 1.5rem;
  }

  .connection-status {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .connection-button {
    width: 100%;
  }

  .video-top-status {
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.5rem;
  }

  .video-top-status .status-item {
    flex: 1 1 calc(50% - 0.5rem);
  }

  .video-section {
    padding: 1rem;
  }

  .control-button {
    width: 70px;
    height: 70px;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .video-top-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .video-top-status .status-item {
    flex: 1 1 100%;
  }

  .control-button {
    width: 60px;
    height: 60px;
    font-size: 0.8rem;
  }
}
</style>