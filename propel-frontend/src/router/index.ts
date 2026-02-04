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
        {
          path: 'employees',
          name: 'admin-employees',
          component: () => import('@/views/admin/EmployeeManagement.vue'),
          meta: { title: 'Personel Yönetimi' }
        },
        {
          path: 'employees/:id',
          name: 'admin-employee-details',
          component: () => import('@/views/admin/EmployeeDetails.vue'),
          meta: { title: 'Personel Detayı' }
        },
        {
          path: 'data-management',
          name: 'admin-data-management',
          component: () => import('@/views/admin/DataManagement.vue'),
          meta: { title: 'Veri Yönetimi' }
        },
        {
          path: 'ai-insights',
          name: 'admin-ai-insights',
          component: () => import('@/views/admin/AIInsights.vue'),
          meta: { title: 'Yapay Zeka İçgörüleri' }
        }
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
        },
        {
          path: 'team',
          name: 'manager-team',
          component: () => import('@/views/manager/TeamManagement.vue'),
          meta: { title: 'Ekibim' }
        }
      ]
    },
    // Settings Route (Shared)
    {
      path: '/settings',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Ayarlar' },
      children: [
        {
          path: '',
          name: 'settings',
          component: () => import('@/views/Settings.vue'),
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