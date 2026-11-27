import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || (
  import.meta.env.PROD ? 'https://edupilot-api-3i5i.onrender.com' : ''
)

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor — inject Bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — handle 401 and errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || ''
    const isPublicAuthRequest = /\/auth\/(login|register)(\?|$)/.test(requestUrl)
    if (error.response?.status === 401 && !isPublicAuthRequest) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
