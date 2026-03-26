// propel-frontend/src/services/api/feedback.api.ts
// 360° Geri Bildirim Modülü — API Servisi

import { apiClient } from './client'

// ──────────────────────────────────────────────
// TİPLER
// ──────────────────────────────────────────────

export type FeedbackType =
  | 'manager_to_employee'
  | 'employee_to_manager'
  | 'peer_to_peer'
  | 'self_assessment'

export type FeedbackStatus = 'pending' | 'completed' | 'declined' | 'expired'

export type BadgeType =
  | 'team_player'
  | 'problem_solver'
  | 'communicator'
  | 'speed_champion'
  | 'mentor'
  | 'innovator'
  | 'reliable'

export type BadgeLevel = 'bronze' | 'silver' | 'gold'

export interface FeedbackCreate {
  reviewee_id: number
  feedback_type: FeedbackType
  period_date: string // "2024-03-01"
  score_communication?: number
  score_teamwork?: number
  score_problem_solving?: number
  score_leadership?: number
  score_technical?: number
  strength_text?: string
  improvement_text?: string
  general_comment?: string
  is_anonymous?: boolean
  is_voice_input?: boolean
  request_id?: number
}

export interface FeedbackResponse {
  id: number
  reviewer_id: number
  reviewee_id: number
  feedback_type: FeedbackType
  period_date: string
  score_communication?: number
  score_teamwork?: number
  score_problem_solving?: number
  score_leadership?: number
  score_technical?: number
  strength_text?: string
  improvement_text?: string
  general_comment?: string
  is_anonymous: boolean
  is_voice_input: boolean
  nlp_result?: any
  request_id?: number
  created_at: string
  updated_at: string
  reviewer?: { id: number; position?: string; user_id: number; full_name?: string }
  reviewee?: { id: number; position?: string; user_id: number; full_name?: string }
}

export interface FeedbackRequestCreate {
  target_id: number
  period_date: string
  deadline?: string
  message?: string
}

export interface FeedbackRequestResponse {
  id: number
  requester_id: number
  target_id: number
  status: FeedbackStatus
  period_date: string
  deadline?: string
  message?: string
  created_at: string
  updated_at: string
}

export interface BadgeResponse {
  id: number
  employee_id: number
  badge_type: BadgeType
  badge_level: BadgeLevel
  period_date: string
  created_at: string
}

export interface FeedbackSummary {
  employee_id: number
  total_received: number
  avg_communication?: number
  avg_teamwork?: number
  avg_problem_solving?: number
  avg_leadership?: number
  avg_technical?: number
  overall_avg?: number
  badges: BadgeResponse[]
}

export interface EmployeeForFeedback {
  id: number
  position?: string
  user_id: number
  department: { id: number; name: string }
  user: { id: number; email: string; full_name: string; role: string }
}

// ──────────────────────────────────────────────
// API FONKSİYONLARI
// ──────────────────────────────────────────────

export const feedbackApi = {

  // Feedback gönder
  async createFeedback(data: FeedbackCreate): Promise<FeedbackResponse> {
    const { data: res } = await apiClient.post<FeedbackResponse>('/feedback/', data)
    return res
  },

  // Aldığım feedbackler
  async getReceivedFeedbacks(periodDate?: string): Promise<FeedbackResponse[]> {
    const params = periodDate ? { period_date: periodDate } : {}
    const { data } = await apiClient.get<FeedbackResponse[]>('/feedback/received', { params })
    return data
  },

  // Verdiğim feedbackler
  async getGivenFeedbacks(): Promise<FeedbackResponse[]> {
    const { data } = await apiClient.get<FeedbackResponse[]>('/feedback/given')
    return data
  },

  // Kendi özet skorlarım
  async getMyFeedbackSummary(periodDate?: string): Promise<FeedbackSummary> {
    const params = periodDate ? { period_date: periodDate } : {}
    const { data } = await apiClient.get<FeedbackSummary>('/feedback/summary/me', { params })
    return data
  },

  // Feedback talep et
  async createFeedbackRequest(data: FeedbackRequestCreate): Promise<FeedbackRequestResponse> {
    const { data: res } = await apiClient.post<FeedbackRequestResponse>('/feedback/requests', data)
    return res
  },

  // Bana gelen talepler
  async getIncomingRequests(): Promise<FeedbackRequestResponse[]> {
    const { data } = await apiClient.get<FeedbackRequestResponse[]>('/feedback/requests/incoming')
    return data
  },

  // Talebi kabul/reddet
  async updateRequestStatus(requestId: number, status: FeedbackStatus): Promise<FeedbackRequestResponse> {
    const { data } = await apiClient.patch<FeedbackRequestResponse>(`/feedback/requests/${requestId}`, { status })
    return data
  },

  // Rozetlerim
  async getMyBadges(): Promise<BadgeResponse[]> {
    const { data } = await apiClient.get<BadgeResponse[]>('/feedback/badges/me')
    return data
  },

  // Tüm çalışanları getir (feedback vermek için liste)
  async getAllEmployees(): Promise<EmployeeForFeedback[]> {
    const { data } = await apiClient.get<EmployeeForFeedback[]>('/employees/')
    return data
  },
}