import { apiClient } from './client'

export interface MeetingAttendeePayload {
  dataset_employee_id?: number | null
  db_employee_id?: number | null
  name: string
  role?: string | null
}

export interface TeamMeetingCreatePayload {
  team: string
  title: string
  scheduled_date: string
  scheduled_time: string
  duration_minutes: number
  meeting_url?: string | null
  note?: string | null
  agenda_items: string[]
  attendees: MeetingAttendeePayload[]
}

export interface TeamMeetingCreateResponse {
  id: number
  team: string
  title: string
  scheduled_date: string
  scheduled_time: string
  duration_minutes: number
  meeting_url?: string | null
  attendee_count: number
  notification_count: number
  unresolved_attendee_count: number
}

export const meetingsApi = {
  async createTeamRiskMeeting(payload: TeamMeetingCreatePayload): Promise<TeamMeetingCreateResponse> {
    const { data } = await apiClient.post<TeamMeetingCreateResponse>('/meetings/team-risk', payload)
    return data
  },
}
