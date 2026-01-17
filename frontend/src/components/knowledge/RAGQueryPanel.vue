<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Document } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/knowledge'
import type { KnowledgeBase, RAGQueryResponse, DocumentChunk } from '@/types'

const props = defineProps<{
  knowledgeBases: KnowledgeBase[]
}>()

// 状态
const selectedKbIds = ref<number[]>([])
const question = ref('')
const topK = ref(5)
const loading = ref(false)
const result = ref<RAGQueryResponse | null>(null)

// 计算属性
const canQuery = computed(() => selectedKbIds.value.length > 0 && question.value.trim())

// 方法
async function handleQuery() {
  if (!canQuery.value) {
    ElMessage.warning('请选择知识库并输入问题')
    return
  }

  loading.value = true
  result.value = null

  try {
    result.value = await knowledgeApi.query({
      knowledge_base_ids: selectedKbIds.value,
      question: question.value,
      top_k: topK.value
    })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '查询失败')
  } finally {
    loading.value = false
  }
}

function formatScore(score: number): string {
  return (score * 100).toFixed(1) + '%'
}
</script>

<template>
  <div class="rag-query-panel">
    <div class="query-form">
      <!-- 知识库选择 -->
      <div class="form-item">
        <label>选择知识库</label>
        <el-checkbox-group v-model="selectedKbIds">
          <el-checkbox 
            v-for="kb in knowledgeBases" 
            :key="kb.id" 
            :value="kb.id"
          >
            {{ kb.name }} ({{ kb.document_count }}个文档)
          </el-checkbox>
        </el-checkbox-group>
      </div>

      <!-- 问题输入 -->
      <div class="form-item">
        <label>输入问题</label>
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          placeholder="请输入您的问题..."
          maxlength="2000"
          show-word-limit
        />
      </div>

      <!-- 配置 -->
      <div class="form-item inline">
        <label>检索数量:</label>
        <el-input-number v-model="topK" :min="1" :max="20" size="small" />
      </div>

      <!-- 查询按钮 -->
      <el-button 
        type="primary" 
        :icon="Search" 
        :loading="loading"
        :disabled="!canQuery"
        @click="handleQuery"
      >
        查询
      </el-button>
    </div>

    <!-- 查询结果 -->
    <div class="query-result" v-if="result">
      <!-- 答案 -->
      <div class="answer-section">
        <h4>回答</h4>
        <div class="answer-content">{{ result.answer }}</div>
        <div class="tokens-info">消耗 {{ result.tokens_used }} tokens</div>
      </div>

      <!-- 参考来源 -->
      <div class="sources-section" v-if="result.sources.length > 0">
        <h4>参考来源</h4>
        <div class="sources-list">
          <div v-for="(source, index) in result.sources" :key="index" class="source-item">
            <div class="source-header">
              <el-icon><Document /></el-icon>
              <span class="source-name">{{ source.document_name }}</span>
              <el-tag size="small" type="success">
                相似度: {{ formatScore(source.similarity_score) }}
              </el-tag>
            </div>
            <div class="source-content">{{ source.content }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.rag-query-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.query-form {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .form-item {
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
    }

    &.inline {
      display: flex;
      align-items: center;
      gap: 12px;

      label {
        margin-bottom: 0;
      }
    }
  }

  .el-checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
}

.query-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
}

.answer-section {
  h4 {
    margin: 0 0 12px;
    font-size: 14px;
  }

  .answer-content {
    padding: 16px;
    background: var(--el-color-primary-light-9);
    border-radius: 8px;
    line-height: 1.6;
    white-space: pre-wrap;
  }

  .tokens-info {
    margin-top: 8px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    text-align: right;
  }
}

.sources-section {
  h4 {
    margin: 0 0 12px;
    font-size: 14px;
  }
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;

  .source-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;

    .source-name {
      flex: 1;
      font-weight: 500;
    }
  }

  .source-content {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    line-height: 1.5;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }
}
</style>
