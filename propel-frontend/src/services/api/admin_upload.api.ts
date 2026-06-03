import { apiClient } from './client'

export const adminUploadApi = {
    async uploadFile(file: File, fileType: string, departmentKey?: string) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('file_type', fileType)
        if (departmentKey) {
            formData.append('department_key', departmentKey)
        }

        const response = await apiClient.post('/admin/uploads/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
        return response.data
    },

    async getUploadHistory() {
        const response = await apiClient.get('/admin/uploads/')
        return response.data
    },

    async getOrgNetwork() {
        const response = await apiClient.get('/admin/uploads/org-network')
        return response.data as {
            nodes: Array<{
                id: number; name: string; employee_count: number
                centrality: number; is_silo: boolean
                internal_count: number; external_count: number
            }>
            edges: Array<{
                source_id: number; target_id: number
                weight: number; strength: string
            }>
            summary: {
                total_interactions: number; cross_dept_interactions: number
                most_central_dept: string | null
                silos: string[]; bridges: string[]
            }
            data_source: string
        }
    },

    async getFlightRisk() {
        const response = await apiClient.get('/admin/uploads/flight-risk')
        return response.data as {
            high_risk_count: number
            medium_risk_count: number
            low_risk_count: number
            employees: Array<{
                employee_code: string
                employee_name: string | null
                department: string
                position: string | null
                team: string | null
                risk_level: 'High' | 'Medium' | 'Low'
                risk_score: number
                performance_score: number
                confidence: number
                top_driver: string | null
                predicted_band: string
            }>
        }
    },

    async downloadTemplate(dept: 'software' | 'sales' = 'software') {
        const response = await apiClient.get(`/admin/uploads/template?dept=${dept}`, {
            responseType: 'blob',
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', dept === 'sales' ? 'satis_kpi_sablon.csv' : 'yazilim_kpi_sablon.csv')
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
    }
}
