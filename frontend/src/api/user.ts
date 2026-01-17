import request from './index'
import type { UserInfo, AvatarUploadResponse } from '@/types'

// 账号注销相关类型
export interface DeletionRequestData {
  password: string
  reason?: string
}

export interface DeletionRequestResponse {
  success: boolean
  message: string
  requested_at?: string
  scheduled_at?: string
  cooldown_days?: number
}

export interface DeletionCancelResponse {
  success: boolean
  message: string
}

export interface DeletionStatusResponse {
  has_deletion_request: boolean
  requested_at?: string
  scheduled_at?: string
  reason?: string
  remaining_days?: number
  remaining_hours?: number
  can_cancel?: boolean
  message: string
}

export const userApi = {
  // 获取当前用户信息
  getProfile(): Promise<UserInfo> {
    return request.get('/user/profile')
  },

  // 更新用户信息
  updateProfile(data: { nickname?: string; email?: string }): Promise<UserInfo> {
    return request.put('/user/profile', data)
  },

  // 上传头像
  uploadAvatar(file: File): Promise<AvatarUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/user/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 删除头像
  deleteAvatar(): Promise<{ success: boolean; message: string }> {
    return request.delete('/user/avatar')
  },

  // 获取用户头像URL
  getAvatarUrl(userId: number): string {
    return `/api/v1/user/avatar/${userId}`
  },

  // ==================== 账号注销相关API ====================

  // 请求注销账号
  requestDeletion(data: DeletionRequestData): Promise<DeletionRequestResponse> {
    return request.post('/user/deletion/request', data)
  },

  // 取消注销请求
  cancelDeletion(): Promise<DeletionCancelResponse> {
    return request.post('/user/deletion/cancel')
  },

  // 查询注销状态
  getDeletionStatus(): Promise<DeletionStatusResponse> {
    return request.get('/user/deletion/status')
  }
}
