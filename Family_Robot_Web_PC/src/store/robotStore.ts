// store/robotStore.ts - 机器人状态管理

import { defineStore } from 'pinia';

export const useRobotStore = defineStore('robot', {
  state: () => ({
    // 连接状态
    connection: {
      isConnected: false,
      lastConnected: null as Date | null,
      error: null as string | null,
    },
    
    // 机器人状态
    status: {
      battery: 100,
      isRunning: false,
      temperature: 30,
      signalStrength: 5,
    },
    
    // 系统设置
    settings: {
      autoConnect: true,
      notifications: true,
      sound: true,
      language: 'zh-CN',
    },
  }),
  
  getters: {
    // 计算属性：电池状态
    batteryStatus(): string {
      const { battery } = this.status;
      if (battery > 80) return '充足';
      if (battery > 50) return '良好';
      if (battery > 20) return '一般';
      return '低电量';
    },
    
    // 计算属性：是否需要充电
    needsCharging(): boolean {
      return this.status.battery < 20;
    },
  },
  
  actions: {
    // 更新连接状态
    updateConnectionStatus(isConnected: boolean, error: string | null = null): void {
      this.connection.isConnected = isConnected;
      this.connection.error = error;
      if (isConnected) {
        this.connection.lastConnected = new Date();
      }
    },
    
    // 更新机器人状态
    updateRobotStatus(status: Partial<typeof this.status>): void {
      this.status = { ...this.status, ...status };
    },
    
    // 启动机器人
    startRobot(): void {
      this.status.isRunning = true;
    },
    
    // 停止机器人
    stopRobot(): void {
      this.status.isRunning = false;
    },
    
    // 更新系统设置
    updateSettings(settings: Partial<typeof this.settings>): void {
      this.settings = { ...this.settings, ...settings };
    },
    
    // 重置状态
    resetState(): void {
      this.connection = {
        isConnected: false,
        lastConnected: null,
        error: null,
      };
      this.status = {
        battery: 100,
        isRunning: false,
        temperature: 30,
        signalStrength: 5,
      };
    },
  },
});