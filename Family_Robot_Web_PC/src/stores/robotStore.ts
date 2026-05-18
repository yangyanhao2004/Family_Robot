import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ConnectionStatus, Notification } from '@/types'

export const useRobotStore = defineStore('robot', () => {
  const connectionStatus = ref<ConnectionStatus>('disconnected')

  const battery = ref<number | null>(null)
  const signalStrength = ref<number | null>(null)
  const speedLevel = ref<'low' | 'medium' | 'high'>('medium')

  const autoConnect = ref(true)
  const notifications = ref<Notification[]>([])

  let _nextNotifId = 0

  function updateConnectionStatus(connected: boolean, _error: string | null = null) {
    connectionStatus.value = connected ? 'connected' : 'disconnected'
  }

  function setConnecting() {
    connectionStatus.value = 'connecting'
  }

  function setDisconnected() {
    connectionStatus.value = 'disconnected'
    battery.value = null
    signalStrength.value = null
  }

  function updateRobotStatus(payload: { battery?: number; isRunning?: boolean; signalStrength?: number }) {
    if (payload.battery !== undefined) battery.value = payload.battery
    if (payload.signalStrength !== undefined) signalStrength.value = payload.signalStrength
  }

  function addNotification(message: string, type: Notification['type'] = 'info') {
    const id = `notif-${++_nextNotifId}`
    notifications.value = [...notifications.value, { id, message, type }]
    setTimeout(() => removeNotification(id), 3000)
  }

  function removeNotification(id: string) {
    notifications.value = notifications.value.filter((n) => n.id !== id)
  }

  return {
    connectionStatus,
    battery,
    signalStrength,
    speedLevel,
    autoConnect,
    notifications,
    updateConnectionStatus,
    setConnecting,
    setDisconnected,
    updateRobotStatus,
    addNotification,
    removeNotification,
  }
})
