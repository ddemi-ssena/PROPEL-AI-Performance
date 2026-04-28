import { apiClient } from './client'

export interface AnalyticsLayerResponse {
  key: string
  title: string
  summary: string
}

export interface DepartmentAnalyticsConfigResponse {
  key: string
  label: string
  description: string
  readiness_status: string
  supports_live_data: boolean
  planned_targets: string[]
  supported_teams: string[]
  layers: AnalyticsLayerResponse[]
}

export interface AnalyticsMetricCardResponse {
  key: string
  label: string
  value: string
  tone: string
  hint: string
}

export interface TeamAnalyticsSnapshotResponse {
  team: string
  employee_count: number
  average_score: number
  average_trend_delta?: number | null
  watchlist_count: number
}

export interface EmployeeAnalyticsSnapshotResponse {
  employee_id: number
  employee_name: string
  team?: string | null
  position?: string | null
  external_employee_code?: string | null
  latest_score: number
  previous_score?: number | null
  trend_delta?: number | null
  strongest_category?: string | null
  weakest_category?: string | null
  risk_band: string
}

export interface DepartmentAnalyticsOverviewResponse {
  definition: DepartmentAnalyticsConfigResponse
  department_name: string
  selected_team?: string | null
  selected_employee_id?: number | null
  latest_period?: string | null
  metrics: AnalyticsMetricCardResponse[]
  team_summaries: TeamAnalyticsSnapshotResponse[]
  employee_summaries: EmployeeAnalyticsSnapshotResponse[]
  notes: string[]
  sprint_focus: string[]
}

export const analyticsApi = {
  async getDepartmentConfigs(): Promise<DepartmentAnalyticsConfigResponse[]> {
    const { data } = await apiClient.get<DepartmentAnalyticsConfigResponse[]>('/analytics/departments')
    return data
  },

  async getDepartmentOverview(
    departmentKey: string,
    params?: { team?: string; employee_id?: number }
  ): Promise<DepartmentAnalyticsOverviewResponse> {
    const { data } = await apiClient.get<DepartmentAnalyticsOverviewResponse>(
      `/analytics/departments/${departmentKey}/overview`,
      { params }
    )
    return data
  },
}
