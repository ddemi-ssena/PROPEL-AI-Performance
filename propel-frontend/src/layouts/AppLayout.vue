<template>
  <div class="min-h-screen bg-gray-50 flex font-sans text-slate-800">
    <aside class="w-72 bg-slate-900 border-r border-slate-800 hidden md:flex flex-col shadow-xl z-20">
      <div class="p-6 border-b border-slate-800 flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <span class="text-white font-bold text-lg">K</span>
        </div>
        <div>
          <h1 class="text-xl font-bold text-white tracking-tight">KUTUP</h1>
          <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Enterprise</p>
        </div>
      </div>

      <nav class="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
        <div class="mb-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Menu
        </div>

        <template v-for="item in navigation" :key="item.name">
          <button
            v-if="item.type === 'group'"
            type="button"
            class="w-full"
            @click="toggleGroup(item.name)"
          >
            <div
              class="flex items-center justify-between gap-3 px-3 py-3 text-sm font-medium rounded-lg transition-all duration-200 group"
              :class="isGroupActive(item) ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white'"
            >
              <div class="flex items-center gap-3">
                <component
                  :is="item.icon"
                  class="w-5 h-5 flex-shrink-0 transition-colors"
                  :class="isGroupActive(item) ? 'text-white' : 'text-slate-500 group-hover:text-white'"
                />
                {{ item.name }}
              </div>
              <component
                :is="isGroupOpen(item.name) ? ChevronDownIcon : ChevronRightIcon"
                class="w-4 h-4 flex-shrink-0"
              />
            </div>
          </button>

          <div
            v-else-if="item.type === 'section'"
            class="px-3 pt-4 pb-2 text-[11px] font-semibold text-slate-500 uppercase tracking-[0.18em]"
          >
            {{ item.name }}
          </div>

          <router-link
            v-else
            :to="item.to"
            class="flex items-center gap-3 px-3 py-3 text-sm font-medium rounded-lg transition-all duration-200 group"
            :class="[
              isActiveRoute(item.to)
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/20'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white',
              item.indent ? 'ml-4 pl-4 text-[13px]' : ''
            ]"
          >
            <component
              :is="item.icon"
              class="w-5 h-5 flex-shrink-0 transition-colors"
              :class="isActiveRoute(item.to) ? 'text-white' : 'text-slate-500 group-hover:text-white'"
            />
            {{ item.name }}
          </router-link>

          <transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="opacity-0 -translate-y-1 max-h-0"
            enter-to-class="opacity-100 translate-y-0 max-h-96"
            leave-active-class="transition-all duration-150 ease-in"
            leave-from-class="opacity-100 translate-y-0 max-h-96"
            leave-to-class="opacity-0 -translate-y-1 max-h-0"
          >
            <div
              v-if="item.type === 'group' && isGroupOpen(item.name)"
              class="relative mt-1 space-y-1 overflow-hidden"
            >
              <div class="absolute left-6 top-2 bottom-2 w-px bg-slate-800"></div>

              <template v-for="child in item.children" :key="`${item.name}-${child.name}`">
                <div
                  v-if="child.type === 'section'"
                  class="ml-7 px-3 pt-3 pb-1 text-[11px] font-semibold text-slate-500 uppercase tracking-[0.18em]"
                >
                  {{ child.name }}
                </div>
                <router-link
                  v-else
                  :to="child.to"
                  class="relative ml-7 flex items-center gap-3 px-3 py-3 text-[13px] font-medium rounded-lg transition-all duration-200 group"
                  :class="isActiveRoute(child.to)
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/20'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'"
                >
                  <span
                    class="absolute -left-[18px] top-1/2 h-8 w-[3px] -translate-y-1/2 rounded-full transition-all duration-200"
                    :class="isActiveRoute(child.to) ? 'bg-indigo-400' : 'bg-transparent group-hover:bg-slate-700'"
                  ></span>
                  <component
                    :is="child.icon"
                    class="w-4 h-4 flex-shrink-0 transition-colors"
                    :class="isActiveRoute(child.to) ? 'text-white' : 'text-slate-500 group-hover:text-white'"
                  />
                  {{ child.name }}
                </router-link>
              </template>
            </div>
          </transition>
        </template>
      </nav>

      <div class="p-4 border-t border-slate-800 bg-slate-900/50">
        <div class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer group">
          <div class="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center text-white font-bold text-sm ring-2 ring-slate-800 group-hover:ring-slate-600 transition-all">
            {{ userInitials }}
          </div>
          <div class="flex-1 overflow-hidden">
            <p class="text-sm font-medium text-white truncate">{{ userName }}</p>
            <p class="text-xs text-slate-400 truncate">{{ userRoleLabel }}</p>
          </div>
          <button @click="handleLogout" class="text-slate-500 hover:text-red-400 transition-colors p-1 rounded-md hover:bg-slate-700/50">
            <ArrowRightOnRectangleIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
    </aside>

    <div class="md:hidden flex flex-col min-h-screen w-full"></div>

    <main class="flex-1 overflow-auto bg-gray-50/50">
      <header class="bg-white/80 backdrop-blur-md border-b border-gray-200 px-8 py-5 flex items-center justify-between sticky top-0 z-10 transition-shadow hover:shadow-sm">
        <div class="flex items-center gap-4">
          <button @click="goBack" class="p-2 text-slate-400 hover:text-slate-700 hover:bg-gray-100/80 rounded-lg transition-colors" title="Geri Don">
            <ArrowLeftIcon class="w-5 h-5" />
          </button>
          <div>
            <h2 class="text-xl font-bold text-slate-900 tracking-tight">
              {{ pageTitle }}
            </h2>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <button
            v-if="userRole === 'employee'"
            @click="isWeeklyPulseModalOpen = true"
            class="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-xl text-sm font-bold border border-indigo-100 hover:bg-indigo-100 transition-all shadow-sm"
          >
            <HeartIcon class="w-4 h-4" />
            <span>Nabiz Anketi</span>
          </button>
          <div v-if="userRole === 'employee'" class="w-px h-6 bg-slate-200 mx-1"></div>
          <button class="p-2 text-slate-400 hover:text-indigo-600 rounded-full hover:bg-indigo-50 transition-all relative">
            <BellIcon class="w-6 h-6" />
            <span class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
          </button>
        </div>
      </header>

      <div class="p-6">
        <router-view />
      </div>

      <WeeklyPulseModal
        :is-open="isWeeklyPulseModalOpen"
        @close="isWeeklyPulseModalOpen = false"
        @submit="handlePulseSubmit"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FunctionalComponent, HTMLAttributes, VNodeProps } from 'vue'
import { useAuthStore } from '@/stores/auth'
import WeeklyPulseModal from '@/components/dashboard/WeeklyPulseModal.vue'
import { employeeApi } from '@/services/api/employee.api'
import { ChatBubbleLeftRightIcon } from '@heroicons/vue/24/solid'
import {
  ArrowLeftIcon,
  ArrowRightOnRectangleIcon,
  BellIcon,
  ChartBarIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  Cog6ToothIcon,
  DocumentTextIcon,
  HeartIcon,
  HomeIcon,
  UserIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isWeeklyPulseModalOpen = ref(false)

const userRole = computed(() => authStore.user?.role || localStorage.getItem('role') || 'employee')
// dept_id=2 gerçek DB, dept_id=18 mock fallback
const isSalesDept = computed(() => {
  const id = authStore.user?.department_id
  return id === 2 || id === 18
})
const userName = computed(() => authStore.user?.full_name || 'Kullanici')

const userInitials = computed(() =>
  userName.value.split(' ').map((n) => n[0]).join('').toUpperCase().substring(0, 2)
)

const userRoleLabel = computed(() => {
  const roles: Record<string, string> = {
    admin: 'Sistem Yoneticisi',
    department_manager: 'Departman Yoneticisi',
    employee: 'Personel',
  }
  return roles[userRole.value] || 'Kullanici'
})

const pageTitle = computed(() => route.meta.title || 'KUTUP')

type NavIcon = FunctionalComponent<HTMLAttributes & VNodeProps>

type NavLeaf = {
  name: string
  to: string
  icon: NavIcon
  role?: string
  dept?: 'sales' | 'software' | 'all'
  type?: undefined
  indent?: boolean
}

type NavSection = {
  name: string
  type: 'section'
  role?: string
}

type NavGroupChild = NavLeaf | NavSection

type NavGroup = {
  name: string
  type: 'group'
  icon: NavIcon
  role?: string
  dept?: 'sales' | 'software' | 'all'
  children: NavGroupChild[]
}

type NavigationItem = NavLeaf | NavSection | NavGroup

const allNavigation: NavigationItem[] = [
  // ── Admin ──────────────────────────────────────────────────────────────────
  { name: 'Genel Bakis', to: '/admin', icon: HomeIcon, role: 'admin' },
  { name: 'Personel Yonetimi', to: '/admin/employees', icon: UsersIcon, role: 'admin' },
  { name: 'Veri Yonetimi', to: '/admin/data-management', icon: DocumentTextIcon, role: 'admin' },
  { name: 'Yapay Zeka Icgoruleri', to: '/admin/ai-insights', icon: ChartBarIcon, role: 'admin' },
  { name: 'Anket Sonuclari', to: '/admin/survey-results', icon: DocumentTextIcon, role: 'admin' },
  { name: 'Satis ML Analizi', to: '/admin/sales-analytics', icon: ChartBarIcon, role: 'admin' },
  {
    name: '360 Derece Feedback',
    type: 'group',
    icon: ChatBubbleLeftRightIcon,
    role: 'admin',
    children: [
      { name: 'Feedback', to: '/feedback', icon: ChatBubbleLeftRightIcon },
      { name: '360 Derece Feedback Raporlari', type: 'section' },
      { name: 'Calisan Analizi', to: '/admin/feedback-reports/employees', icon: UsersIcon },
      { name: 'Departman Analizi', to: '/admin/feedback-reports/department', icon: DocumentTextIcon },
    ],
  },

  // ── Yazilim Yoneticisi ─────────────────────────────────────────────────────
  { name: 'Departman Performansi', to: '/manager', icon: ChartBarIcon, role: 'department_manager', dept: 'software' },
  {
    name: 'KPI & ML Analizi',
    type: 'group',
    icon: ChartBarIcon,
    role: 'department_manager',
    dept: 'software',
    children: [
      { name: 'Model Durumu', to: '/manager/kpi-ml-analysis?section=model', icon: ChartBarIcon },
      { name: 'Departman Analizi', to: '/manager/kpi-ml-analysis?section=department', icon: DocumentTextIcon },
      { name: 'Takim Analizi', to: '/manager/kpi-ml-analysis?section=teams', icon: UsersIcon },
      { name: 'Calisan Analizi', to: '/manager/kpi-ml-analysis?section=watchlist', icon: UsersIcon },
      { name: 'Teknik Detaylar', to: '/manager/kpi-ml-analysis?section=technical', icon: Cog6ToothIcon },
    ],
  },

  // ── Satis Yoneticisi ────────────────────────────────────────────────────────
  { name: 'Departman Performansi', to: '/manager', icon: ChartBarIcon, role: 'department_manager', dept: 'sales' },
  {
    name: 'Satis KPI & ML',
    type: 'group',
    icon: ChartBarIcon,
    role: 'department_manager',
    dept: 'sales',
    children: [
      { name: 'Performans Analizi', to: '/manager/sales-analytics', icon: ChartBarIcon },
      { name: 'Takim Riski', to: '/manager/sales-analytics', icon: UsersIcon },
    ],
  },

  // ── Ortak Yonetici ─────────────────────────────────────────────────────────
  { name: 'Ekibim', to: '/manager/team', icon: UsersIcon, role: 'department_manager' },
  { name: 'Anket Sonuclari', to: '/manager/survey-results', icon: DocumentTextIcon, role: 'department_manager' },
  {
    name: '360 Derece Feedback',
    type: 'group',
    icon: ChatBubbleLeftRightIcon,
    role: 'department_manager',
    children: [
      { name: 'Feedback', to: '/feedback', icon: ChatBubbleLeftRightIcon },
      { name: '360 Derece Feedback Raporlari', type: 'section' },
      { name: 'Calisan Analizi', to: '/manager/feedback-reports/employees', icon: UsersIcon },
      { name: 'Departman Analizi', to: '/manager/feedback-reports/department', icon: DocumentTextIcon },
    ],
  },

  // ── Yazilim Calisan ────────────────────────────────────────────────────────
  { name: 'Kisisel Gelisim', to: '/employee', icon: UserIcon, role: 'employee', dept: 'software' },
  { name: '360 Derece Feedback', to: '/feedback', icon: ChatBubbleLeftRightIcon, role: 'employee', dept: 'software' },
  { name: 'Nabiz Anketi', to: '/employee/pulse', icon: HeartIcon, role: 'employee', dept: 'software' },

  // ── Satis Calisan ──────────────────────────────────────────────────────────
  { name: 'Satis Performansim', to: '/employee/sales', icon: ChartBarIcon, role: 'employee', dept: 'sales' },
  { name: '360 Derece Feedback', to: '/feedback', icon: ChatBubbleLeftRightIcon, role: 'employee', dept: 'sales' },
  { name: 'Nabiz Anketi', to: '/employee/pulse', icon: HeartIcon, role: 'employee', dept: 'sales' },

  // ── Ortak ──────────────────────────────────────────────────────────────────
  { name: 'Ayarlar', to: '/settings', icon: Cog6ToothIcon, role: 'all' },
]

const navigation = computed(() =>
  allNavigation.filter((item) => {
    if (item.role !== 'all' && item.role !== userRole.value) return false
    if (!('dept' in item) || !item.dept || item.dept === 'all') return true
    if (item.dept === 'sales') return isSalesDept.value
    if (item.dept === 'software') return !isSalesDept.value
    return true
  })
)

const openGroups = ref<string[]>(['360 Derece Feedback', 'KPI & ML Analizi', 'Satis KPI & ML'])

const isActiveRoute = (target: string) => {
  if (target.includes('?')) {
    return route.fullPath === target
  }
  const targetPath = target.split('?')[0]
  if (['/manager', '/admin', '/employee', '/feedback', '/settings'].includes(target)) {
    return route.path === target
  }
  return route.path === targetPath || route.path.startsWith(`${targetPath}/`)
}

const isGroupOpen = (groupName: string) => openGroups.value.includes(groupName)

const toggleGroup = (groupName: string) => {
  if (isGroupOpen(groupName)) {
    openGroups.value = openGroups.value.filter((item) => item !== groupName)
    return
  }
  openGroups.value = [...openGroups.value, groupName]
}

const isGroupActive = (item: NavGroup) => item.children.some((child) => 'to' in child && isActiveRoute(child.to))

const handlePulseSubmit = async (data: any) => {
  try {
    const payload = {
      employee_id: authStore.user?.id || 1,
      period_date: new Date().toISOString().split('T')[0],
      ...data,
    }
    await employeeApi.submitWeeklyPulse(payload)
    isWeeklyPulseModalOpen.value = false
    alert('Anketiniz basariyla kaydedildi. Motivasyon analiziniz guncellendi.')
  } catch (error: any) {
    if (error.response?.data?.detail) {
      alert(error.response.data.detail)
      return
    }
    alert('Anket gonderilirken bir hata olustu.')
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const goBack = () => {
  router.back()
}
</script>
