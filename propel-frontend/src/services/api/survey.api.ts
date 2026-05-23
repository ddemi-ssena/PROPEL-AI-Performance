import { apiClient } from './client'

export interface SurveyResponse {
  id: number
  employee_id: number
  survey_type: string
  score: number
  period_date: string
  comments?: string
  created_at: string
  employee: {
    id: number
    position: string
    user_id: number
    full_name: string
  }
  raw_data?: any
  mte_score?: number
  ars_score?: number
}

export interface SurveyCreatePayload {
  employee_id: number
  survey_type: string
  score: number
  period_date: string
  comments?: string
}

export const surveyApi = {
  getResponses: async (params?: { skip?: number, limit?: number }) => {
    const response = await apiClient.get<SurveyResponse[]>('/surveys/', { params })
    return response.data
  },

  getById: async (id: number) => {
    const response = await apiClient.get<SurveyResponse>(`/surveys/${id}`)
    return response.data
  },

  createSurvey: async (payload: SurveyCreatePayload): Promise<SurveyResponse> => {
    const response = await apiClient.post<SurveyResponse>('/surveys/', payload)
    return response.data
  },
}
