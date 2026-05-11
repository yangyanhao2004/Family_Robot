import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    isLoading.value = true
    error.value = null
    try {
      const res = await api.login(email, password)
      token.value = res.token
      localStorage.setItem('auth_token', res.token)
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    token.value = null
    localStorage.removeItem('auth_token')
  }

  return { token, isLoading, error, isAuthenticated, login, logout }
})
