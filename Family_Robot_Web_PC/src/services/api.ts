const BASE_URL = import.meta.env.VITE_BACKEND_HTTP_URL || 'http://localhost:8080'

function httpBase() {
  return BASE_URL.replace(/\/$/, '')
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${httpBase()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${options?.method || 'GET'} ${path} failed: ${res.status}`)
  return res.json()
}

export const api = {
  // Auth — mock for now, real when Java backend is ready
  login: (email: string, password: string) =>
    new Promise<{ token: string }>((resolve) =>
      setTimeout(() => resolve({ token: 'mock-jwt-token' }), 600)
    ),

  logout: () =>
    new Promise<void>((resolve) => setTimeout(resolve, 200)),

  // Album — mock
  getPhotos: () =>
    new Promise<{ id: string; url: string; date: string }[]>((resolve) =>
      setTimeout(
        () =>
          resolve([
            { id: '1', url: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400', date: '2026-05-10' },
            { id: '2', url: 'https://images.unsplash.com/photo-1527430253228-e93688616381?w=400', date: '2026-05-09' },
            { id: '3', url: 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400', date: '2026-05-08' },
            { id: '4', url: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400', date: '2026-05-07' },
          ]),
        300
      )
    ),

  deletePhoto: (id: string) =>
    new Promise<void>((resolve) => setTimeout(resolve, 200)),

  // Settings — mock
  getSettings: () =>
    new Promise<{ autoSave: boolean; firmwareVersion: string; serialNumber: string }>((resolve) =>
      setTimeout(
        () =>
          resolve({ autoSave: true, firmwareVersion: 'v2.4.1 (latest)', serialNumber: 'RBT-98234-XYZ' }),
        200
      )
    ),

  updateSettings: (settings: Record<string, unknown>) =>
    new Promise<void>((resolve) => setTimeout(resolve, 200)),

  // User — mock
  getProfile: () =>
    new Promise<{ name: string; email: string; role: string; lastLogin: string }>((resolve) =>
      setTimeout(
        () =>
          resolve({
            name: 'Admin',
            email: 'admin@family-robot.local',
            role: 'Admin',
            lastLogin: new Date().toLocaleString(),
          }),
        200
      )
    ),
}
