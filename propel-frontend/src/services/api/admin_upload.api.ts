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
    }
}
