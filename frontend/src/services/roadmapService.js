import api from './api'

export const roadmapService = {
  getRoadmap: async () => {
    const response = await api.get('/api/v1/roadmap/')
    return response.data
  },

  generateRoadmap: async (params) => {
    const response = await api.post('/api/v1/roadmap/generate', params)
    return response.data
  },

  updateTask: async (taskId, status) => {
    const response = await api.patch(`/api/v1/roadmap/tasks/${taskId}`, { status })
    return response.data
  },
}
