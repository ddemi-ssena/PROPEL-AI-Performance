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
        {
          path: 'employees',
          name: 'admin-employees',
          component: () => import('@/views/admin/EmployeeManagement.vue'),
          meta: { title: 'Personel Yonetimi' },
        },
        {
          path: 'employees/:id',
          name: 'admin-employee-details',
          component: () => import('@/views/admin/EmployeeDetails.vue'),
          meta: { title: 'Personel Detayi' },
        },
        {
          path: 'data-management',
          name: 'admin-data-management',
          component: () => import('@/views/admin/DataManagement.vue'),
          meta: { title: 'Veri Yonetimi' },
        },
        {
          path: 'ai-insights',
          name: 'admin-ai-insights',
          component: () => import('@/views/admin/AIInsights.vue'),
          meta: { title: 'Yapay Zeka Icgoruleri' },
        },
        {
          path: 'survey-results',
          name: 'admin-survey-results',
          component: () => import('@/views/shared/SurveyResults.vue'),
          meta: { title: 'Anket Sonuclari' },
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
        {
          path: 'kpi-ml-analysis',
          name: 'manager-kpi-ml-analysis',
          component: () => import('@/views/manager/ManagerAnalyticsView.vue'),
          meta: { title: 'KPI & ML Analizi' },
        },
        {
          path: 'team',
          name: 'manager-team',
          component: () => import('@/views/manager/TeamManagement.vue'),
          meta: { title: 'Ekibim' },
        },
        {
          path: 'survey-results',
          name: 'manager-survey-results',
          component: () => import('@/views/shared/SurveyResults.vue'),
          meta: { title: 'Anket Sonuclari' },
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
      path: '/settings',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'Ayarlar' },
      children: [
        {
          path: '',
          name: 'settings',
          component: () => import('@/views/Settings.vue'),
        },
      ],
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
        {
          path: 'pulse',
          name: 'employee-pulse',
          component: () => import('@/views/employee/EmployeePulseView.vue'),
          meta: { title: 'Nabiz Anketi' },
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
    const role = authStore.userRole
    if (role === 'admin') next('/admin')
    else if (role === 'department_manager') next('/manager')
    else if (role === 'employee') next('/employee')
    else next('/dashboard')
  } else {
    next()
  }
})

export default router
