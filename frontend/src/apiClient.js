import axios from 'axios'

const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').trim()

const apiBaseUrl = configuredBaseUrl.endsWith('/')
  ? configuredBaseUrl.slice(0, -1)
  : configuredBaseUrl

const apiClient = axios.create({
  baseURL: apiBaseUrl,
})

export default apiClient