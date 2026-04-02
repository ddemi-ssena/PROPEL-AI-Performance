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
    {
      path: '/admin',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Genel Mudur Paneli' },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/AdminDashboard.vue'),
        },
      ],
    },
    {
      path: '/manager',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Departman Yonetici Paneli' },
      children: [
        {
          path: '',
          name: 'manager-dashboard',
          component: () => import('@/views/manager/ManagerDashboard.vue'),
          meta: { title: 'Departman Performansi' },
        },
        {
          path: 'feedback-reports/employees',
          name: 'manager-employee-analysis',
          component: () => import('@/views/manager/EmployeeAnalysisView.vue'),
          meta: { title: 'Calisan Analizi' },
        },
        {
          path: 'feedback-reports/department',
          name: 'manager-department-analysis',
          component: () => import('@/views/manager/DepartmentAnalysisView.vue'),
          meta: { title: 'Departman Analizi' },
        },
      ],
    },
    {
      path: '/feedback',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: '360 Derece Geri Bildirim Paneli' },
      children: [
        {
          path: '',
          name: 'feedback',
          component: () => import('@/views/feedback/FeedbackView.vue'),
        },
      ],
    },
    {
      path: '/feedback-dashboard',
      redirect: '/feedback',
    },
    {
      path: '/employee',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Personel Paneli' },
      children: [
        {
          path: '',
          name: 'employee-dashboard',
          component: () => import('@/views/employee/EmployeeDashboard.vue'),
        },
      ],
    },
    {
      path: '/dashboard',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/admin/AdminDashboard.vue'),
        },
      ],
    },
    {
      path: '/',
      redirect: '/login',
    },
  ],
})

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
