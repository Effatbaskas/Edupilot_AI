import api from './api'

export const materialService = {
  uploadMaterial: async (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/api/v1/materials/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    })
    return response.data
  },

  getMaterials: async (search = '') => {
    const response = await api.get('/api/v1/materials/', { params: search ? { search } : {} })
    return response.data
  },

  getMaterial: async (id) => {
    const response = await api.get(`/api/v1/materials/${id}`)
    return response.data
  },

  deleteMaterial: async (id) => {
    const response = await api.delete(`/api/v1/materials/${id}`)
    return response.data
  },
}
