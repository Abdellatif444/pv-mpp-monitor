import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const apiToken = import.meta.env.VITE_API_TOKEN || ''

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach Bearer token for write requests only
api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (['post', 'put', 'patch', 'delete'].includes(method) && apiToken) {
    config.headers = config.headers || {}
    ;(config.headers as any)['Authorization'] = `Bearer ${apiToken}`
  }
  return config
})

export const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live'
