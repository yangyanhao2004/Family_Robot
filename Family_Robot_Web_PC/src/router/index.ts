import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
    },
    {
      path: '/reset-password',
      name: 'resetPassword',
      component: () => import('@/views/ResetPasswordView.vue'),
    },
    {
      path: '/home',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'ai-chat',
          name: 'aiChat',
          component: () => import('@/views/AIChatView.vue'),
        },
        {
          path: 'album',
          name: 'album',
          component: () => import('@/views/AlbumView.vue'),
        },
        {
          path: 'reminders',
          name: 'reminders',
          component: () => import('@/views/ReminderView.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
        },
        {
          path: 'user',
          name: 'user',
          component: () => import('@/views/UserProfileView.vue'),
        },
      ],
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'adminUsers',
          component: () => import('@/views/admin/AdminUserList.vue'),
        },
        {
          path: 'robots',
          name: 'adminRobots',
          component: () => import('@/views/admin/AdminRobotRegister.vue'),
        },
      ],
    },
  ],
})

let tokenVerified = false

router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('auth_token')
  const role = localStorage.getItem('auth_role')

  if (to.meta.requiresAuth && !token) {
    next({ name: 'login' })
  } else if (to.meta.requiresAdmin && role !== 'Admin') {
    next({ name: 'dashboard' })
  } else if (to.meta.requiresAuth && token && !tokenVerified) {
    // Verify token on first protected navigation
    try {
      const BASE = (import.meta as any).env.VITE_JAVA_API_URL || 'http://localhost:8090'
      const res = await fetch(`${BASE.replace(/\/$/, '')}/api/users/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('token invalid')
      tokenVerified = true
      next()
    } catch {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_role')
      next({ name: 'login' })
    }
  } else {
    next()
  }
})

export default router
