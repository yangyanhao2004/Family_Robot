<script setup lang="ts">
// App.vue - 家庭陪伴型机器人 Web 控制端主布局

import RobotControlPanel from './views/RobotControlPanel.vue';
</script>

<template>
  <div class="app-container">
    <!-- 直接显示机器人远程控制面板 -->
    <RobotControlPanel />
  </div>
</template>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f5f5f5;
}

/* 应用容器 */
.app-container {
  width: 100%;
  min-height: 100vh;
}
</style>
