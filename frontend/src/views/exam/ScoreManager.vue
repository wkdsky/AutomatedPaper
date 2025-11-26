<template>
  <div class="score-manager">
    <div class="tab-actions">
      <el-button type="primary" @click="exportScores">
        导出成绩
      </el-button>
      <el-button @click="$emit('refresh')">刷新</el-button>
    </div>

    <el-table :data="scores" style="width: 100%">
      <el-table-column prop="student_name" label="学生" width="120" />
      <el-table-column prop="total_score" label="得分" width="100">
        <template #default="scope">
          <span :style="{ color: getScoreColor(scope.row.total_score, scope.row.max_score) }">
            {{ scope.row.total_score || 0 }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="max_score" label="满分" width="100" />
      <el-table-column label="得分率" width="100">
        <template #default="scope">
          {{ getScoreRate(scope.row.total_score, scope.row.max_score) }}%
        </template>
      </el-table-column>
      <el-table-column prop="grading_status" label="阅卷状态" width="120">
        <template #default="scope">
          <el-tag :type="getGradingStatusType(scope.row.grading_status)">
            {{ getGradingStatusText(scope.row.grading_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="graded_at" label="阅卷时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.graded_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="scope">
          <el-button size="small" @click="viewScoreDetail(scope.row)">
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 成绩详情对话框 -->
    <el-dialog v-model="showScoreDetailDialog" title="成绩详情" width="600px">
      <div v-if="scoreDetail">
        <h3>学生：{{ scoreDetail.student_name }}</h3>
        <p>总分：{{ scoreDetail.total_score }} / {{ scoreDetail.max_score }}</p>

        <el-table :data="detailScores" style="width: 100%">
          <el-table-column prop="questionNumber" label="题号" width="80" />
          <el-table-column prop="score" label="得分" width="80" />
          <el-table-column prop="maxScore" label="满分" width="80" />
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="scope">
              {{ (scope.row.confidence * 100).toFixed(1) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  scores: {
    type: Array,
    default: () => []
  },
  examId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['refresh'])

const showScoreDetailDialog = ref(false)
const scoreDetail = ref(null)
const detailScores = ref([])

// 查看成绩详情
const viewScoreDetail = (score) => {
  scoreDetail.value = score

  // 转换详细得分数据
  if (score.detail_scores && typeof score.detail_scores === 'object') {
    detailScores.value = Object.entries(score.detail_scores).map(([questionNumber, detail]) => ({
      questionNumber,
      score: detail.score || 0,
      maxScore: detail.maxScore || 0,
      confidence: detail.confidence || 0
    }))
  } else {
    detailScores.value = []
  }

  showScoreDetailDialog.value = true
}

// 导出成绩函数
const exportScores = () => {
  ElMessage.info('成绩导出功能开发中...')
}

// Helpers
const getScoreColor = (score, maxScore) => {
  if (!maxScore) return '#606266'
  const rate = score / maxScore
  if (rate >= 0.9) return '#67c23a'
  if (rate >= 0.7) return '#e6a23c'
  return '#f56c6c'
}

const getScoreRate = (score, maxScore) => {
  if (!maxScore) return 0
  return ((score / maxScore) * 100).toFixed(1)
}

const getGradingStatusType = (status) => {
  const statusMap = {
    pending: 'warning',
    processing: 'warning',
    completed: 'success',
    error: 'danger'
  }
  return statusMap[status] || ''
}

const getGradingStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.tab-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
</style>
