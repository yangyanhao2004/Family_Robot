import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const role = ref<string | null>(localStorage.getItem('auth_role'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'Admin')

  async function login(email: string, password: string) {
    isLoading.value = true
    error.value = null
    try {
      const res = await api.login(email, password)
      token.value = res.token
      role.value = res.role
      localStorage.setItem('auth_token', res.token)
      localStorage.setItem('auth_role', res.role)
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function setAuth(newToken: string, newRole: string) {
    token.value = newToken
    role.value = newRole
    localStorage.setItem('auth_token', newToken)
    localStorage.setItem('auth_role', newRole)
  }

  function logout() {
    token.value = null
    role.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_role')
  }

  return { token, role, isLoading, error, isAuthenticated, isAdmin, login, setAuth, logout }
})
