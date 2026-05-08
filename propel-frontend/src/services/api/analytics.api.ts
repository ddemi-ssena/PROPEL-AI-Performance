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

export interface SoftwareModelTrainRequest {
  upload_id: number
  target_column: string
  model_name?: string
  test_period_count?: number
}

export interface SoftwareDatasetResponse {
  id: number
  file_name: string
  file_type: string
  status: string
  record_count: number
  upload_date: string
  raw_info?: Record<string, any> | null
}

export interface SoftwareDatasetEmployeeResponse {
  employee_id: number
  employee_name?: string | null
  display_label?: string | null
  external_employee_code?: string | null
  team?: string | null
  role?: string | null
  position?: string | null
  row_count: number
}

export interface SoftwareModelStateResponse {
  department: string
  upload_id: number
  target_column: string
  target_label: string
  is_trained: boolean
  is_current_dataset: boolean
  trained_at?: string | null
  model_name?: string | null
  train_count?: number | null
  test_count?: number | null
  labels: string[]
  metrics: Record<string, any>
  artifact_dir?: string | null
}

export interface SoftwareModelTrainResponse {
  department: string
  upload_id: number
  target_column: string
  model_name: string
  train_count: number
  test_count: number
  labels: string[]
  metrics: Record<string, any>
  top_features: Array<Record<string, any>>
  validation_summary: Record<string, any>
  artifact_dir: string
}

export interface SoftwarePredictionResponse {
  department: string
  upload_id: number
  employee_id: number
  target_column: string
  predicted_band: string
  confidence: number
  probabilities: Record<string, number>
  top_features: Array<Record<string, any>>
  risk_summary: string
  top_drivers: Array<Record<string, any>>
  recommended_actions: string[]
  summary_payload: Record<string, any>
  narrative?: Record<string, any> | null
}

export interface SoftwareBulkPredictionResponse {
  department: string
  upload_id: number
  target_column: string
  prediction_count: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  department_narrative?: Record<string, any> | null
  team_narratives: Array<Record<string, any>>
  team_analytics?: Array<Record<string, any>>
  items: SoftwarePredictionResponse[]
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

  async getSoftwareDatasets(): Promise<SoftwareDatasetResponse[]> {
    const { data } = await apiClient.get<SoftwareDatasetResponse[]>('/analytics/departments/software/datasets')
    return data
  },

  async getSoftwareDatasetEmployees(uploadId: number): Promise<SoftwareDatasetEmployeeResponse[]> {
    const { data } = await apiClient.get<SoftwareDatasetEmployeeResponse[]>(
      `/analytics/departments/software/datasets/${uploadId}/employees`
    )
    return data
  },

  async getSoftwareModelState(uploadId: number): Promise<SoftwareModelStateResponse[]> {
    const { data } = await apiClient.get<SoftwareModelStateResponse[]>(
      `/analytics/departments/software/datasets/${uploadId}/model-state`
    )
    return data
  },

  async trainSoftwareModel(payload: SoftwareModelTrainRequest): Promise<SoftwareModelTrainResponse> {
    const { data } = await apiClient.post<SoftwareModelTrainResponse>(
      '/analytics/departments/software/models/train',
      {
        model_name: 'random_forest',
        test_period_count: 12,
        ...payload,
      }
    )
    return data
  },

  async getLatestSoftwarePrediction(params: {
    upload_id: number
    employee_id: number
    target_column?: string
    use_llm_narrative?: boolean
  }): Promise<SoftwarePredictionResponse> {
    const { data } = await apiClient.get<SoftwarePredictionResponse>(
      '/analytics/departments/software/predictions/latest',
      { params }
    )
    return data
  },

  async getBulkSoftwarePredictions(params: {
    upload_id: number
    target_column?: string
    use_llm_narrative?: boolean
    llm_team?: string
  }): Promise<SoftwareBulkPredictionResponse> {
    const { data } = await apiClient.get<SoftwareBulkPredictionResponse>(
      '/analytics/departments/software/predictions/bulk',
      { params }
    )
    return data
  },
}
