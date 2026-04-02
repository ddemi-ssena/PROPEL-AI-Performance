import { apiClient } from './client'

export type KPIUnit = 'numeric' | 'percentage' | 'currency' | 'hours'

export interface KPIDepartment {
  id: number
  name: string
}

export interface KPIResponse {
  id: number
  name: string
  description?: string | null
  unit: KPIUnit
  department_id?: number | null
  target_value?: number | null
  department?: KPIDepartment | null
  created_at: string
  updated_at: string
}

export interface KPIRecordEmployee {
  id: number
  position?: string | null
  user_id: number
}

export interface KPIRecordDetailResponse {
  id: number
  kpi_id: number
  employee_id: number
  value: number
  period_date: string
  created_at: string
  updated_at: string
  kpi: KPIResponse
  employee: KPIRecordEmployee
}

export const kpiApi = {
  async getDepartmentKpis(departmentId: number): Promise<KPIResponse[]> {
    const { data } = await apiClient.get<KPIResponse[]>(`/kpis/department/${departmentId}`)
    return data
  },

  async getAllVisibleRecords(): Promise<KPIRecordDetailResponse[]> {
    const { data } = await apiClient.get<KPIRecordDetailResponse[]>('/kpis/records')
    return data
  },

  async getEmployeeRecords(employeeId: number): Promise<KPIRecordDetailResponse[]> {
    const { data } = await apiClient.get<KPIRecordDetailResponse[]>(`/kpis/records/employee/${employeeId}`)
    return data
  },
}
