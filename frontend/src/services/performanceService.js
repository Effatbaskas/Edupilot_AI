import api from './api'

export const performanceService = {
  getOverview: async () => {
    const response = await api.get('/api/v1/performance/overview')
    return response.data
  },

  getTopics: async () => {
    const response = await api.get('/api/v1/performance/topics')
    return response.data
  },

  getMisconceptions: async () => {
    const response = await api.get('/api/v1/performance/misconceptions')
    return response.data
  },
}
