import { apiClient } from './client'

export interface TeamHealthStat {
  key: string
  label: string
  value: string
  hint: string
  tone: string
}

export interface TeamHealthSourceSummary {
  kpi_analyzed_count: number
  pulse_response_count: number
  feedback_profile_count: number
  latest_kpi_period?: string | null
  latest_pulse_period?: string | null
  latest_feedback_update?: string | null
}

export interface TeamHealthMember {
  id: number
  name: string
  role: string
  team?: string | null
  external_employee_code?: string | null
  latest_pulse_score?: number | null
  latest_mte?: number | null
  latest_ars?: number | null
  kpi_score?: number | null
  kpi_trend?: number | null
  kpi_latest_period?: string | null
  kpi_band?: string | null
  kpi_confidence?: number | null
  kpi_top_driver?: string | null
  kpi_source?: string | null
  feedback_count: number
  feedback_sentiment_score?: number | null
  feedback_motivation_score?: number | null
  feedback_flight_risk_level?: string | null
  feedback_flight_risk_confidence?: number | null
  feedback_burnout_risk_level?: string | null
  feedback_burnout_risk_confidence?: number | null
  nlp_review_status?: string | null
  nlp_review_note?: string | null
  nlp_reviewed_at?: string | null
  nlp_reviewer_name?: string | null
  combined_risk_score: number
  combined_risk_level: 'Low' | 'Medium' | 'High' | string
  recommended_action: string
  data_sources: string[]
}

export interface TeamHealthResponse {
  generated_at: string
  department_id?: number | null
  department_name?: string | null
  member_count: number
  stats: TeamHealthStat[]
  source_summary: TeamHealthSourceSummary
  members: TeamHealthMember[]
}

export const employeeApi = {
  submitWeeklyPulse: async (data: any) => {
    const response = await apiClient.post('/surveys/weekly-pulse', data)
    return response.data
  },
  getEmployees: async () => {
    const response = await apiClient.get('/employees/')
    return response.data
  },
  getEmployee: async (id: number) => {
    const response = await apiClient.get(`/employees/${id}`)
    return response.data
  },
  getTeamHealth: async (): Promise<TeamHealthResponse> => {
    const response = await apiClient.get('/employees/team-health')
    return response.data
  },
  getDepartments: async () => {
    const response = await apiClient.get('/departments/')
    return response.data
  }
}
