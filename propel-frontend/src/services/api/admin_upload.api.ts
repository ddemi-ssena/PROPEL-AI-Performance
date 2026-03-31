import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1'

export const adminUploadApi = {
    async uploadFile(file: File, fileType: string) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('file_type', fileType)
        
        const token = localStorage.getItem('token')
        const response = await axios.post(`${API_URL}/admin/uploads/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
                'Authorization': `Bearer ${token}`
            }
        })
        return response.data
    },

    async getUploadHistory() {
        const token = localStorage.getItem('token')
        const response = await axios.get(`${API_URL}/admin/uploads/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        return response.data
    }
}
