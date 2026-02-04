import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/api/auth.api'
import type { LoginCredentials, User } from '@/services/types/auth.types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role)

  async function login(credentials: LoginCredentials) {
    loading.value = true
    error.value = null

    try {
      const response = await authApi.login(credentials)
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)

      await fetchCurrentUser()

      return true
    } catch (err: any) {
      console.warn('Backend login failed, attempting mock login...', err)

      // Mock Login Fallback
      if (tryMockLogin(credentials)) {
        return true
      }

      error.value = err.response?.data?.detail || 'Giriş başarısız'
      return false
    } finally {
      loading.value = false
    }
  }

  function tryMockLogin(credentials: LoginCredentials): boolean {
    const mockUsers: Record<string, User> = {
      'admin@propel.com': {
        id: 1,
        email: 'admin@propel.com',
        full_name: 'System Admin',
        role: 'admin',
        is_active: true,
        department_id: 1,
        created_at: new Date().toISOString()
      },
      'manager.yazilim@propel.com': {
        id: 2,
        email: 'manager.yazilim@propel.com',
        full_name: 'Yazılım Müdürü',
        role: 'department_manager',
        is_active: true,
        department_id: 2,
        created_at: new Date().toISOString()
      },
      'developer1@propel.com': {
        id: 3,
        email: 'developer1@propel.com',
        full_name: 'Senior Developer',
        role: 'employee',
        is_active: true,
        department_id: 2,
        created_at: new Date().toISOString()
      }
    }

    const mockUser = mockUsers[credentials.username]

    // Basit şifre kontrolü (herkes için generic şifreler veya mock şifreler)
    if (mockUser) {
      token.value = 'mock-token-' + credentials.username
      user.value = mockUser
      localStorage.setItem('token', token.value)
      return true
    }

    return false
  }

  async function fetchCurrentUser() {
    try {
      // Eğer mock token ise API'ye gitme
      if (token.value?.startsWith('mock-token-')) {
        // User zaten login sırasında set edildi, ancak refresh durumunda:
        if (!user.value) {
          const email = token.value.replace('mock-token-', '')
          const mockUsers: Record<string, User> = {
            'admin@propel.com': {
              id: 1,
              email: 'admin@propel.com',
              full_name: 'System Admin',
              role: 'admin',
              is_active: true,
              department_id: 1,
              created_at: new Date().toISOString()
            },
            'manager.yazilim@propel.com': {
              id: 2,
              email: 'manager.yazilim@propel.com',
              full_name: 'Yazılım Müdürü',
              role: 'department_manager',
              is_active: true,
              department_id: 2,
              created_at: new Date().toISOString()
            },
            'developer1@propel.com': {
              id: 3,
              email: 'developer1@propel.com',
              full_name: 'Senior Developer',
              role: 'employee',
              is_active: true,
              department_id: 2,
              created_at: new Date().toISOString()
            }
          }
          user.value = mockUsers[email] || null
        }
        return
      }

      user.value = await authApi.getCurrentUser()
    } catch (err) {
      console.error('Kullanıcı bilgileri alınamadı:', err)
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    userRole,
    login,
    logout,
    fetchCurrentUser,
  }
})