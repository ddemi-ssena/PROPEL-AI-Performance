<template>
  <div class="min-h-screen bg-gray-50 flex font-sans text-slate-800">
    <!-- Sidebar -->
    <aside class="w-72 bg-slate-900 border-r border-slate-800 hidden md:flex flex-col shadow-xl z-20">
      <div class="p-6 border-b border-slate-800 flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <span class="text-white font-bold text-lg">P</span>
        </div>
        <div>
            <h1 class="text-xl font-bold text-white tracking-tight">
            TeamPulse
            </h1>
            <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Enterprise</p>
        </div>
      </div>

      <nav class="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
        <div class="mb-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Menu
        </div>
        <template v-for="item in navigation" :key="item.name">
          <router-link
            v-if="!item.role || item.role === userRole"
            :to="item.to"
            class="flex items-center gap-3 px-3 py-3 text-sm font-medium rounded-lg transition-all duration-200 group"
            :class="[
              $route.path === item.to
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/20'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            ]"
          >
            <component 
                :is="item.icon" 
                class="w-5 h-5 flex-shrink-0 transition-colors"
                :class="$route.path === item.to ? 'text-white' : 'text-slate-500 group-hover:text-white'"
            />
            {{ item.name }}
          </router-link>
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

    <!-- Mobile Header -->
    <div class="md:hidden flex flex-col min-h-screen w-full">
        <!-- Header implementation for mobile can be added here -->
    </div>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto bg-gray-50/50">
      <header class="bg-white/80 backdrop-blur-md border-b border-gray-200 px-8 py-5 flex items-center justify-between sticky top-0 z-10 transition-shadow hover:shadow-sm">
        <div class="flex items-center gap-4">
          <button @click="goBack" class="p-2 text-slate-400 hover:text-slate-700 hover:bg-gray-100/80 rounded-lg transition-colors" title="Geri Dön">
            <ArrowLeftIcon class="w-5 h-5" />
          </button>
          <div>
              <h2 class="text-xl font-bold text-slate-900 tracking-tight">
                {{ pageTitle }}
              </h2>
          </div>
        </div>
        <div class="flex items-center gap-4">
            <button class="p-2 text-slate-400 hover:text-indigo-600 rounded-full hover:bg-indigo-50 transition-all relative">
                <BellIcon class="w-6 h-6" />
                <span class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
            </button>
        </div>
      </header>

      <div class="p-6">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  HomeIcon,
  UsersIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  BellIcon,
  ArrowLeftIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Gerçek kullanıcı verilerini Store'dan al
// Fallback olarak localStorage kontrolü
const userRole = computed(() => authStore.user?.role || localStorage.getItem('role') || 'employee')
const userName = computed(() => authStore.user?.full_name || 'Kullanıcı')

const userInitials = computed(() => {
  return userName.value.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
})

const userRoleLabel = computed(() => {
  const roles: Record<string, string> = {
    admin: 'Sistem Yöneticisi',
    department_manager: 'Departman Yöneticisi',
    employee: 'Personel'
  }
  return roles[userRole.value] || 'Kullanıcı'
})

const pageTitle = computed(() => {
    return route.meta.title || 'TeamPulse'
})

// Navigation items definition
const allNavigation = [
  // Admin Routes
  { name: 'Genel Bakış', to: '/admin', icon: HomeIcon, role: 'admin' },
  { name: 'Departman Yönetimi', to: '/admin/departments', icon: BuildingOfficeIcon, role: 'admin' },
  { name: 'Personel Yönetimi', to: '/admin/employees', icon: UsersIcon, role: 'admin' },
  
  // Manager Routes
  { name: 'Departman Performansı', to: '/manager', icon: ChartBarIcon, role: 'department_manager' },
  { name: 'Ekibim', to: '/manager/team', icon: UsersIcon, role: 'department_manager' },
  
  // Employee Routes
  { name: 'Kişisel Gelişim', to: '/employee', icon: UserIcon, role: 'employee' },
  { name: 'Performansım', to: '/employee/performance', icon: ChartBarIcon, role: 'employee' },
]

// Filter navigation based on active role
const navigation = computed(() => {
  return allNavigation.filter(item => item.role === userRole.value)
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const goBack = () => {
  router.back()
}
</script>
