import axios from 'axios'

const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').trim()

const withoutTrailingSlash = configuredBaseUrl.endsWith('/')
  ? configuredBaseUrl.slice(0, -1)
  : configuredBaseUrl

const apiBaseUrl = !withoutTrailingSlash || withoutTrailingSlash === '/'
  ? '/api'
  : (withoutTrailingSlash.endsWith('/api') ? withoutTrailingSlash : `${withoutTrailingSlash}/api`)

const apiClient = axios.create({
  baseURL: apiBaseUrl,
})

export default apiClient