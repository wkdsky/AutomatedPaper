<template>
  <div class="ai-grading-container">
    <div class="ai-grading-header">
      <h3>AI阅卷控制台</h3>
      <p>使用人工智能对学生的答卷进行自动评分和分析</p>
    </div>

    <div class="ai-grading-actions">
      <el-button
        type="success"
        size="large"
        @click="triggerAIGrading"
        :loading="aiGradingInProgress"
      >
        <el-icon><Cpu /></el-icon>
        开始AI阅卷
      </el-button>
      <el-button @click="$emit('refresh')">
        <el-icon><Refresh /></el-icon>
        刷新状态
      </el-button>
    </div>

    <div class="ai-grading-status" v-if="aiGradingInProgress">
      <el-progress
        :percentage="aiGradingProgress"
        :status="aiGradingStatus"
      />
      <p>{{ aiGradingMessage }}</p>
    </div>

    <div class="ai-grading-info" v-if="!aiGradingInProgress">
      <el-card>
        <template #header>
          <span>阅卷统计</span>
        </template>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ ungradedCount }}</div>
            <div class="stat-label">待阅卷</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ gradedCount }}</div>
            <div class="stat-label">已完成</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ totalStudents }}</div>
            <div class="stat-label">总学生数</div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  examId: {
    type: String,
    required: true
  },
  scores: {
    type: Array,
    default: () => []
  },
  totalStudents: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['refresh'])

const aiGradingInProgress = ref(false)
const aiGradingProgress = ref(0)
const aiGradingStatus = ref('success')
const aiGradingMessage = ref('')

const ungradedCount = computed(() => {
  return props.scores.filter(score => score.grading_status === 'pending').length
})

const gradedCount = computed(() => {
  return props.scores.filter(score => score.grading_status === 'completed').length
})

const triggerAIGrading = async () => {
  try {
    aiGradingInProgress.value = true
    aiGradingMessage.value = '正在处理中...'
    aiGradingProgress.value = 50 // Simple fake progress for now as API is sync/async wait
    
    ElMessage.info('正在启动AI阅卷...')
    const response = await axios.post(`http://localhost:8001/api/exams/${props.examId}/grade`)

    if (response.data.code === 1) {
      aiGradingProgress.value = 100
      aiGradingMessage.value = '阅卷完成'
      ElMessage.success(`AI阅卷完成！处理了 ${response.data.data.graded_count} 个学生`)
      emit('refresh')
      
      // Auto hide progress after delay
      setTimeout(() => {
        aiGradingInProgress.value = false
        aiGradingProgress.value = 0
      }, 2000)
    } else {
      aiGradingStatus.value = 'exception'
      aiGradingMessage.value = response.data.msg || 'AI阅卷失败'
      ElMessage.error(response.data.msg || 'AI阅卷失败')
      aiGradingInProgress.value = false
    }
  } catch (error) {
    console.error('AI阅卷失败:', error)
    aiGradingStatus.value = 'exception'
    aiGradingMessage.value = '请求异常'
    ElMessage.error('AI阅卷失败')
    aiGradingInProgress.value = false
  }
}
</script>

<style scoped>
.ai-grading-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ai-grading-header {
  text-align: center;
}

.ai-grading-header h3 {
  margin: 0 0 8px 0;
  color: #374151;
  font-size: 1.5rem;
  font-weight: 600;
}

.ai-grading-header p {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.ai-grading-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.ai-grading-status {
  text-align: center;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
}

.ai-grading-status p {
  margin: 12px 0 0 0;
  color: #374151;
  font-weight: 500;
}

.ai-grading-info {
  margin-top: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 16px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
  transition: all 0.2s;
}

.stat-item:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #3b82f6;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 0.9rem;
  color: #6b7280;
  font-weight: 500;
}
</style>
