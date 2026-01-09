<template>
  <div class="min-h-screen flex">
    <!-- Sol Panel -->
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-500 to-blue-700 p-12 flex-col justify-between">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center">
          <span class="text-blue-500 font-bold text-xl">P</span>
        </div>
        <h1 class="text-white text-2xl font-bold">propel</h1>
      </div>

      <div class="text-white">
        <h2 class="text-4xl font-bold mb-4">
          Veriyle Güçlen,<br />
          Performansını Keşfet
        </h2>
        <p class="text-lg text-blue-100">
          Yapay zeka destekli performans analizi ile ekibinizin potansiyelini ortaya çıkarın.
        </p>
      </div>

      <div class="w-full h-64 bg-white/10 rounded-lg backdrop-blur-sm flex items-center justify-center">
        <p class="text-white/50 text-sm">📊 Illustration</p>
      </div>
    </div>

    <!-- Sağ Panel - Login Form -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
      <div class="w-full max-w-md">
        <div class="mb-8">
          <h2 class="text-3xl font-bold text-gray-900 mb-2">Welcome Back!</h2>
          <p class="text-gray-600">Sign in to continue to your dashboard</p>
        </div>

        <!-- Error Alert -->
        <div v-if="authStore.error" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-700 text-sm">{{ authStore.error }}</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Email address
            </label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </span>
              <input
                v-model="credentials.username"
                type="email"
                placeholder="Enter your email"
                class="input-field pl-10"
                required
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </span>
              <input
                v-model="credentials.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter your password"
                class="input-field pl-10 pr-10"
                required
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 flex items-center pr-3"
              >
                <svg v-if="!showPassword" class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Remember Me & Forgot Password -->
          <div class="flex items-center justify-between">
            <label class="flex items-center">
              <input type="checkbox" class="w-4 h-4 text-blue-500 border-gray-300 rounded focus:ring-blue-500" />
              <span class="ml-2 text-sm text-gray-600">Remember Me</span>
            </label>
            <a href="#" class="text-sm text-blue-500 hover:text-blue-600">
              Forgot Password?
            </a>
          </div>

          <!-- Login Button -->
          <button
            type="submit"
            :disabled="authStore.loading"
            class="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <span v-if="!authStore.loading">Login</span>
            <span v-else class="flex items-center gap-2">
              <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Logging in...
            </span>
          </button>
        </form>

        <!-- Test Accounts -->
        <div class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <p class="text-xs text-blue-900 font-semibold mb-2">🔐 Test Kullanıcıları:</p>
          <div class="space-y-1 text-xs text-blue-700">
            <p><strong>Admin:</strong> admin@propel.com / admin123</p>
            <p><strong>Manager:</strong> manager.yazilim@propel.com / manager123</p>
            <p><strong>Employee:</strong> developer1@propel.com / dev123</p>
          </div>
        </div>

        <!-- Register Link -->
        <p class="mt-6 text-center text-sm text-gray-600">
          New to propel?
          <router-link to="/register" class="text-blue-500 hover:text-blue-600 font-medium">
            Create an account
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const credentials = ref({
  username: '',
  password: '',
})

const showPassword = ref(false)

async function handleLogin() {
  const success = await authStore.login(credentials.value)
  
  if (success) {
    const role = authStore.user?.role
    
    if (role === 'admin') {
      router.push('/admin')
    } else if (role === 'department_manager') {
      router.push('/manager')
    } else if (role === 'employee') {
      router.push('/employee')
    } else {
      router.push('/dashboard')
    }
  }
}
</script>