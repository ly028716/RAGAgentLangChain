import request from './index'
import type { LoginRequest, RegisterRequest, TokenResponse, UserInfo } from '@/types'

export const authApi = {
  // 用户登录
  login(data: LoginRequest): Promise<TokenResponse> {
    return request.post('/auth/login', data)
  },

  // 用户注册
  register(data: RegisterRequest): Promise<UserInfo> {
    return request.post('/auth/register', data)
  },

  // 刷新Token
  refreshToken(refreshToken: string): Promise<TokenResponse> {
    return request.post('/auth/refresh', { refresh_token: refreshToken })
  },

  // 修改密码
  changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
    return request.put('/auth/password', { 
      old_password: oldPassword, 
      new_password: newPassword 
    })
  },

  // 获取当前用户信息
  getCurrentUser(): Promise<UserInfo> {
    return request.get('/auth/profile')
  }
}
