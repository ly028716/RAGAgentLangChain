import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { knowledgeApi } from '@/api/knowledge'
import type { KnowledgeBase, Document, KnowledgeBaseCreate, KnowledgeBaseUpdate } from '@/types'

export const useKnowledgeStore = defineStore('knowledge', () => {
  // State
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const currentKnowledgeBase = ref<KnowledgeBase | null>(null)
  const documents = ref<Document[]>([])
  const total = ref(0)
  const documentsTotal = ref(0)
  const loading = ref(false)
  const documentsLoading = ref(false)
  const error = ref<string | null>(null)
  const documentsError = ref<string | null>(null)

  // Getters
  const hasKnowledgeBases = computed(() => knowledgeBases.value.length > 0)
  const hasError = computed(() => error.value !== null)

  // Actions
  async function fetchKnowledgeBases(skip = 0, limit = 20) {
    loading.value = true
    error.value = null
    try {
      const res = await knowledgeApi.getList(skip, limit)
      knowledgeBases.value = res.items
      total.value = res.total
    } catch (e: any) {
      error.value = e.response?.data?.detail || '加载知识库列表失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchKnowledgeBase(id: number) {
    loading.value = true
    error.value = null
    try {
      currentKnowledgeBase.value = await knowledgeApi.getById(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail || '加载知识库详情失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createKnowledgeBase(data: KnowledgeBaseCreate) {
    const kb = await knowledgeApi.create(data)
    knowledgeBases.value.unshift(kb)
    total.value++
    return kb
  }

  async function updateKnowledgeBase(id: number, data: KnowledgeBaseUpdate) {
    const kb = await knowledgeApi.update(id, data)
    const index = knowledgeBases.value.findIndex(k => k.id === id)
    if (index !== -1) {
      knowledgeBases.value[index] = kb
    }
    if (currentKnowledgeBase.value?.id === id) {
      currentKnowledgeBase.value = kb
    }
    return kb
  }

  async function deleteKnowledgeBase(id: number) {
    await knowledgeApi.delete(id)
    knowledgeBases.value = knowledgeBases.value.filter(k => k.id !== id)
    total.value--
    if (currentKnowledgeBase.value?.id === id) {
      currentKnowledgeBase.value = null
    }
  }

  async function fetchDocuments(kbId: number, skip = 0, limit = 20) {
    documentsLoading.value = true
    documentsError.value = null
    try {
      const res = await knowledgeApi.getDocuments(kbId, skip, limit)
      documents.value = res.items
      documentsTotal.value = res.total
    } catch (e: any) {
      documentsError.value = e.response?.data?.detail || '加载文档列表失败'
      throw e
    } finally {
      documentsLoading.value = false
    }
  }

  async function uploadDocument(kbId: number, file: File) {
    const doc = await knowledgeApi.uploadDocument(kbId, file)
    // 刷新文档列表
    await fetchDocuments(kbId)
    // 更新知识库文档数量
    const kb = knowledgeBases.value.find(k => k.id === kbId)
    if (kb) {
      kb.document_count++
    }
    if (currentKnowledgeBase.value?.id === kbId) {
      currentKnowledgeBase.value.document_count++
    }
    return doc
  }

  async function uploadDocuments(kbId: number, files: File[]) {
    const result = await knowledgeApi.uploadDocuments(kbId, files)
    // 刷新文档列表
    await fetchDocuments(kbId)
    // 更新知识库文档数量
    const successCount = result.documents.length
    const kb = knowledgeBases.value.find(k => k.id === kbId)
    if (kb) {
      kb.document_count += successCount
    }
    if (currentKnowledgeBase.value?.id === kbId) {
      currentKnowledgeBase.value.document_count += successCount
    }
    return result
  }

  async function deleteDocument(docId: number, kbId: number) {
    await knowledgeApi.deleteDocument(docId)
    documents.value = documents.value.filter(d => d.id !== docId)
    documentsTotal.value--
    // 更新知识库文档数量
    const kb = knowledgeBases.value.find(k => k.id === kbId)
    if (kb) {
      kb.document_count--
    }
    if (currentKnowledgeBase.value?.id === kbId) {
      currentKnowledgeBase.value.document_count--
    }
  }

  function clearCurrentKnowledgeBase() {
    currentKnowledgeBase.value = null
    documents.value = []
    documentsTotal.value = 0
    documentsError.value = null
  }

  function clearError() {
    error.value = null
    documentsError.value = null
  }

  return {
    knowledgeBases,
    currentKnowledgeBase,
    documents,
    total,
    documentsTotal,
    loading,
    documentsLoading,
    error,
    documentsError,
    hasKnowledgeBases,
    hasError,
    fetchKnowledgeBases,
    fetchKnowledgeBase,
    createKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
    fetchDocuments,
    uploadDocument,
    uploadDocuments,
    deleteDocument,
    clearCurrentKnowledgeBase,
    clearError
  }
})
