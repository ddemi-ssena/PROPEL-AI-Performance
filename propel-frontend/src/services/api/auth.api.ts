import { apiClient } from './client'
import type { LoginCredentials, RegisterData, AuthResponse, User } from '../types/auth.types'

export const authApi = {
  async register(data: RegisterData): Promise<User> {
    const { data: userData } = await apiClient.post<User>('/auth/register', data)
    return userData
  },

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const { data } = await apiClient.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return data
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  },
}