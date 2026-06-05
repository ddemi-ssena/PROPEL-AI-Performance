// propel-frontend/src/services/api/feedback.api.ts
// 360° Geri Bildirim Modülü — API Servisi

import { apiClient } from './client'

// ──────────────────────────────────────────────
// TİPLER
// ──────────────────────────────────────────────

export type ClassicFeedbackType =
  | 'manager_to_employee'
  | 'employee_to_manager'
  | 'peer_to_peer'
  | 'self_assessment'

export type WeeklyFeedbackDirection =
  | 'manager_to_employee'
  | 'employee_to_manager'
  | 'peer_to_peer'
  | 'manager_to_manager'
  | 'employee_to_employee'

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
  feedback_type: ClassicFeedbackType
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
  feedback_type: ClassicFeedbackType
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
  source_feedback_ids?: number[]
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
  external_employee_code?: string
  team?: string
  position?: string
  experience_years?: number
  user_id: number
  department_id: number
  department: { id: number; name: string }
  user: { id: number; email: string; full_name: string; role: string }
}

export interface WeeklyQuestionResponse {
  question_id: number
  week_number: number
  category: string
  direction: WeeklyFeedbackDirection
  question_text: string
  is_ai_generated: boolean
}

export interface WeeklyFeedbackSubmitPayload {
  receiver_id: number
  response_text: string
  score_communication: number
  score_teamwork: number
  score_leadership: number
  score_technical: number
}

export interface WeeklyProgressResponse {
  week_number: number
  required_count: number
  completed_count: number
  remaining_count: number
  is_completed: boolean
}

export interface WeeklyAssignmentTargetResponse {
  id: number
  status: string
  assignment_type: string
  employee: EmployeeForFeedback
}

export interface WeeklyAssignmentStateResponse {
  week_number: number
  required_count: number
  completed_count: number
  remaining_count: number
  is_completed: boolean
  current_slot: 'mandatory_random' | 'department_internal' | 'cross_functional' | 'completed'
  assignment_required: boolean
  mandatory_assignment?: WeeklyAssignmentTargetResponse | null
  available_candidates: EmployeeForFeedback[]
  department_candidates: EmployeeForFeedback[]
  cross_functional_candidates: EmployeeForFeedback[]
  rules_summary: string[]
}

export type NLPRiskLevel = 'low' | 'medium' | 'high'
export type NLPSentimentLabel = 'positive' | 'neutral' | 'negative'

export interface WeeklyNLPAnalysis {
  id: number
  source_type: 'weekly_feedback' | 'classic_feedback'
  weekly_feedback_id?: number
  classic_feedback_id?: number
  employee_id: number
  reviewer_employee_id?: number
  department_id?: number
  direction?: string
  theme?: string
  analysis_version: string
  model_provider?: string
  model_name?: string
  sentiment_label?: NLPSentimentLabel
  sentiment_score?: number
  motivation_score?: number
  burnout_risk?: NLPRiskLevel
  flight_risk?: NLPRiskLevel
  psychological_safety_score?: number
  collaboration_score?: number
  growth_signal_score?: number
  leadership_support_score?: number | null
  key_strengths: string[]
  risk_flags: string[]
  support_needs: string[]
  keywords: string[]
  manager_summary?: string
  raw_analysis?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface EmployeeNLPProfile {
  id: number
  employee_id: number
  department_id?: number
  period_type: 'weekly' | 'monthly'
  period_year: number
  period_month: number
  period_week?: number
  feedback_count: number
  avg_sentiment_score?: number
  avg_motivation_score?: number
  avg_psychological_safety_score?: number
  avg_collaboration_score?: number
  avg_growth_signal_score?: number
  burnout_risk_level?: NLPRiskLevel
  flight_risk_level?: NLPRiskLevel
  top_strengths: string[]
  top_risk_areas: string[]
  top_support_needs: string[]
  manager_summary?: string
  recommended_action?: string
  created_at: string
  updated_at: string
}

export interface WeeklyNLPInsightResponse {
  profile: EmployeeNLPProfile
  recent_analyses: WeeklyNLPAnalysis[]
}

export interface NLPTestAnalysisPayload {
  response_text: string
  question_text?: string
  department_id?: number
  target_role?: 'admin' | 'department_manager' | 'employee'
  week_theme?: string
  direction_label?: string
  score_communication?: number
  score_teamwork?: number
  score_leadership?: number
  score_technical?: number
}

export interface NLPTestAnalysisResponse {
  department_name: string
  model_provider: string
  model_name: string
  analysis: Record<string, any>
}

export interface DepartmentWeeklyNLPResponse {
  department_id: number
  period_year: number
  period_month: number
  period_week: number
  employee_count: number
  analyzed_employee_count: number
  avg_sentiment_score?: number
  avg_motivation_score?: number
  avg_psychological_safety_score?: number
  avg_collaboration_score?: number
  avg_growth_signal_score?: number
  high_burnout_count: number
  high_flight_risk_count: number
  top_strengths: string[]
  top_risk_areas: string[]
  top_support_needs: string[]
  headline: string
  recommended_action?: string
}

export interface SummaryMetric {
  label: string
  value?: number
  display_value: string
  risk_level?: 'low' | 'medium' | 'high' | string
  description?: string
}

export interface SummarySection {
  title: string
  items: string[]
}

export interface SkillScore {
  label: string
  value: number | null
}

export interface Employee360SummaryReportResponse {
  employee_id: number
  employee_name: string
  department_id?: number
  department_name?: string
  team?: string
  position?: string
  period_year: number
  period_month: number
  period_week: number
  report_title: string
  report_summary: string
  recommended_action?: string
  badges: BadgeResponse[]
  metrics: SummaryMetric[]
  sections: SummarySection[]
  skill_scores?: SkillScore[]
}

export interface Department360SummaryReportResponse {
  department_id: number
  department_name: string
  period_year: number
  period_month: number
  period_week: number
  report_title: string
  report_summary: string
  recommended_action?: string
  metrics: SummaryMetric[]
  sections: SummarySection[]
}

export interface TrendPoint {
  label: string
  value: number
}

export interface DistributionPoint {
  label: string
  value: number
}

export interface ThemePoint {
  label: string
  value: number
}

export interface DepartmentNLPChartsResponse {
  department_id: number
  department_name: string
  period_year: number
  period_month: number
  motivation_trend: TrendPoint[]
  psychological_safety_trend: TrendPoint[]
  flight_risk_distribution: DistributionPoint[]
  burnout_risk_distribution: DistributionPoint[]
  top_risk_themes: ThemePoint[]
}

export interface EmployeeMonthlyDeepAnalysisResponse {
  employee_id: number
  employee_name: string
  period_year: number
  period_month: number
  feedback_count: number
  motivation_trend_direction: string
  sentiment_trend_direction: string
  top_complaint_topics: string[]
  top_praise_topics: string[]
  top_themes: string[]
  flight_risk_score?: number | null
  flight_risk_reasons: string[]
  action_recommendation?: string | null
}

export interface DepartmentMonthlyDeepAnalysisResponse {
  department_id: number
  department_name: string
  period_year: number
  period_month: number
  analyzed_feedback_count: number
  analyzed_employee_count: number
  motivation_trend_direction: string
  sentiment_trend_direction: string
  avg_flight_risk_score?: number | null
  top_complaint_topics: string[]
  top_praise_topics: string[]
  top_themes: string[]
  top_flight_risk_reasons: string[]
  action_recommendation?: string | null
}

export interface EmployeeMonthlyRAGReportResponse {
  employee_id: number
  employee_name: string
  department_id?: number | null
  department_name?: string | null
  team?: string | null
  period_year: number
  period_month: number
  report_summary: string
  trend_summary: string
  flight_risk_score?: number | null
  retention_risk_level?: string | null
  top_complaint_topics: string[]
  top_praise_topics: string[]
  key_takeaways: string[]
  action_recommendation?: string | null
  retrieved_memory_count: number
  retrieved_memory_summaries: string[]
  model_provider?: string | null
  model_name?: string | null
  confidence?: number | null
}

export interface DepartmentMonthlyRAGReportResponse {
  department_id: number
  department_name: string
  period_year: number
  period_month: number
  report_summary: string
  trend_summary: string
  flight_risk_score?: number | null
  retention_risk_level?: string | null
  top_complaint_topics: string[]
  top_praise_topics: string[]
  key_takeaways: string[]
  action_recommendation?: string | null
  retrieved_memory_count: number
  retrieved_memory_summaries: string[]
  model_provider?: string | null
  model_name?: string | null
  confidence?: number | null
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

  // Feedback verilebilecek adayları getir
  async getFeedbackCandidates(): Promise<EmployeeForFeedback[]> {
    const { data } = await apiClient.get<EmployeeForFeedback[]>('/feedback/candidates')
    return data
  },

  async getCurrentQuestion(receiverId: number): Promise<WeeklyQuestionResponse> {
    const { data } = await apiClient.get<WeeklyQuestionResponse>('/feedbacks/current-question', {
      params: { receiver_id: receiverId },
    })
    return data
  },

  async submitWeeklyFeedback(payload: WeeklyFeedbackSubmitPayload): Promise<void> {
    await apiClient.post('/feedbacks/submit', payload)
  },

  async getWeeklyProgress(): Promise<WeeklyProgressResponse> {
    const { data } = await apiClient.get<WeeklyProgressResponse>('/feedbacks/progress')
    return data
  },

  async getWeeklyAssignmentState(): Promise<WeeklyAssignmentStateResponse> {
    const { data } = await apiClient.get<WeeklyAssignmentStateResponse>('/feedbacks/assignment')
    return data
  },

  async getMyWeeklyNlpProfile(): Promise<WeeklyNLPInsightResponse> {
    const { data } = await apiClient.get<WeeklyNLPInsightResponse>('/feedbacks/nlp/me')
    return data
  },

  async testNlpAnalysis(payload: NLPTestAnalysisPayload): Promise<NLPTestAnalysisResponse> {
    const { data } = await apiClient.post<NLPTestAnalysisResponse>('/feedbacks/nlp/test-analysis', payload)
    return data
  },

  async getEmployeeWeeklyNlpProfile(employeeId: number): Promise<WeeklyNLPInsightResponse> {
    const { data } = await apiClient.get<WeeklyNLPInsightResponse>(`/feedbacks/nlp/employee/${employeeId}`)
    return data
  },

  async getDepartmentWeeklyNlpSummary(departmentId?: number): Promise<DepartmentWeeklyNLPResponse> {
    const { data } = await apiClient.get<DepartmentWeeklyNLPResponse>('/feedbacks/nlp/department-summary', {
      params: departmentId ? { department_id: departmentId } : {},
    })
    return data
  },

  async getEmployee360SummaryReport(employeeId: number): Promise<Employee360SummaryReportResponse> {
    const { data } = await apiClient.get<Employee360SummaryReportResponse>(`/feedbacks/reports/employee/${employeeId}`)
    return data
  },

  async getDepartment360SummaryReport(params?: { department_id?: number; team?: string }): Promise<Department360SummaryReportResponse> {
    const { data } = await apiClient.get<Department360SummaryReportResponse>('/feedbacks/reports/department', {
      params: params || {},
    })
    return data
  },

  async getDepartmentNlpCharts(params?: { department_id?: number; team?: string }): Promise<DepartmentNLPChartsResponse> {
    const { data } = await apiClient.get<DepartmentNLPChartsResponse>('/feedbacks/charts/department', {
      params: params || {},
    })
    return data
  },

  async getEmployeeMonthlyDeepAnalysis(
    employeeId: number,
    params?: { year?: number; month?: number }
  ): Promise<EmployeeMonthlyDeepAnalysisResponse> {
    const { data } = await apiClient.get<EmployeeMonthlyDeepAnalysisResponse>(
      `/feedbacks/reports/employee/${employeeId}/monthly-deep`,
      { params: params || {} }
    )
    return data
  },

  async getDepartmentMonthlyDeepAnalysis(
    params?: { department_id?: number; team?: string; year?: number; month?: number }
  ): Promise<DepartmentMonthlyDeepAnalysisResponse> {
    const { data } = await apiClient.get<DepartmentMonthlyDeepAnalysisResponse>(
      '/feedbacks/reports/department/monthly-deep',
      { params: params || {} }
    )
    return data
  },

  async getEmployeeMonthlyRagReport(
    employeeId: number,
    params?: { year?: number; month?: number }
  ): Promise<EmployeeMonthlyRAGReportResponse> {
    const { data } = await apiClient.get<EmployeeMonthlyRAGReportResponse>(
      `/feedbacks/reports/employee/${employeeId}/monthly-rag`,
      { params: params || {} }
    )
    return data
  },

  async getDepartmentMonthlyRagReport(
    params?: { department_id?: number; team?: string; year?: number; month?: number }
  ): Promise<DepartmentMonthlyRAGReportResponse> {
    const { data } = await apiClient.get<DepartmentMonthlyRAGReportResponse>(
      '/feedbacks/reports/department/monthly-rag',
      { params: params || {} }
    )
    return data
  },
}
