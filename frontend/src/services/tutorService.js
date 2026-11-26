import api from './api'

export const tutorService = {
  sendMessage: async (question, sessionId, language = 'auto') => {
    const response = await api.post('/api/v1/tutor/chat', {
      question,
      session_id: sessionId,
      language,
    })
    return response.data
  },

  getChatHistory: async (sessionId) => {
    const params = sessionId ? { session_id: sessionId } : {}
    const response = await api.get('/api/v1/tutor/history', { params })
    return response.data
  },

  getSessions: async () => {
    const response = await api.get('/api/v1/tutor/sessions')
    return response.data
  },
}
