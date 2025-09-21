import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const apiToken = import.meta.env.VITE_API_TOKEN || ''

export const api = axios.create({ baseURL })

// Attach headers dynamically: Authorization and Content-Type
api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  const isFormData = typeof FormData !== 'undefined' && (config.data instanceof FormData)

  // Set Content-Type only when NOT sending FormData
  if (!isFormData && ['post', 'put', 'patch'].includes(method)) {
    config.headers = config.headers || {}
    ;(config.headers as any)['Content-Type'] = 'application/json'
  } else if (isFormData) {
    // Let the browser set the correct multipart boundary
    if (config.headers) {
      delete (config.headers as any)['Content-Type']
    }
  }

  if (['post', 'put', 'patch', 'delete'].includes(method) && apiToken) {
    config.headers = config.headers || {}
    ;(config.headers as any)['Authorization'] = `Bearer ${apiToken}`
  }
  return config
})

export const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live'
