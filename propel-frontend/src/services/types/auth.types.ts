export interface LoginCredentials {
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'department_manager' | 'employee'
  is_active: boolean
  created_at: string
}