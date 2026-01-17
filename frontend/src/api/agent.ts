import request from './index'
import type {
  AgentTool,
  ToolCreate,
  ToolUpdate,
  TaskExecuteRequest,
  ExecutionResponse,
  ExecutionListItem,
  PaginatedList
} from '@/types'

export const agentApi = {
  // 工具管理
  getTools(params?: { skip?: number, limit?: number, tool_type?: string, is_enabled?: boolean }): Promise<PaginatedList<AgentTool>> {
    return request.get('/agent/tools', { params })
  },

  getTool(id: number): Promise<AgentTool> {
    return request.get(`/agent/tools/${id}`)
  },

  createTool(data: ToolCreate): Promise<AgentTool> {
    return request.post('/agent/tools', data)
  },

  updateTool(id: number, data: ToolUpdate): Promise<AgentTool> {
    return request.put(`/agent/tools/${id}`, data)
  },

  deleteTool(id: number): Promise<{ message: string }> {
    return request.delete(`/agent/tools/${id}`)
  },

  // 任务执行
  executeTask(data: TaskExecuteRequest): Promise<ExecutionResponse> {
    return request.post('/agent/execute', data)
  },

  // 流式执行任务
  streamExecuteTask(
    data: TaskExecuteRequest, 
    onMessage: (event: any) => void, 
    onError?: (error: any) => void,
    onComplete?: () => void
  ): () => void {
    const controller = new AbortController()
    
    fetch(`${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/agent/execute/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(data),
      signal: controller.signal
    }).then(async response => {
      // 检查响应状态
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
        throw new Error(errorData.detail || `请求失败: ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('无法读取响应流')
      }
      
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const text = decoder.decode(value, { stream: true })
          const lines = text.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') {
                onComplete?.()
                return
              }
              try {
                const event = JSON.parse(data)
                onMessage(event)
              } catch {
                // 忽略解析错误
              }
            }
          }
        }
        onComplete?.()
      } finally {
        reader.releaseLock()
      }
    }).catch(error => {
      if (error.name !== 'AbortError') {
        onError?.(error)
      }
    })
    
    return () => controller.abort()
  },

  // 执行历史
  getExecutions(params?: { skip?: number, limit?: number, status?: string }): Promise<PaginatedList<ExecutionListItem>> {
    return request.get('/agent/executions', { params })
  },

  getExecution(id: number): Promise<ExecutionResponse> {
    return request.get(`/agent/executions/${id}`)
  }
}
