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
          path: 'album',
          name: 'album',
          component: () => import('@/views/AlbumView.vue'),
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

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('auth_token')
  const role = localStorage.getItem('auth_role')

  if (to.meta.requiresAuth && !token) {
    next({ name: 'login' })
  } else if (to.meta.requiresAdmin && role !== 'Admin') {
    next({ name: 'dashboard' })
  } else if (to.name === 'login' && token) {
    if (role === 'Admin') {
      next({ name: 'adminUsers' })
    } else {
      next({ name: 'dashboard' })
    }
  } else {
    next()
  }
})

export default router
