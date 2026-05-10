import { apiClient } from './client'

export interface TeamReportSharePayload {
  team: string
  report_title: string
  summary: string
  include_admins: boolean
  include_department_managers: boolean
  include_team_leads: boolean
}

export interface TeamReportShareResponse {
  team: string
  notification_count: number
  recipients: Array<Record<string, any>>
}

export const notificationsApi = {
  async shareTeamReport(payload: TeamReportSharePayload): Promise<TeamReportShareResponse> {
    const { data } = await apiClient.post<TeamReportShareResponse>('/notifications/team-report', payload)
    return data
  },
}
