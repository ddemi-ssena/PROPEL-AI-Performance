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

export interface PerformanceStrengthResponse {
  label: string
  tooltip: string
}

export interface PerformanceEmployeeRowResponse {
  employee_id: number
  employee_name: string
  external_employee_code?: string | null
  department_id: number
  department_name: string
  team?: string | null
  position?: string | null
  experience_years?: number | null
  role_level: 'junior' | 'mid' | 'senior' | 'lead' | string
  kpi_score?: number | null
  trend?: number | null
  sparkline_values: number[]
  strength?: PerformanceStrengthResponse | null
  status: 'stable' | 'watch' | 'risk' | 'no_data' | string
  latest_period?: string | null
  record_count: number
  has_kpi_data: boolean
}

export interface PerformanceTeamSummaryResponse {
  team: string
  employee_count: number
  analyzed_count: number
  average_kpi?: number | null
  average_trend?: number | null
  declining_count: number
  top_performer_count: number
}

export interface PerformanceRoleSummaryResponse {
  role_level: 'junior' | 'mid' | 'senior' | 'lead' | string
  label: string
  employee_count: number
  analyzed_count: number
  average_kpi?: number | null
  average_trend?: number | null
  highest_employee_name?: string | null
  highest_kpi?: number | null
  lowest_employee_name?: string | null
  lowest_kpi?: number | null
}

export interface PerformanceKpiSummaryResponse {
  total_employees: number
  analyzed_employees: number
  team_count: number
  average_kpi?: number | null
  average_trend?: number | null
  top_performer_count: number
  declining_count: number
  junior_average?: number | null
  junior_count: number
  senior_average?: number | null
  senior_count: number
}

export interface PerformanceInsightResponse {
  title: string
  icon: string
  text: string
  tone: string
}

export interface PerformanceActionGroupResponse {
  title: string
  items: string[]
}

export interface DepartmentPerformanceSummaryResponse {
  scope_department_id?: number | null
  scope_team?: string | null
  latest_period?: string | null
  summary: PerformanceKpiSummaryResponse
  employees: PerformanceEmployeeRowResponse[]
  teams: PerformanceTeamSummaryResponse[]
  roles: PerformanceRoleSummaryResponse[]
  insights: PerformanceInsightResponse[]
  risk_people: PerformanceEmployeeRowResponse[]
  success_people: PerformanceEmployeeRowResponse[]
  action_groups: PerformanceActionGroupResponse[]
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
  generated_at?: string
  department_narrative?: Record<string, any> | null
  team_narratives: Array<Record<string, any>>
  team_analytics?: Array<Record<string, any>>
  items: SoftwarePredictionResponse[]
}

export interface SoftwareEmployeeKPIMetricResponse {
  code: string
  label: string
  value: string
  raw_value?: number | null
  unit: string
  status: string
  tone: 'good' | 'warn' | 'bad' | string
  bar_pct: number
  hint: string
  category: string
}

export interface SoftwareEmployeePerformanceResponse {
  department: string
  upload_id: number
  file_name: string
  employee_id: number
  employee_name?: string | null
  team?: string | null
  role?: string | null
  period_label: string
  latest_period?: string | null
  metrics: SoftwareEmployeeKPIMetricResponse[]
  trend_labels: string[]
  trend_values: number[]
  prediction?: SoftwarePredictionResponse | null
}

export interface SoftwareDepartmentInsightsResponse {
  status: string
  department: string
  upload_id?: number | null
  period: string
  insights: string
  generated_at: string
  source: string
  model?: string | null
  fallback_used: boolean
  health_score?: number | null
  sections: Record<string, any>
  actions: Array<Record<string, any>>
}

export interface DepartmentDashboardDepartmentResponse {
  id: number
  name: string
  member_count: number
  team_count: number
  teams: string[]
}

export interface DepartmentDashboardCoverageResponse {
  kpi_employee_count: number
  kpi_percentage: number
  pulse_response_count: number
  pulse_employee_count: number
  pulse_percentage: number
  feedback_response_count: number
  feedback_employee_count: number
  feedback_percentage: number
  confidence_score: number
  last_kpi_update?: string | null
  last_pulse_update?: string | null
  last_feedback_update?: string | null
}

export interface DepartmentDashboardScoresResponse {
  department_health: number
  execution_score: number
  people_health_score: number
  risk_score: number
  confidence_score: number
  weights: Record<string, number>
}

export interface DepartmentDashboardSourceResponse {
  label: string
  score: number
  status: string
  metrics: Record<string, any>
  details: Record<string, any>
}

export interface DepartmentDashboardInsightResponse {
  type: string
  severity: string
  title: string
  description: string
  recommendation: string
  action: string
  team?: string | null
  evidence: string[]
  manager_interpretation?: string | null
  impact?: string | null
  follow_up_metrics: string[]
  source: string
  model?: string | null
  fallback_used: boolean
}

export interface DepartmentDashboardTeamResponse {
  team: string
  member_count: number
  scores: Record<string, number>
  metrics: Record<string, any>
  status: string
  trend: string
}

export interface DepartmentDashboardActionResponse {
  title: string
  description: string
  priority: string
  due_date: string
  owner: string
  source: string
}

export interface DepartmentDashboardActionsResponse {
  urgent: DepartmentDashboardActionResponse[]
  this_week: DepartmentDashboardActionResponse[]
  monitoring: DepartmentDashboardActionResponse[]
}

export interface DepartmentDashboardAISummaryResponse {
  summary: string
  strengths: string[]
  risks: string[]
  recommendations: string[]
  source: string
  model?: string | null
  fallback_used: boolean
}

export interface SoftwareDepartmentDashboardResponse {
  status: string
  department: DepartmentDashboardDepartmentResponse
  period: string
  generated_at: string
  upload_id?: number | null
  coverage: DepartmentDashboardCoverageResponse
  scores: DepartmentDashboardScoresResponse
  sources: Record<string, DepartmentDashboardSourceResponse>
  hybrid_insights: DepartmentDashboardInsightResponse[]
  team_breakdown: DepartmentDashboardTeamResponse[]
  actions: DepartmentDashboardActionsResponse
  ai_summary: DepartmentDashboardAISummaryResponse
}

export interface TeamReportExportPayload {
  team: string
  report_date: string
  report_type: string
  metrics: Array<{ label: string; value: string }>
  main_issue_title: string
  main_issue_description: string
  main_reason: string
  actions: Array<Record<string, any>>
  members: Array<Record<string, any>>
  trend: Array<{ period: string; risk_score: number }>
  risk_factors: Array<Record<string, any>>
  talking_points: string[]
}

// ── Sales Department Types ────────────────────────────────────────────────────

export type SalesTargetColumn =
  | 'Performance_Drop_Target'
  | 'Burnout_Target'
  | 'Resignation_Target'
  | 'High_Risk_Target'

export interface SalesModelTrainRequest {
  upload_id: number
  target_column: SalesTargetColumn
  test_period_count?: number
}

export interface SalesModelStateResponse {
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

export interface SalesModelTrainResponse {
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

export interface SalesPredictionResponse {
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

export interface SalesBulkPredictionResponse {
  department: string
  upload_id: number
  target_column: string
  prediction_count: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  generated_at?: string
  department_narrative?: Record<string, any> | null
  team_narratives: Array<Record<string, any>>
  team_analytics?: Array<Record<string, any>>
  items: SalesPredictionResponse[]
}

export interface SalesKPIMetric {
  code: string
  name: string
  raw_value?: number | null
  unit: string
  direction: string
  threshold_status?: string | null
  trend_signal?: string | null
  bar_pct: number
}

export interface SalesWeeklyTrendPoint {
  label: string
  score: number
}

export interface SalesEmployeePerformanceResponse {
  employee_id: number
  external_code?: string | null
  latest_period?: string | null
  kpis: Record<string, SalesKPIMetric>
  weekly_trend: SalesWeeklyTrendPoint[]
  prediction?: SalesPredictionResponse | null
  has_upload: boolean
  has_model: boolean
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

  async getPerformanceSummary(params?: {
    department_id?: number
    team?: string
  }): Promise<DepartmentPerformanceSummaryResponse> {
    const { data } = await apiClient.get<DepartmentPerformanceSummaryResponse>(
      '/analytics/performance/summary',
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
        model_name: 'stacking_lgbm_xgb_rf_lr',
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

  async getMySoftwarePerformance(): Promise<SoftwareEmployeePerformanceResponse> {
    const { data } = await apiClient.get<SoftwareEmployeePerformanceResponse>(
      '/analytics/departments/software/my-performance'
    )
    return data
  },

  async getSoftwareDepartmentInsights(params?: {
    upload_id?: number
    period?: string
    target_column?: string
    use_llm?: boolean
  }): Promise<SoftwareDepartmentInsightsResponse> {
    const { data } = await apiClient.get<SoftwareDepartmentInsightsResponse>(
      '/analytics/departments/software/insights',
      { params: params || {} }
    )
    return data
  },

  async getSoftwareDepartmentDashboard(params?: {
    upload_id?: number
    period?: 'week' | 'month' | 'quarter' | 'year' | string
    target_column?: string
    use_llm?: boolean
  }): Promise<SoftwareDepartmentDashboardResponse> {
    const { data } = await apiClient.get<SoftwareDepartmentDashboardResponse>(
      '/analytics/departments/software/dashboard',
      { params: params || {} }
    )
    return data
  },

  async exportSoftwareTeamReport(payload: TeamReportExportPayload): Promise<Blob> {
    const { data } = await apiClient.post<Blob>(
      '/analytics/departments/software/team-report/export',
      payload,
      { responseType: 'blob' }
    )
    return data
  },

  // ── Sales Department ────────────────────────────────────────────────────────

  async getSalesDatasets(): Promise<SoftwareDatasetResponse[]> {
    const { data } = await apiClient.get<SoftwareDatasetResponse[]>('/analytics/departments/sales/datasets')
    return data
  },

  async getSalesDatasetEmployees(uploadId: number): Promise<SoftwareDatasetEmployeeResponse[]> {
    const { data } = await apiClient.get<SoftwareDatasetEmployeeResponse[]>(
      `/analytics/departments/sales/datasets/${uploadId}/employees`
    )
    return data
  },

  async getSalesModelState(uploadId: number): Promise<SalesModelStateResponse[]> {
    const { data } = await apiClient.get<SalesModelStateResponse[]>(
      `/analytics/departments/sales/datasets/${uploadId}/model-state`
    )
    return data
  },

  async trainSalesModel(payload: SalesModelTrainRequest): Promise<SalesModelTrainResponse> {
    const { data } = await apiClient.post<SalesModelTrainResponse>(
      '/analytics/departments/sales/models/train',
      { test_period_count: 12, ...payload }
    )
    return data
  },

  async getLatestSalesPrediction(params: {
    upload_id: number
    employee_id: number
    target_column?: string
    use_llm_narrative?: boolean
  }): Promise<SalesPredictionResponse> {
    const { data } = await apiClient.get<SalesPredictionResponse>(
      '/analytics/departments/sales/predictions/latest',
      { params }
    )
    return data
  },

  async getBulkSalesPredictions(params: {
    upload_id: number
    target_column?: string
    use_llm_narrative?: boolean
    llm_team?: string
  }): Promise<SalesBulkPredictionResponse> {
    const { data } = await apiClient.get<SalesBulkPredictionResponse>(
      '/analytics/departments/sales/predictions/bulk',
      { params }
    )
    return data
  },

  async getMyPerformance(): Promise<SalesEmployeePerformanceResponse> {
    const { data } = await apiClient.get<SalesEmployeePerformanceResponse>(
      '/analytics/departments/sales/my-performance'
    )
    return data
  },
}
