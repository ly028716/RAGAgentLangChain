import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { promptsApi } from '@/api/prompts'
import type { SystemPrompt, SystemPromptCreate, SystemPromptUpdate } from '@/types'

export const usePromptsStore = defineStore('prompts', () => {
  // State
  const prompts = ref<SystemPrompt[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentPrompt = ref<SystemPrompt | null>(null)

  // Getters
  const systemPrompts = computed(() => prompts.value.filter(p => p.is_system))
  const userPrompts = computed(() => prompts.value.filter(p => !p.is_system))
  const defaultPrompt = computed(() => prompts.value.find(p => p.is_default))
  const hasPrompts = computed(() => prompts.value.length > 0)

  // Actions
  async function fetchPrompts(skip = 0, limit = 50, category?: string) {
    loading.value = true
    error.value = null
    try {
      const res = await promptsApi.getList(skip, limit, category)
      prompts.value = res.items
      total.value = res.total
    } catch (e: any) {
      error.value = e.response?.data?.detail || '加载提示词列表失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchPrompt(id: number) {
    loading.value = true
    error.value = null
    try {
      currentPrompt.value = await promptsApi.getById(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail || '加载提示词详情失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createPrompt(data: SystemPromptCreate) {
    const prompt = await promptsApi.create(data)
    prompts.value.unshift(prompt)
    total.value++
    return prompt
  }

  async function updatePrompt(id: number, data: SystemPromptUpdate) {
    const prompt = await promptsApi.update(id, data)
    const index = prompts.value.findIndex(p => p.id === id)
    if (index !== -1) {
      prompts.value[index] = prompt
    }
    if (currentPrompt.value?.id === id) {
      currentPrompt.value = prompt
    }
    return prompt
  }

  async function deletePrompt(id: number) {
    await promptsApi.delete(id)
    prompts.value = prompts.value.filter(p => p.id !== id)
    total.value--
    if (currentPrompt.value?.id === id) {
      currentPrompt.value = null
    }
  }

  async function setDefaultPrompt(id: number) {
    await promptsApi.setDefault(id)
    // 更新本地状态
    prompts.value.forEach(p => {
      p.is_default = p.id === id
    })
  }

  function clearError() {
    error.value = null
  }

  return {
    prompts,
    total,
    loading,
    error,
    currentPrompt,
    systemPrompts,
    userPrompts,
    defaultPrompt,
    hasPrompts,
    fetchPrompts,
    fetchPrompt,
    createPrompt,
    updatePrompt,
    deletePrompt,
    setDefaultPrompt,
    clearError
  }
})
