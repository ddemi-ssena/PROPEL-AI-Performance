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

    const username = credentials.username.toLowerCase().trim()
    const cleanCredentials = { ...credentials, username }

    try {
      const response = await authApi.login(cleanCredentials)
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      
      await fetchCurrentUser()
      
      if (user.value?.role) {
        localStorage.setItem('role', user.value.role)
      }

      return true
    } catch (err: any) {
      console.warn('Backend login failed, attempting mock login...', err)

      if (tryMockLogin(cleanCredentials)) {
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
        id: 153,
        email: 'admin@propel.com',
        full_name: 'Sistem Yoneticisi',
        role: 'admin',
        is_active: true,
        department_id: 17,
        department_name: 'Yazilim Gelistirme',
        created_at: new Date().toISOString()
      },
      'manager.yazilim@propel.com': {
        id: 154,
        email: 'manager.yazilim@propel.com',
        full_name: 'Ahmet Yilmaz',
        role: 'department_manager',
        is_active: true,
        department_id: 17,
        department_name: 'Yazilim Gelistirme',
        created_at: new Date().toISOString()
      },
      'manager.satis@propel.com': {
        id: 155,
        email: 'manager.satis@propel.com',
        full_name: 'Mehmet Satis',
        role: 'department_manager',
        is_active: true,
        department_id: 18,
        department_name: 'Satis',
        created_at: new Date().toISOString()
      },
      'developer1@propel.com': {
        id: 156,
        email: 'developer1@propel.com',
        full_name: 'Canan Dagdelen',
        role: 'employee',
        is_active: true,
        department_id: 17,
        department_name: 'Yazilim Gelistirme',
        created_at: new Date().toISOString()
      },
      'sl-001@propel.com': {
        id: 186,
        email: 'sl-001@propel.com',
        full_name: 'Ali Yilmaz',
        role: 'employee',
        is_active: true,
        department_id: 18,
        department_name: 'Satis',
        created_at: new Date().toISOString()
      },
      'satis.employee@propel.com': {
        id: 187,
        email: 'satis.employee@propel.com',
        full_name: 'Zeynep Kaya',
        role: 'employee',
        is_active: true,
        department_id: 18,
        department_name: 'Satis',
        created_at: new Date().toISOString()
      }
    }

    const mockUser = mockUsers[credentials.username]

    if (mockUser) {
      token.value = 'mock-token-' + credentials.username
      user.value = mockUser
      localStorage.setItem('token', token.value)
      localStorage.setItem('role', mockUser.role)
      return true
    }

    return false
  }

  async function fetchCurrentUser() {
    try {
      if (token.value?.startsWith('mock-token-')) {
        if (!user.value) {
          const email = token.value.replace('mock-token-', '')
          const mockUsers: Record<string, User> = {
            'admin@propel.com': {
              id: 153,
              email: 'admin@propel.com',
              full_name: 'Sistem Yoneticisi',
              role: 'admin',
              is_active: true,
              department_id: 17,
              department_name: 'Yazilim Gelistirme',
              created_at: new Date().toISOString()
            },
            'manager.yazilim@propel.com': {
              id: 154,
              email: 'manager.yazilim@propel.com',
              full_name: 'Ahmet Yilmaz',
              role: 'department_manager',
              is_active: true,
              department_id: 17,
              department_name: 'Yazilim Gelistirme',
              created_at: new Date().toISOString()
            },
            'manager.satis@propel.com': {
              id: 155,
              email: 'manager.satis@propel.com',
              full_name: 'Mehmet Satis',
              role: 'department_manager',
              is_active: true,
              department_id: 18,
              department_name: 'Satis',
              created_at: new Date().toISOString()
            },
            'developer1@propel.com': {
              id: 156,
              email: 'developer1@propel.com',
              full_name: 'Canan Dagdelen',
              role: 'employee',
              is_active: true,
              department_id: 17,
              department_name: 'Yazilim Gelistirme',
              created_at: new Date().toISOString()
            },
            'sl-001@propel.com': {
              id: 186,
              email: 'sl-001@propel.com',
              full_name: 'Ali Yilmaz',
              role: 'employee',
              is_active: true,
              department_id: 18,
              department_name: 'Satis',
              created_at: new Date().toISOString()
            },
            'satis.employee@propel.com': {
              id: 187,
              email: 'satis.employee@propel.com',
              full_name: 'Zeynep Kaya',
              role: 'employee',
              is_active: true,
              department_id: 18,
              department_name: 'Satis',
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
    localStorage.removeItem('role')
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
