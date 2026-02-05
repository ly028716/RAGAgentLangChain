/**
 * Agent页面组件测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AgentView from '@/views/agent/AgentView.vue'
import { useAgentStore } from '@/stores/agent'

// Mock Element Plus组件
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('AgentView Component', () => {
  let wrapper: any
  let agentStore: any

  beforeEach(() => {
    setActivePinia(createPinia())
    agentStore = useAgentStore()

    wrapper = mount(AgentView, {
      global: {
        stubs: {
          'el-button': true,
          'el-input': true,
          'el-switch': true,
          'el-icon': true,
          'el-tag': true,
          'el-alert': true,
          'el-input-number': true
        }
      }
    })
  })

  describe('初始化', () => {
    it('应该正确渲染组件', () => {
      expect(wrapper.exists()).toBe(true)
    })

    it('应该有工具列表侧边栏', () => {
      expect(wrapper.find('.tools-sidebar').exists()).toBe(true)
    })

    it('应该有任务执行主区域', () => {
      expect(wrapper.find('.execution-main').exists()).toBe(true)
    })
  })

  describe('工具列表显示', () => {
    it('应该显示内置工具标题', () => {
      agentStore.tools = [
        {
          id: 1,
          name: 'calculator',
          description: '数学计算工具',
          tool_type: 'builtin',
          is_enabled: true
        }
      ]

      expect(wrapper.text()).toContain('内置工具')
    })

    it('应该显示工具卡片', async () => {
      agentStore.tools = [
        {
          id: 1,
          name: 'calculator',
          description: '数学计算工具',
          tool_type: 'builtin',
          is_enabled: true
        }
      ]

      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('.tool-card').length).toBeGreaterThan(0)
    })

    it('应该显示工具名称和描述', async () => {
      agentStore.tools = [
        {
          id: 1,
          name: 'calculator',
          description: '数学计算工具',
          tool_type: 'builtin',
          is_enabled: true
        }
      ]

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('calculator')
      expect(wrapper.text()).toContain('数学计算工具')
    })

    it('应该显示工具启用/禁用开关', async () => {
      agentStore.tools = [
        {
          id: 1,
          name: 'calculator',
          description: '数学计算工具',
          tool_type: 'builtin',
          is_enabled: true
        }
      ]

      await wrapper.vm.$nextTick()

      expect(wrapper.find('el-switch-stub').exists()).toBe(true)
    })
  })

  describe('空状态显示', () => {
    it('应该在没有工具时显示空状态', async () => {
      agentStore.tools = []

      await wrapper.vm.$nextTick()

      expect(wrapper.find('.empty-tools').exists()).toBe(true)
    })

    it('应该显示初始化提示', async () => {
      agentStore.tools = []

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('系统内置工具未初始化')
    })

    it('应该显示初始化命令', async () => {
      agentStore.tools = []

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('python backend/scripts/seed_data.py')
    })
  })

  describe('任务执行', () => {
    it('应该有任务输入框', () => {
      expect(wrapper.find('el-input-stub[type="textarea"]').exists()).toBe(true)
    })

    it('应该有执行按钮', () => {
      const buttons = wrapper.findAll('el-button-stub')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('应该有最大迭代次数配置', () => {
      expect(wrapper.find('el-input-number-stub').exists()).toBe(true)
    })

    it('输入为空时不能执行', async () => {
      wrapper.vm.taskInput = ''

      await wrapper.vm.$nextTick()

      expect(wrapper.vm.canExecute).toBe(false)
    })

    it('有输入且未执行时可以执行', async () => {
      wrapper.vm.taskInput = '测试任务'
      agentStore.executing = false

      await wrapper.vm.$nextTick()

      expect(wrapper.vm.canExecute).toBe(true)
    })

    it('执行中时不能再次执行', async () => {
      wrapper.vm.taskInput = '测试任务'
      agentStore.executing = true

      await wrapper.vm.$nextTick()

      expect(wrapper.vm.canExecute).toBe(false)
    })
  })

  describe('计算属性', () => {
    it('应该正确过滤内置工具', async () => {
      agentStore.tools = [
        { id: 1, name: 'calculator', tool_type: 'builtin', is_enabled: true },
        { id: 2, name: 'search', tool_type: 'builtin', is_enabled: true },
        { id: 3, name: 'custom', tool_type: 'custom', is_enabled: true }
      ]

      await wrapper.vm.$nextTick()

      expect(wrapper.vm.builtinTools.length).toBe(2)
    })

    it('内置工具应该只包含builtin类型', async () => {
      agentStore.tools = [
        { id: 1, name: 'calculator', tool_type: 'builtin', is_enabled: true },
        { id: 2, name: 'custom', tool_type: 'custom', is_enabled: true }
      ]

      await wrapper.vm.$nextTick()

      const builtinTools = wrapper.vm.builtinTools
      expect(builtinTools.every((t: any) => t.tool_type === 'builtin')).toBe(true)
    })
  })

  describe('功能移除验证', () => {
    it('不应该有创建工具按钮', () => {
      const createButton = wrapper.findAll('el-button-stub').find((btn: any) =>
        btn.text().includes('创建工具')
      )
      expect(createButton).toBeUndefined()
    })

    it('不应该有工具编辑按钮', async () => {
      agentStore.tools = [
        { id: 1, name: 'calculator', tool_type: 'builtin', is_enabled: true }
      ]

      await wrapper.vm.$nextTick()

      const editButton = wrapper.findAll('el-button-stub').find((btn: any) =>
        btn.text().includes('编辑')
      )
      expect(editButton).toBeUndefined()
    })

    it('不应该有工具删除按钮', async () => {
      agentStore.tools = [
        { id: 1, name: 'calculator', tool_type: 'builtin', is_enabled: true }
      ]

      await wrapper.vm.$nextTick()

      const deleteButton = wrapper.findAll('el-button-stub').find((btn: any) =>
        btn.text().includes('删除')
      )
      expect(deleteButton).toBeUndefined()
    })

    it('不应该有工具创建对话框', () => {
      expect(wrapper.find('el-dialog-stub').exists()).toBe(false)
    })
  })
})
