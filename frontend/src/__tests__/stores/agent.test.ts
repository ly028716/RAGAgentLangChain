/**
 * Agent Store 测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAgentStore } from '@/stores/agent'
import { agentApi } from '@/api/agent'
import type { AgentTool, ExecutionResponse, ExecutionListItem, PaginatedList } from '@/types'

// Mock API
vi.mock('@/api/agent', () => ({
  agentApi: {
    getTools: vi.fn(),
    createTool: vi.fn(),
    updateTool: vi.fn(),
    deleteTool: vi.fn(),
    executeTask: vi.fn(),
    streamExecuteTask: vi.fn(),
    getExecutions: vi.fn(),
    getExecution: vi.fn()
  }
}))

// 创建完整的 mock 数据
const createMockTool = (overrides: Partial<AgentTool> = {}): AgentTool => ({
  id: 1,
  name: 'test_tool',
  description: '测试工具',
  tool_type: 'builtin',
  is_enabled: true,
  created_at: '2025-01-01T00:00:00Z',
  ...overrides
})

const createMockExecution = (overrides: Partial<ExecutionResponse> = {}): ExecutionResponse => ({
  execution_id: 1,
  task: '测试任务',
  result: '执行结果',
  steps: [],
  status: 'completed',
  created_at: '2025-01-01T00:00:00Z',
  ...overrides
})

const createMockExecutionListItem = (overrides: Partial<ExecutionListItem> = {}): ExecutionListItem => ({
  execution_id: 1,
  task: '测试任务',
  result: '执行结果',
  status: 'completed',
  step_count: 3,
  created_at: '2025-01-01T00:00:00Z',
  ...overrides
})

describe('Agent Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useAgentStore()
      
      expect(store.tools).toEqual([])
      expect(store.toolsTotal).toBe(0)
      expect(store.executions).toEqual([])
      expect(store.executionsTotal).toBe(0)
      expect(store.currentExecution).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.executing).toBe(false)
      expect(store.streamingSteps).toEqual([])
      expect(store.streamingResult).toBe('')
    })
  })

  describe('计算属性', () => {
    it('enabledTools 应该只返回启用的工具', () => {
      const store = useAgentStore()
      store.tools = [
        createMockTool({ id: 1, name: 'tool1', is_enabled: true, tool_type: 'builtin' }),
        createMockTool({ id: 2, name: 'tool2', is_enabled: false, tool_type: 'builtin' }),
        createMockTool({ id: 3, name: 'tool3', is_enabled: true, tool_type: 'custom' })
      ]

      expect(store.enabledTools.length).toBe(2)
      expect(store.enabledTools.every(t => t.is_enabled)).toBe(true)
    })

    it('builtinTools 应该只返回内置工具', () => {
      const store = useAgentStore()
      store.tools = [
        createMockTool({ id: 1, name: 'tool1', tool_type: 'builtin' }),
        createMockTool({ id: 2, name: 'tool2', tool_type: 'custom' })
      ]

      expect(store.builtinTools.length).toBe(1)
      expect(store.builtinTools[0].tool_type).toBe('builtin')
    })

    it('customTools 应该只返回自定义工具', () => {
      const store = useAgentStore()
      store.tools = [
        createMockTool({ id: 1, name: 'tool1', tool_type: 'builtin' }),
        createMockTool({ id: 2, name: 'tool2', tool_type: 'custom' })
      ]

      expect(store.customTools.length).toBe(1)
      expect(store.customTools[0].tool_type).toBe('custom')
    })
  })

  describe('fetchTools', () => {
    it('应该成功获取工具列表', async () => {
      const mockData: PaginatedList<AgentTool> = {
        items: [createMockTool({ id: 1, name: 'search', description: '搜索工具' })],
        total: 1
      }
      vi.mocked(agentApi.getTools).mockResolvedValue(mockData)

      const store = useAgentStore()
      await store.fetchTools()

      expect(store.tools).toEqual(mockData.items)
      expect(store.toolsTotal).toBe(1)
      expect(store.loading).toBe(false)
    })

    it('应该支持过滤参数', async () => {
      vi.mocked(agentApi.getTools).mockResolvedValue({ items: [], total: 0 })

      const store = useAgentStore()
      await store.fetchTools({ tool_type: 'custom', is_enabled: true })

      expect(agentApi.getTools).toHaveBeenCalledWith({ tool_type: 'custom', is_enabled: true })
    })

    it('应该在加载时设置 loading 状态', async () => {
      vi.mocked(agentApi.getTools).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ items: [], total: 0 }), 100))
      )

      const store = useAgentStore()
      const promise = store.fetchTools()
      
      expect(store.loading).toBe(true)
      await promise
      expect(store.loading).toBe(false)
    })
  })

  describe('createTool', () => {
    it('应该成功创建工具', async () => {
      const newTool = createMockTool({ 
        id: 1, 
        name: 'new_tool', 
        description: '新工具', 
        tool_type: 'custom',
        config: {}
      })
      vi.mocked(agentApi.createTool).mockResolvedValue(newTool)

      const store = useAgentStore()
      const result = await store.createTool({ 
        name: 'new_tool', 
        description: '新工具',
        config: {}
      })

      expect(result).toEqual(newTool)
      expect(store.tools[0]).toEqual(newTool)
      expect(store.toolsTotal).toBe(1)
    })
  })

  describe('updateTool', () => {
    it('应该成功更新工具', async () => {
      const store = useAgentStore()
      store.tools = [createMockTool({ id: 1, name: 'old_name', tool_type: 'custom' })]
      
      const updatedTool = createMockTool({ id: 1, name: 'new_name', description: '新描述', tool_type: 'custom' })
      vi.mocked(agentApi.updateTool).mockResolvedValue(updatedTool)

      const result = await store.updateTool(1, { name: 'new_name', description: '新描述' })

      expect(result).toEqual(updatedTool)
      expect(store.tools[0].name).toBe('new_name')
    })
  })

  describe('deleteTool', () => {
    it('应该成功删除工具', async () => {
      const store = useAgentStore()
      store.tools = [
        createMockTool({ id: 1, name: 'tool1', tool_type: 'custom' }),
        createMockTool({ id: 2, name: 'tool2', tool_type: 'custom' })
      ]
      store.toolsTotal = 2
      
      vi.mocked(agentApi.deleteTool).mockResolvedValue({ message: '删除成功' })

      await store.deleteTool(1)

      expect(store.tools.length).toBe(1)
      expect(store.tools[0].id).toBe(2)
      expect(store.toolsTotal).toBe(1)
    })
  })

  describe('toggleTool', () => {
    it('应该切换工具启用状态', async () => {
      const store = useAgentStore()
      store.tools = [createMockTool({ id: 1, name: 'tool1', tool_type: 'custom', is_enabled: true })]
      
      const updatedTool = createMockTool({ id: 1, name: 'tool1', tool_type: 'custom', is_enabled: false })
      vi.mocked(agentApi.updateTool).mockResolvedValue(updatedTool)

      await store.toggleTool(1, false)

      expect(agentApi.updateTool).toHaveBeenCalledWith(1, { is_enabled: false })
    })
  })

  describe('executeTask', () => {
    it('应该成功执行任务', async () => {
      const mockResult = createMockExecution({
        execution_id: 1,
        task: '测试任务',
        status: 'completed',
        result: '执行结果'
      })
      vi.mocked(agentApi.executeTask).mockResolvedValue(mockResult)

      const store = useAgentStore()
      const result = await store.executeTask('测试任务')

      expect(result).toEqual(mockResult)
      expect(store.currentExecution).toEqual(mockResult)
      expect(store.executing).toBe(false)
    })

    it('应该在执行时设置 executing 状态', async () => {
      vi.mocked(agentApi.executeTask).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(createMockExecution()), 100))
      )

      const store = useAgentStore()
      const promise = store.executeTask('测试任务')
      
      expect(store.executing).toBe(true)
      await promise
      expect(store.executing).toBe(false)
    })

    it('应该清除之前的流式状态', async () => {
      const store = useAgentStore()
      store.streamingSteps = [{ step_number: 1, thought: '', action: 'test', action_input: {}, observation: 'ok' }]
      store.streamingResult = '之前的结果'
      
      vi.mocked(agentApi.executeTask).mockResolvedValue(createMockExecution())

      await store.executeTask('新任务')

      expect(store.streamingSteps).toEqual([])
      expect(store.streamingResult).toBe('')
    })
  })

  describe('streamExecuteTask', () => {
    it('应该调用流式执行 API', () => {
      const mockCancel = vi.fn()
      vi.mocked(agentApi.streamExecuteTask).mockReturnValue(mockCancel)

      const store = useAgentStore()
      const cancel = store.streamExecuteTask('测试任务')

      expect(agentApi.streamExecuteTask).toHaveBeenCalled()
      expect(store.executing).toBe(true)
      expect(cancel).toBe(mockCancel)
    })

    it('应该处理步骤事件', () => {
      let onEventCallback: ((event: any) => void) | undefined
      vi.mocked(agentApi.streamExecuteTask).mockImplementation((_, onEvent) => {
        onEventCallback = onEvent
        return vi.fn()
      })

      const store = useAgentStore()
      store.streamExecuteTask('测试任务')

      // 模拟步骤事件
      onEventCallback!({ type: 'step', data: { step_number: 1, thought: '', action: 'search', action_input: {}, observation: 'found' } })

      expect(store.streamingSteps.length).toBe(1)
      expect(store.streamingSteps[0].action).toBe('search')
    })

    it('应该处理结果事件', () => {
      let onEventCallback: ((event: any) => void) | undefined
      vi.mocked(agentApi.streamExecuteTask).mockImplementation((_, onEvent) => {
        onEventCallback = onEvent
        return vi.fn()
      })

      const store = useAgentStore()
      store.streamExecuteTask('测试任务')

      // 模拟结果事件
      onEventCallback!({ type: 'result', data: { result: '最终结果' } })

      expect(store.streamingResult).toBe('最终结果')
    })

    it('应该处理错误事件', () => {
      let onEventCallback: ((event: any) => void) | undefined
      vi.mocked(agentApi.streamExecuteTask).mockImplementation((_, onEvent) => {
        onEventCallback = onEvent
        return vi.fn()
      })

      const store = useAgentStore()
      store.streamExecuteTask('测试任务')

      // 模拟错误事件
      onEventCallback!({ type: 'error', data: { message: '执行失败' } })

      expect(store.executing).toBe(false)
    })

    it('应该处理完成回调', () => {
      let onCompleteCallback: (() => void) | undefined
      vi.mocked(agentApi.streamExecuteTask).mockImplementation((_, _onEvent, _onError, onComplete) => {
        onCompleteCallback = onComplete
        return vi.fn()
      })

      const store = useAgentStore()
      store.streamExecuteTask('测试任务')

      // 模拟完成
      if (onCompleteCallback) {
        onCompleteCallback()
      }

      expect(store.executing).toBe(false)
    })
  })

  describe('fetchExecutions', () => {
    it('应该成功获取执行历史', async () => {
      const mockData: PaginatedList<ExecutionListItem> = {
        items: [createMockExecutionListItem({ execution_id: 1, task: '任务1', status: 'completed' })],
        total: 1
      }
      vi.mocked(agentApi.getExecutions).mockResolvedValue(mockData)

      const store = useAgentStore()
      await store.fetchExecutions()

      expect(store.executions).toEqual(mockData.items)
      expect(store.executionsTotal).toBe(1)
    })
  })

  describe('fetchExecution', () => {
    it('应该成功获取执行详情', async () => {
      const mockExecution = createMockExecution({
        execution_id: 1,
        task: '测试任务',
        status: 'completed',
        result: '结果'
      })
      vi.mocked(agentApi.getExecution).mockResolvedValue(mockExecution)

      const store = useAgentStore()
      await store.fetchExecution(1)

      expect(store.currentExecution).toEqual(mockExecution)
    })
  })

  describe('clearCurrentExecution', () => {
    it('应该清除当前执行状态', () => {
      const store = useAgentStore()
      store.currentExecution = createMockExecution()
      store.streamingSteps = [{ step_number: 1, thought: '', action: '', action_input: {}, observation: '' }]
      store.streamingResult = '结果'

      store.clearCurrentExecution()

      expect(store.currentExecution).toBeNull()
      expect(store.streamingSteps).toEqual([])
      expect(store.streamingResult).toBe('')
    })
  })
})
