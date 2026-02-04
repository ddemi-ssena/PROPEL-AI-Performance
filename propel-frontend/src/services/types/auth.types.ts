export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  full_name: string
  email: string
  password: string
  role: 'admin' | 'department_manager' | 'employee'
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
  department_id?: number
  created_at: string
}