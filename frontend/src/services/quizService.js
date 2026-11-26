import api from './api'

export const quizService = {
  generateQuiz: async (params) => {
    const response = await api.post('/api/v1/quiz/generate', params)
    return response.data
  },

  getQuizzes: async () => {
    const response = await api.get('/api/v1/quiz/')
    return response.data
  },

  getHistory: async () => {
    const response = await api.get('/api/v1/quiz/history')
    return response.data
  },

  getQuiz: async (id) => {
    const response = await api.get(`/api/v1/quiz/${id}`)
    return response.data
  },

  submitQuiz: async (id, answers) => {
    const response = await api.post(`/api/v1/quiz/${id}/submit`, { answers })
    return response.data
  },
}
