import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { storage } from '@/utils/storage'
import router from '@/router'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// Token 刷新状态管理（防止竞态条件）
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

const instance: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error) => {
    const { response, config } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          // Token过期，尝试刷新（处理竞态条件）
          const refreshToken = storage.getRefreshToken()
          if (refreshToken && !config._retry) {
            config._retry = true
            
            if (!isRefreshing) {
              isRefreshing = true
              try {
                // 使用 authApi.refreshToken 而不是硬编码 URL
                const { access_token, refresh_token: newRefreshToken } = await import('@/api/auth').then(m => m.authApi.refreshToken(refreshToken))
                storage.setToken(access_token)
                storage.setRefreshToken(newRefreshToken)
                onTokenRefreshed(access_token)
                config.headers.Authorization = `Bearer ${access_token}`
                return instance(config)
              } catch {
                storage.clearAuth()
                router.push('/login')
                return Promise.reject(error)
              } finally {
                isRefreshing = false
              }
            } else {
              // 等待 Token 刷新完成
              return new Promise(resolve => {
                subscribeTokenRefresh(token => {
                  config.headers.Authorization = `Bearer ${token}`
                  resolve(instance(config))
                })
              })
            }
          } else {
            storage.clearAuth()
            router.push('/login')
          }
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 423:
          ElMessage.error(response.data?.detail || '账户已被锁定')
          break
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(response.data?.detail || response.data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    
    return Promise.reject(error)
  }
)

export default instance
