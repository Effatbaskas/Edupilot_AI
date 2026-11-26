import api from './api'

export const authService = {
  login: async (email, password) => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const response = await api.post('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  register: async (data) => {
    const response = await api.post('/api/v1/auth/register', data)
    return response.data
  },

  getMe: async () => {
    const response = await api.get('/api/v1/auth/me')
    return response.data
  },
}
