const JAVA_API_URL = import.meta.env.VITE_JAVA_API_URL || 'http://localhost:8090'

function apiBase() {
  return JAVA_API_URL.replace(/\/$/, '')
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token')
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  return {}
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    // 401 on protected endpoints → token expired, force re-login
    if (res.status === 401 && !path.startsWith('/api/auth/')) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_role')
      window.location.hash = '#/login'
      throw new Error('登录已过期，请重新登录')
    }
    let message = `${options?.method || 'GET'} ${path} failed (${res.status})`
    try {
      const body = await res.json()
      if (body.message) {
        message = body.message
      }
    } catch {
      const text = await res.text()
      if (text) message = text
    }
    throw new Error(message)
  }
  return res.json()
}

export const api = {
  // ---- Auth ----
  login: (email: string, password: string) =>
    request<{ token: string; role: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string, serialNumber: string) =>
    request<{ message: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, serialNumber }),
    }),

  verify: (email: string, code: string) =>
    request<{ message: string }>('/api/auth/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),

  logout: () =>
    request<void>('/api/auth/logout', { method: 'POST' }),

  sendLoginCode: (email: string) =>
    request<{ message: string }>('/api/auth/login-code/send', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  verifyLoginCode: (email: string, code: string) =>
    request<{ token: string; role: string }>('/api/auth/login-code/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),

  sendResetPasswordCode: (email: string) =>
    request<{ message: string }>('/api/auth/reset-password/send', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  resetPassword: (email: string, code: string, newPassword: string) =>
    request<{ message: string }>('/api/auth/reset-password/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code, newPassword }),
    }),

  // ---- Album ----
  getPhotos: () =>
    request<{ id: string; url: string; date: string }[]>('/api/albums'),

  deletePhoto: (id: string) =>
    request<void>(`/api/albums/${id}`, { method: 'DELETE' }),

  addPhoto: (url: string, filename: string) =>
    request<{ message: string }>('/api/albums', {
      method: 'POST',
      body: JSON.stringify({ url, filename }),
    }),

  // ---- Settings ----
  getSettings: () =>
    request<{ autoSave: boolean; firmwareVersion: string; serialNumber: string }>('/api/settings'),

  updateSettings: (settings: Record<string, unknown>) =>
    request<void>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),

  // ---- User Profile ----
  getProfile: () =>
    request<{ name: string; email: string; role: string; lastLogin: string }>('/api/users/profile'),

  // ---- Admin ----
  getAdminUsers: () =>
    request<{ userId: number; email: string; name: string; role: string; password: string; robotSerialNumbers: string[] }[]>('/api/admin/users'),

  registerRobot: (serialNumber: string) =>
    request<{ message: string }>('/api/admin/robots', {
      method: 'POST',
      body: JSON.stringify({ serialNumber }),
    }),
}
