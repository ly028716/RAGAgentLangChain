export const APP_CONSTANTS = {
  UPLOAD: {
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_TYPES: ['.pdf', '.doc', '.docx', '.txt', '.md']
  },
  API: {
    TIMEOUT: 30000,
    BASE_URL: import.meta.env.VITE_API_BASE_URL || '/api/v1'
  }
}

export function parseApiError(error: any, defaultMsg = '操作失败'): string {
  return error.response?.data?.detail || error.message || defaultMsg
}
