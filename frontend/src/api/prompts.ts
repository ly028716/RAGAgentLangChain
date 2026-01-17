import request from './index'
import type {
  SystemPrompt,
  SystemPromptCreate,
  SystemPromptUpdate,
  PaginatedList
} from '@/types'

export const promptsApi = {
  // 获取提示词列表
  getList(skip = 0, limit = 20, category?: string): Promise<PaginatedList<SystemPrompt>> {
    return request.get('/prompts', { params: { skip, limit, category } })
  },

  // 获取提示词详情
  getById(id: number): Promise<SystemPrompt> {
    return request.get(`/prompts/${id}`)
  },

  // 创建提示词
  create(data: SystemPromptCreate): Promise<SystemPrompt> {
    return request.post('/prompts', data)
  },

  // 更新提示词
  update(id: number, data: SystemPromptUpdate): Promise<SystemPrompt> {
    return request.put(`/prompts/${id}`, data)
  },

  // 删除提示词
  delete(id: number): Promise<void> {
    return request.delete(`/prompts/${id}`)
  },

  // 设为默认提示词
  setDefault(id: number): Promise<{ success: boolean; message: string }> {
    return request.put(`/prompts/${id}/default`)
  }
}
