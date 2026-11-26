import api from './api'

export const adminService = {
  async getUsers() {
    const response = await api.get('/api/v1/admin/users')
    return response.data
  },
  async updateUserRole(userId, role) {
    const response = await api.put(`/api/v1/admin/users/${userId}/role`, { role })
    return response.data
  },
}
