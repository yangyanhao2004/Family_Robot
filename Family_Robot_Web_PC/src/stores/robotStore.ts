import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ConnectionStatus, Notification } from '@/types'

export const useRobotStore = defineStore('robot', () => {
  const connectionStatus = ref<ConnectionStatus>('disconnected')
  const connectionError = ref<string | null>(null)

  const battery = ref<number | null>(null)
  const isRunning = ref(false)
  const signalStrength = ref<number | null>(null)

  const autoConnect = ref(true)
  const notifications = ref<Notification[]>([])

  let _nextNotifId = 0

  const needsCharging = computed(() => (battery.value ?? 100) < 20)

  function updateConnectionStatus(connected: boolean, error: string | null = null) {
    connectionStatus.value = connected ? 'connected' : 'disconnected'
    connectionError.value = error
  }

  function setConnecting() {
    connectionStatus.value = 'connecting'
    connectionError.value = null
  }

  function setDisconnected() {
    connectionStatus.value = 'disconnected'
    battery.value = null
    isRunning.value = false
    signalStrength.value = null
  }

  function updateRobotStatus(payload: { battery?: number; isRunning?: boolean; signalStrength?: number }) {
    if (payload.battery !== undefined) battery.value = payload.battery
    if (payload.isRunning !== undefined) isRunning.value = payload.isRunning
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
    connectionError,
    battery,
    isRunning,
    signalStrength,
    autoConnect,
    notifications,
    needsCharging,
    updateConnectionStatus,
    setConnecting,
    setDisconnected,
    updateRobotStatus,
    addNotification,
    removeNotification,
  }
})
