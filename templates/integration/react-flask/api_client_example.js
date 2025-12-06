// Example API client usage for React-Flask integration
import api from '../utils/api'

// Example API calls
export const fetchData = async () => {
  const response = await api.get('/endpoint')
  return response.data
}

export const createData = async (data) => {
  const response = await api.post('/endpoint', data)
  return response.data
}

export const updateData = async (id, data) => {
  const response = await api.put(`/endpoint/${id}`, data)
  return response.data
}

export const deleteData = async (id) => {
  const response = await api.delete(`/endpoint/${id}`)
  return response.data
}

