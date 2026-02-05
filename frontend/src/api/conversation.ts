import request from './index'
import type { Conversation, Message, PaginatedList } from '@/types'

export const conversationApi = {
  // 获取对话列表
  getList(page = 1, pageSize = 20): Promise<PaginatedList<Conversation>> {
    // 后端使用 skip/limit 分页，需要转换
    const skip = (page - 1) * pageSize
    return request.get('/conversations', { params: { skip, limit: pageSize } })
  },

  // 创建对话
  create(title?: string): Promise<Conversation> {
    return request.post('/conversations', { title })
  },

  // 获取对话详情
  getDetail(id: number): Promise<Conversation> {
    return request.get(`/conversations/${id}`)
  },

  // 更新对话标题
  update(id: number, title: string): Promise<Conversation> {
    return request.put(`/conversations/${id}`, { title })
  },

  // 删除对话
  delete(id: number): Promise<{ message: string }> {
    return request.delete(`/conversations/${id}`)
  },

  // 获取对话消息列表
  getMessages(conversationId: number, skip = 0, limit = 50): Promise<{ items: Message[] }> {
    return request.get(`/conversations/${conversationId}/messages`, { 
      params: { skip, limit } 
    }).then((messages: any) => ({ items: messages }))
  },

  // 导出对话
  export(id: number, format: 'markdown' | 'json' = 'markdown'): Promise<Blob> {
    return request.get(`/conversations/${id}/export`, { 
      params: { format },
      responseType: 'blob'
    })
  }
}
