<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoPlay, Check, Close, Loading, Tools, Clock
} from '@element-plus/icons-vue'
import { useAgentStore } from '@/stores/agent'
import type { AgentTool } from '@/types'

const agentStore = useAgentStore()

// 状态
const taskInput = ref('')
const selectedToolIds = ref<number[]>([])
const maxIterations = ref(10)

// 计算属性
const canExecute = computed(() => taskInput.value.trim() && !agentStore.executing)

// 只显示内置工具
const builtinTools = computed(() =>
  agentStore.tools.filter(tool => tool.tool_type === 'builtin')
)

// 方法
async function handleExecute() {
  if (!taskInput.value.trim()) {
    ElMessage.warning('请输入任务描述')
    return
  }

  try {
    const toolIds = selectedToolIds.value.length > 0 ? selectedToolIds.value : undefined
    await agentStore.executeTask(taskInput.value, toolIds, maxIterations.value)
    ElMessage.success('任务执行完成')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '执行失败')
  }
}

function handleStreamExecute() {
  if (!taskInput.value.trim()) {
    ElMessage.warning('请输入任务描述')
    return
  }

  const toolIds = selectedToolIds.value.length > 0 ? selectedToolIds.value : undefined
  agentStore.streamExecuteTask(taskInput.value, toolIds, maxIterations.value)
}

async function handleToggleTool(tool: AgentTool) {
  try {
    await agentStore.toggleTool(tool.id, !tool.is_enabled)
    ElMessage.success(tool.is_enabled ? '已禁用' : '已启用')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getStatusIcon(status: string) {
  const icons: Record<string, any> = {
    pending: Clock,
    running: Loading,
    completed: Check,
    failed: Close
  }
  return icons[status] || Clock
}

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

onMounted(() => {
  agentStore.fetchTools()
  agentStore.fetchExecutions()
})
</script>

<template>
  <div class="agent-view">
    <div class="agent-layout">
      <!-- 左侧：工具列表 -->
      <aside class="tools-sidebar">
        <div class="tools-header">
          <h3>内置工具</h3>
        </div>

        <div class="tools-list" v-loading="agentStore.loading">
          <template v-if="builtinTools.length > 0">
            <div v-for="tool in builtinTools" :key="tool.id" class="tool-card">
              <div class="tool-header-row">
                <div class="tool-icon">
                  <el-icon :size="20"><Tools /></el-icon>
                </div>
                <div class="tool-name-col">
                  <span class="tool-name">{{ tool.name }}</span>
                </div>
                <el-switch
                  :model-value="tool.is_enabled"
                  @change="handleToggleTool(tool)"
                  size="small"
                />
              </div>
              <p class="tool-desc">{{ tool.description }}</p>
            </div>
          </template>
          <div v-else class="empty-tools">
            <el-icon :size="48" color="#909399"><Tools /></el-icon>
            <h4>系统内置工具未初始化</h4>
            <p class="empty-desc">
              系统需要初始化内置工具（计算器、搜索、天气查询等）才能使用 Agent 功能。
            </p>
            <el-alert type="info" :closable="false" style="margin-top: 16px;">
              <template #title>
                <span style="font-weight: 500;">如何初始化？</span>
              </template>
              <div style="font-size: 13px; line-height: 1.6; margin-top: 4px;">
                请联系系统管理员运行以下命令初始化内置工具：<br>
                <code style="background: #f5f7fa; padding: 2px 8px; border-radius: 3px; margin-top: 4px; display: inline-block;">
                  python backend/scripts/seed_data.py
                </code>
              </div>
            </el-alert>
          </div>
        </div>
      </aside>

      <!-- 右侧：任务执行 -->
      <main class="execution-main">
        <div class="execution-header">
          <h2>Agent 任务执行</h2>
        </div>

        <div class="execution-content">
          <!-- 任务输入区 -->
          <div class="task-input-section">
            <el-input
              v-model="taskInput"
              type="textarea"
              :rows="3"
              placeholder="请描述您要执行的任务，例如：搜索最新的AI新闻并总结..."
              maxlength="2000"
              show-word-limit
            />
            <div class="action-bar">
              <div class="config-inline">
                <span>最大迭代:</span>
                <el-input-number v-model="maxIterations" :min="1" :max="50" size="small" style="width: 100px" />
              </div>
              <div class="buttons">
                <el-button 
                  type="primary" 
                  :icon="VideoPlay" 
                  :loading="agentStore.executing"
                  :disabled="!canExecute"
                  @click="handleExecute"
                >
                  执行
                </el-button>
                <el-button 
                  :icon="VideoPlay" 
                  :loading="agentStore.executing"
                  :disabled="!canExecute"
                  @click="handleStreamExecute"
                >
                  流式
                </el-button>
              </div>
            </div>
          </div>

          <!-- 执行结果/时间线 -->
          <div class="result-timeline" v-if="agentStore.currentExecution || agentStore.streamingSteps.length > 0">
            <h3>执行过程</h3>
            <div class="steps-container">
              <div class="timeline-line"></div>
              <div class="steps-list">
                <template v-for="(step, index) in (agentStore.currentExecution?.steps || agentStore.streamingSteps)" :key="index">
                  <div class="step-item">
                    <div class="step-marker"></div>
                    <div class="step-body">
                      <div class="step-title">
                        <span class="step-action">{{ step.action }}</span>
                        <span class="step-num">Step {{ step.step_number }}</span>
                      </div>
                      <div class="step-details">
                        <div class="detail-row" v-if="step.thought">
                          <span class="label">Thought:</span>
                          <span class="content">{{ step.thought }}</span>
                        </div>
                        <div class="detail-row" v-if="step.action_input">
                          <span class="label">Input:</span>
                          <code class="content code">{{ JSON.stringify(step.action_input) }}</code>
                        </div>
                        <div class="detail-row" v-if="step.observation">
                          <span class="label">Observation:</span>
                          <span class="content">{{ step.observation }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <!-- 最终结果 -->
            <div class="final-result-card" v-if="agentStore.currentExecution?.result || agentStore.streamingResult">
              <div class="result-header">
                <el-icon><Check /></el-icon>
                <span>最终结果</span>
              </div>
              <div class="result-body">
                {{ agentStore.currentExecution?.result || agentStore.streamingResult }}
              </div>
            </div>
          </div>
          
          <!-- 执行历史入口 (简化) -->
          <div class="history-link-section">
             <el-divider>执行历史</el-divider>
             <div class="history-mini-list">
                <template v-if="agentStore.executions.length > 0">
                  <div 
                    v-for="exec in agentStore.executions.slice(0, 5)" 
                    :key="exec.execution_id" 
                    class="history-mini-item"
                    @click="agentStore.fetchExecution(exec.execution_id)"
                  >
                    <el-tag :type="getStatusType(exec.status)" size="small">{{ getStatusText(exec.status) }}</el-tag>
                    <span class="task-summary">{{ exec.task }}</span>
                    <span class="time">{{ formatDate(exec.created_at) }}</span>
                  </div>
                </template>
                <div v-else class="no-history">暂无历史记录</div>
             </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped lang="scss">
.agent-view {
  height: 100%;
  padding: 0;
  overflow: hidden;
  background: var(--el-bg-color);
}

.agent-layout {
  display: flex;
  height: 100%;
  
  .tools-sidebar {
    width: 320px;
    border-right: 1px solid var(--el-border-color-light);
    display: flex;
    flex-direction: column;
    background: #fff;
    
    .tools-header {
      padding: 16px;
      border-bottom: 1px solid var(--el-border-color-light);
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }
    
    .tools-list {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
  }
  
  .execution-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--el-bg-color-page);
    
    .execution-header {
      padding: 16px 24px;
      background: #fff;
      border-bottom: 1px solid var(--el-border-color-light);
      
      h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }
    }
    
    .execution-content {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      max-width: 900px;
      margin: 0 auto;
      width: 100%;
    }
  }
}

.tool-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
  transition: all 0.2s;
  
  &:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    border-color: var(--el-border-color);
  }
  
  .tool-header-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
    
    .tool-icon {
      width: 32px;
      height: 32px;
      background: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .tool-name-col {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;
      
      .tool-name {
        font-weight: 500;
        font-size: 14px;
      }
    }
  }
  
  .tool-desc {
    margin: 0;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

.task-input-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  
  .action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .config-inline {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--el-text-color-regular);
    }
    
    .buttons {
      display: flex;
      gap: 12px;
    }
  }
}

.result-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
  
  h3 {
    margin: 0;
    font-size: 16px;
    border-left: 4px solid var(--el-color-primary);
    padding-left: 12px;
  }
}

.steps-container {
  position: relative;
  padding-left: 20px;
  
  .timeline-line {
    position: absolute;
    left: 7px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--el-border-color-light);
  }
}

.step-item {
  position: relative;
  margin-bottom: 20px;
  
  .step-marker {
    position: absolute;
    left: -17px;
    top: 16px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--el-color-primary);
    border: 2px solid #fff;
    box-shadow: 0 0 0 2px var(--el-color-primary-light-5);
  }
  
  .step-body {
    background: #fff;
    border-radius: 8px;
    border: 1px solid var(--el-border-color-light);
    overflow: hidden;
    
    .step-title {
      background: var(--el-fill-color-light);
      padding: 10px 16px;
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid var(--el-border-color-light);
      
      .step-action {
        font-weight: 600;
        color: var(--el-color-primary);
      }
      .step-num {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
    
    .step-details {
      padding: 12px 16px;
      font-size: 13px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      
      .detail-row {
        display: flex;
        flex-direction: column;
        gap: 4px;
        
        .label {
          font-weight: 500;
          color: var(--el-text-color-primary);
        }
        
        .content {
          color: var(--el-text-color-regular);
          line-height: 1.5;
          
          &.code {
            background: var(--el-fill-color-darker);
            padding: 8px;
            border-radius: 4px;
            font-family: monospace;
            white-space: pre-wrap;
          }
        }
      }
    }
  }
}

.final-result-card {
  background: var(--el-color-success-light-9);
  border: 1px solid var(--el-color-success-light-5);
  border-radius: 8px;
  overflow: hidden;
  
  .result-header {
    padding: 10px 16px;
    background: var(--el-color-success-light-8);
    color: var(--el-color-success);
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .result-body {
    padding: 16px;
    line-height: 1.6;
    color: var(--el-text-color-primary);
    white-space: pre-wrap;
  }
}

.history-link-section {
  margin-top: 20px;
  
  .history-mini-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .history-mini-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px;
    background: #fff;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
    
    &:hover {
      background: var(--el-fill-color-light);
    }
    
    .task-summary {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 13px;
    }
    
    .time {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
  
  .no-history {
    text-align: center;
    color: var(--el-text-color-secondary);
    font-size: 13px;
    padding: 10px;
  }
}

.empty-tools {
  text-align: center;
  padding: 40px 20px;
  color: var(--el-text-color-secondary);

  h4 {
    margin: 16px 0 8px;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .empty-desc {
    margin: 0 0 16px;
    font-size: 14px;
    line-height: 1.6;
    color: var(--el-text-color-regular);
  }

  code {
    background: #f5f7fa;
    padding: 2px 8px;
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    color: var(--el-color-primary);
  }
}
</style>
