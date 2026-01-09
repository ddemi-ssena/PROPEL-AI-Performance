import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { requiresGuest: true },
    },
    // Admin Routes
    {
      path: '/admin',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Genel Müdür Paneli' },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/AdminDashboard.vue'),
        },
        // Gelecekte eklenecek admin rotaları
      ]
    },
    // Manager Routes
    {
      path: '/manager',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Yazılım Geliştirme Yönetici Paneli' },
      children: [
        {
          path: '',
          name: 'manager-dashboard',
          component: () => import('@/views/manager/ManagerDashboard.vue'),
        }
      ]
    },
    // Employee Routes
    {
      path: '/employee',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Personel Paneli' },
      children: [
        {
          path: '',
          name: 'employee-dashboard',
          component: () => import('@/views/employee/EmployeeDashboard.vue'),
        }
      ]
    },
    // Legacy/Default Fallback
    {
      path: '/dashboard',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          // Rol bazlı yönlendirme yapılana kadar geçici olarak admin'e
          component: () => import('@/views/admin/AdminDashboard.vue'),
        }
      ]
    },
    {
      path: '/',
      redirect: '/login',
    },
  ],
})

// Auth Guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router