import { apiClient } from './client'

export const employeeApi = {
  submitWeeklyPulse: async (data: any) => {
    const response = await apiClient.post('/surveys/weekly-pulse', data)
    return response.data
  },
  getEmployees: async () => {
    const response = await apiClient.get('/employees/')
    return response.data
  },
  getDepartments: async () => {
    const response = await apiClient.get('/departments/')
    return response.data
  }
}
