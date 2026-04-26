import { apiClient } from './client'

export const dashboardApi = {
  getInsights: async () => {
    const response = await apiClient.get('/surveys/analytics/insights')
    return response.data
  }
}
