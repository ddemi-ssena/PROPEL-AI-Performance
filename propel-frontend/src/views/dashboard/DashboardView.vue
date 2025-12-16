<template>
  <div class="min-h-screen bg-gray-100 p-8">
    <div class="max-w-7xl mx-auto">
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p class="text-gray-600 mt-1">Welcome, {{ authStore.user?.full_name }}</p>
          </div>
          <button @click="handleLogout" class="btn-primary">
            Logout
          </button>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-6">
        <div class="card">
          <h3 class="text-sm font-medium text-gray-500 mb-2">Role</h3>
          <p class="text-2xl font-bold text-gray-900">{{ authStore.user?.role }}</p>
        </div>
        
        <div class="card">
          <h3 class="text-sm font-medium text-gray-500 mb-2">Email</h3>
          <p class="text-lg text-gray-900">{{ authStore.user?.email }}</p>
        </div>
        
        <div class="card">
          <h3 class="text-sm font-medium text-gray-500 mb-2">Status</h3>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            Active
          </span>
        </div>
      </div>

      <div class="mt-8 card">
        <h2 class="text-xl font-bold mb-4">Coming Soon...</h2>
        <p class="text-gray-600">Dashboard components will be added here.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchCurrentUser()
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>