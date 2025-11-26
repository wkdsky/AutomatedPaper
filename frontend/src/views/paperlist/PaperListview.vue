<template>
  <div class="paper-list-container">
    <header class="main-header">
      <div class="title">自动阅卷系统</div>
      <button @click="goHome" class="back-btn">返回考试列表</button>
    </header>
    <div class="main-content">
      <!-- 考试信息和操作按钮 -->
      <div class="exam-info-section">
        <div class="exam-header">
          <h2>{{ examName }}</h2>
          <div class="exam-stats" v-if="papers.length > 0">
            <span class="total-papers">共 {{ papers.length }} 份试卷</span>
            <span class="graded-papers">已判卷 {{ gradedCount }} 份</span>
            <div class="progress-indicator">
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: progressPercentage + '%' }"
                ></div>
              </div>
              <span class="progress-text">{{ progressPercentage }}%</span>
            </div>
          </div>
        </div>
        
        <div class="action-buttons">
          <button @click="importStandardAnswers" class="action-btn import-answers-btn">
            导入标准答案
          </button>
          <button @click="batchGrade" class="action-btn batch-grade-btn" :disabled="gradedCount === papers.length">
            AI批量评分
          </button>
          <button @click="previewScores" class="action-btn preview-btn">
            预览成绩表
          </button>
          <button @click="exportScores" class="action-btn export-btn">
            导出成绩 Excel
          </button>
        </div>
      </div>

      <!-- 试卷列表 -->
      <div class="papers-section">
        <h3>学生试卷列表</h3>
        <div v-if="papers.length === 0" class="no-data">
          <p>暂无试卷数据</p>
          <p class="hint">请检查该考试是否已上传视频并处理完成</p>
        </div>
        <div v-else class="paper-grid">
          <div
            v-for="paper in papers"
            :key="paper.paper_id"
            @click="goToDetail(paper.paper_id)"
            class="paper-card"
          >
            <div class="paper-header">
            <div class="paper-title">{{ paper.paper_name }}</div>
            <div class="grading-status-label" v-if="paper.gradingStatus">
              <span v-if="paper.gradingStatus === 'ungraded'" class="status-ungraded">未判卷</span>
              <span v-else-if="paper.gradingStatus === 'partial'" class="status-partial">判卷中</span>
              <span v-else-if="paper.gradingStatus === 'graded'" class="status-graded">已判卷</span>
              </div>
            </div>
            <div class="paper-student">学生: {{ getStudentName(paper.student_id) }}</div>
            <div class="paper-actions">
              <button class="paper-action-btn">查看详情</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 成绩预览弹窗 -->
    <div v-if="showScorePreview" class="score-preview-dialog">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>成绩表预览</h3>
          <button @click="showScorePreview = false" class="close-btn">✕</button>
        </div>
        
        <div class="score-table-container">
                     <div class="table-actions">
             <button @click="addNewScore" class="table-action-btn add-btn">
               添加成绩
             </button>
             <button @click="refreshScores" class="table-action-btn refresh-btn">
               刷新数据
             </button>
           </div>
          
          <div class="score-table-wrapper">
            <table class="score-table">
              <thead>
                <tr>
                  <th>学生姓名</th>
                  <th>学生ID</th>
                  <th>试卷名称</th>
                  <th>总分</th>
                  <th>得分</th>
                  <th>判卷状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="score in scoreList" :key="score.paper_id" class="score-row">
                  <td>
                    <input 
                      v-if="score.editing" 
                      v-model="score.student_name" 
                      class="edit-input"
                      @blur="saveScore(score)"
                      @keyup.enter="saveScore(score)"
                    />
                    <span v-else>{{ score.student_name }}</span>
                  </td>
                  <td>{{ score.student_id }}</td>
                  <td>{{ score.paper_name }}</td>
                  <td>{{ score.total_score || 0 }}</td>
                  <td>
                    <input 
                      v-if="score.editing" 
                      v-model.number="score.final_score" 
                      type="number"
                      class="edit-input score-input"
                      @blur="saveScore(score)"
                      @keyup.enter="saveScore(score)"
                      :max="score.total_score"
                      min="0"
                    />
                    <span v-else :class="{'no-score': score.final_score === null || score.final_score === undefined}">
                      {{ score.final_score !== null && score.final_score !== undefined ? score.final_score : '未评分' }}
                    </span>
                  </td>
                  <td>
                    <span :class="['status-badge', `status-${score.grading_status}`]">
                      {{ getStatusText(score.grading_status) }}
                    </span>
                  </td>
                  <td>
                    <div class="row-actions">
                                             <button 
                         v-if="!score.editing" 
                         @click="editScore(score)" 
                         class="row-action-btn edit-btn"
                         title="编辑"
                       >
                         编辑
                       </button>
                       <button 
                         v-if="score.editing" 
                         @click="saveScore(score)" 
                         class="row-action-btn save-btn"
                         title="保存"
                       >
                         保存
                       </button>
                       <button 
                         v-if="score.editing" 
                         @click="cancelEdit(score)" 
                         class="row-action-btn cancel-btn"
                         title="取消"
                       >
                         取消
                       </button>
                       <button 
                         v-if="!score.editing" 
                         @click="deleteScore(score)" 
                         class="row-action-btn delete-btn"
                         title="删除"
                       >
                         删除
                       </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="score-summary">
            <div class="summary-item">
              <span class="summary-label">总试卷数:</span>
              <span class="summary-value">{{ scoreList.length }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">已评分:</span>
              <span class="summary-value">{{ gradedScoreCount }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">平均分:</span>
              <span class="summary-value">{{ averageScore }}</span>
            </div>
          </div>
        </div>
        
                 <div class="dialog-actions">
           <button @click="exportFromPreview" class="dialog-btn export-btn">
             导出Excel
           </button>
           <button @click="showScorePreview = false" class="dialog-btn cancel-btn">
             关闭
           </button>
         </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const papers = ref([])
const students = ref([])
const examName = ref('')
const exam_id = route.params.exam_id
const currentExamId = ref(Number(exam_id))

// 成绩预览相关
const showScorePreview = ref(false)
const scoreList = ref([])
const originalScoreData = ref([])

// 计算属性
const gradedCount = computed(() => {
  return papers.value.filter(p => p.gradingStatus === 'graded').length
})

const progressPercentage = computed(() => {
  if (papers.value.length === 0) return 0
  return Math.round((gradedCount.value / papers.value.length) * 100)
})

// 成绩相关计算属性
const gradedScoreCount = computed(() => {
  return scoreList.value.filter(score => 
    score.final_score !== null && score.final_score !== undefined
  ).length
})

const averageScore = computed(() => {
  const validScores = scoreList.value.filter(score => 
    score.final_score !== null && score.final_score !== undefined
  )
  if (validScores.length === 0) return '0.00'
  
  const total = validScores.reduce((sum, score) => sum + Number(score.final_score), 0)
  return (total / validScores.length).toFixed(2)
})

const goHome = () => {
  router.push('/home')
}

const goToDetail = (paper_id) => {
  // 将paper_id和exam_id保存到localStorage，以便后续返回时使用
  localStorage.setItem('lastPaperId', paper_id)
  localStorage.setItem('lastExamId', currentExamId.value)
  localStorage.setItem('lastExamName', examName.value)
  
  router.push({ path: `/paper/${paper_id}`, query: { exam_id: currentExamId.value } })
}

const getStudentName = (student_id) => {
  const s = students.value.find(stu => stu.id === student_id || stu.student_id === student_id)
  return s ? s.name : student_id
}

// 判卷状态获取
const fetchGradingStatus = async (paper) => {
  try {
    const res = await axios.get(`http://localhost:8001/api/paper-details/${paper.paper_id}`)
    const details = res.data.data || []
    if (details.length === 0) {
      paper.gradingStatus = 'ungraded'
      return
    }
    const scores = details.map(d => d.score)
    if (scores.every(s => s === null || s === undefined)) {
      paper.gradingStatus = 'ungraded'
    } else if (scores.every(s => s !== null && s !== undefined)) {
      paper.gradingStatus = 'graded'
    } else {
      paper.gradingStatus = 'partial'
    }
  } catch (e) {
    console.error('获取判卷状态失败', e)
    paper.gradingStatus = 'ungraded'
  }
}

// 加载试卷列表并获取判卷状态
const loadPapers = async (examId) => {
  try {
    const res = await axios.get(`http://localhost:8001/api/papers/${examId}`)
    papers.value = res.data.data || []
    // 并发获取每份试卷的判卷状态
    await Promise.all(papers.value.map(fetchGradingStatus))
  } catch (e) {
    console.error('获取试卷失败', e)
    papers.value = []
  }
}

// 导入标准答案
const importStandardAnswers = () => {
  // 这里可以添加导入标准答案的逻辑
  alert('导入标准答案功能待实现')
}

// AI批量评分
const batchGrade = async () => {
  if (gradedCount.value === papers.value.length) {
    alert('所有试卷已评分完成')
    return
  }
  
  if (!confirm('确定要对未评分的试卷进行AI批量评分吗？')) {
    return
  }
  
  try {
    // 这里添加AI批量评分的逻辑
    alert('AI批量评分功能待实现')
  } catch (e) {
    console.error('AI批量评分失败', e)
    alert('AI批量评分失败，请重试')
  }
}

// 预览成绩表
const previewScores = async () => {
  try {
    await loadScoreData()
    showScorePreview.value = true
  } catch (e) {
    console.error('加载成绩数据失败', e)
    alert('加载成绩数据失败，请重试')
  }
}

// 加载成绩数据
const loadScoreData = async () => {
  try {
    const scores = []
    
    for (const paper of papers.value) {
      // 获取试卷详情和分数
        const detailRes = await axios.get(`http://localhost:8001/api/paper-details/${paper.paper_id}`)
        const details = detailRes.data.data || []
      
      // 计算总分和得分
      let totalScore = 0
      let finalScore = 0
      let hasScore = false
      
      details.forEach(detail => {
        if (detail.total_score) {
          totalScore += detail.total_score
        }
        if (detail.score !== null && detail.score !== undefined) {
          finalScore += detail.score
          hasScore = true
        }
      })
      
      const studentName = getStudentName(paper.student_id)
      
      scores.push({
        paper_id: paper.paper_id,
        student_id: paper.student_id,
        student_name: studentName,
        paper_name: paper.paper_name,
        total_score: totalScore,
        final_score: hasScore ? finalScore : null,
        grading_status: paper.gradingStatus,
        editing: false,
        original_data: {
          student_name: studentName,
          final_score: hasScore ? finalScore : null
        }
      })
    }
    
    scoreList.value = scores
    originalScoreData.value = JSON.parse(JSON.stringify(scores))
  } catch (e) {
    console.error('加载成绩数据失败', e)
    throw e
  }
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'ungraded': '未判卷',
    'partial': '判卷中',
    'graded': '已判卷'
  }
  return statusMap[status] || '未知'
}

// 编辑成绩
const editScore = (score) => {
  score.editing = true
}

// 保存成绩
const saveScore = async (score) => {
  try {
    // 这里可以添加API调用来保存成绩
    // await axios.put(`http://localhost:8001/api/scores/${score.paper_id}`, {
    //   final_score: score.final_score,
    //   student_name: score.student_name
    // })
    
    score.editing = false
    score.original_data = {
      student_name: score.student_name,
      final_score: score.final_score
    }
    
    console.log('保存成绩:', score)
  } catch (e) {
    console.error('保存成绩失败', e)
    alert('保存成绩失败，请重试')
  }
}

// 取消编辑
const cancelEdit = (score) => {
  score.student_name = score.original_data.student_name
  score.final_score = score.original_data.final_score
  score.editing = false
}

// 删除成绩
const deleteScore = async (score) => {
  if (!confirm(`确定要删除 ${score.student_name} 的成绩记录吗？`)) {
    return
  }
  
  try {
    // 这里可以添加API调用来删除成绩
    // await axios.delete(`http://localhost:8001/api/scores/${score.paper_id}`)
    
    const index = scoreList.value.findIndex(s => s.paper_id === score.paper_id)
    if (index > -1) {
      scoreList.value.splice(index, 1)
    }
    
    console.log('删除成绩:', score)
  } catch (e) {
    console.error('删除成绩失败', e)
    alert('删除成绩失败，请重试')
  }
}

// 添加新成绩
const addNewScore = () => {
  const newScore = {
    paper_id: `new_${Date.now()}`,
    student_id: '',
    student_name: '',
    paper_name: '手动添加',
    total_score: 100,
    final_score: null,
    grading_status: 'ungraded',
    editing: true,
    original_data: {
      student_name: '',
      final_score: null
    }
  }
  
  scoreList.value.unshift(newScore)
}

// 刷新成绩数据
const refreshScores = async () => {
  try {
    await loadScoreData()
    alert('数据已刷新')
  } catch (e) {
    console.error('刷新数据失败', e)
    alert('刷新数据失败，请重试')
  }
}

// 从预览导出
const exportFromPreview = () => {
  showScorePreview.value = false
  exportScores()
}

const exportScores = async () => {
  try {
    const res = await axios.get(
      `http://localhost:8001/api/exams/${currentExamId.value}/scores/export`,
      { responseType: 'blob' }
    )
    // 下载
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `exam_${currentExamId.value}_scores.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    alert('导出失败')
  }
}

onMounted(async () => {
  // 获取学生列表
  try {
    const res = await axios.get('http://localhost:8001/api/students')
    students.value = res.data.data || []
  } catch (e) {
    console.error('获取学生列表失败', e)
    students.value = []
  }

  // 加载当前考试的试卷
  await loadPapers(exam_id)

  // 获取考试名称
  examName.value = route.query.examName || `考试 ${exam_id}`
  
  // 如果没有从query获取到考试名称，尝试从API获取
  if (!route.query.examName) {
    try {
      const res = await axios.get(`http://localhost:8001/api/exams/${exam_id}`)
      if (res.data.data) {
        examName.value = res.data.data.exam_name || `考试 ${exam_id}`
    }
  } catch (e) {
      console.error('获取考试信息失败', e)
    }
  }
})
</script>

<style scoped>
.paper-list-container {
  min-height: 100vh;
  width: 100vw;
  background: transparent;
  position: relative;
}

.paper-list-container::before {
  content: "";
  background-image: url('/3.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  opacity: 0.9;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(35, 57, 93, 0.9);
  color: #fff;
  padding: 0 32px;
  height: 56px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.title {
  font-size: 1.8rem;
  font-weight: bold;
}

.back-btn {
  background: #f39c12;
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
}

/* 主内容区域 */
.main-content {
  padding: 32px;
  height: calc(100vh - 56px);
  overflow-y: auto;
  background: rgba(247, 248, 250, 0.7);
}

/* 考试信息区域 */
.exam-info-section {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.exam-header h2 {
  margin: 0;
  color: #374151;
  font-size: 1.8rem;
}

.exam-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.total-papers, .graded-papers {
  font-size: 0.9rem;
  color: #6b7280;
}

.progress-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  width: 120px;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
}

.action-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.import-answers-btn {
  background: #3b82f6;
  color: white;
}

.import-answers-btn:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.batch-grade-btn {
  background: #8b5cf6;
  color: white;
}

.batch-grade-btn:hover:not(:disabled) {
  background: #7c3aed;
  transform: translateY(-1px);
}

.batch-grade-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
}

.preview-btn {
  background: #f59e0b;
  color: white;
}

.preview-btn:hover {
  background: #d97706;
  transform: translateY(-1px);
}

.export-btn {
  background: #10b981;
  color: white;
}

.export-btn:hover {
  background: #059669;
  transform: translateY(-1px);
}

/* 试卷列表区域 */
.papers-section {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.papers-section h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #374151;
}

.no-data {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.no-data p {
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.hint {
  font-size: 0.9rem;
  color: #9ca3af;
  font-style: italic;
}

.paper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.paper-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e5e7eb;
}

.paper-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: #3b82f6;
}

.paper-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.paper-title {
  font-weight: 600;
  font-size: 1.1rem;
  color: #374151;
  margin: 0;
}

.paper-student {
  color: #6b7280;
  margin-bottom: 16px;
  font-size: 0.95rem;
}

.paper-actions {
  display: flex;
  justify-content: flex-end;
}

.paper-action-btn {
  padding: 6px 16px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.paper-action-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.grading-status-label {
  margin-top: 8px;
}
.status-ungraded {
  background: #f87171;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.95em;
  margin-right: 4px;
}
.status-partial {
  background: #fbbf24;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.95em;
  margin-right: 4px;
}
.status-graded {
  background: #10b981;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.95em;
  margin-right: 4px;
}



@media (max-width: 768px) {
  .main-content {
    padding: 16px;
  }
  
  .exam-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .exam-stats {
    align-items: flex-start;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-btn {
    width: 100%;
  }

  .paper-grid {
    grid-template-columns: 1fr;
  }
  
  .paper-header {
    flex-direction: column;
    gap: 8px;
  }
}

/* 成绩预览弹窗样式 */
.score-preview-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog-content {
  background: white;
  border-radius: 12px;
  width: 90vw;
  max-width: 1200px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.dialog-header h3 {
  margin: 0;
  color: #374151;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 4px;
  border-radius: 4px;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.score-table-container {
  padding: 24px;
}

.table-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.table-action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn {
  background: #10b981;
  color: white;
}

.add-btn:hover {
  background: #059669;
}

.refresh-btn {
  background: #3b82f6;
  color: white;
}

.refresh-btn:hover {
  background: #2563eb;
}

.score-table-wrapper {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 16px;
}

.score-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.score-table th {
  background: #f9fafb;
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
}

.score-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #f3f4f6;
}

.score-row:hover {
  background: #f9fafb;
}

.edit-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.9rem;
}

.score-input {
  width: 80px;
}

.no-score {
  color: #9ca3af;
  font-style: italic;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-ungraded {
  background: #fee2e2;
  color: #dc2626;
}

.status-partial {
  background: #fef3c7;
  color: #d97706;
}

.status-graded {
  background: #d1fae5;
  color: #059669;
}

.row-actions {
  display: flex;
  gap: 4px;
}

.row-action-btn {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.8rem;
  margin: 0 2px;
  color: #374151;
}

.row-action-btn:hover {
  background: #e5e7eb;
}

.row-action-btn.edit-btn:hover {
  background: #dbeafe;
  color: #1d4ed8;
}

.row-action-btn.save-btn:hover {
  background: #dcfce7;
  color: #059669;
}

.row-action-btn.cancel-btn:hover {
  background: #fef3c7;
  color: #d97706;
}

.row-action-btn.delete-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.score-summary {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.summary-label {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 1.2rem;
  font-weight: 600;
  color: #374151;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.dialog-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.dialog-btn.export-btn {
  background: #10b981;
  color: white;
}

.dialog-btn.export-btn:hover {
  background: #059669;
}

.dialog-btn.cancel-btn {
  background: #e5e7eb;
  color: #374151;
}

.dialog-btn.cancel-btn:hover {
  background: #d1d5db;
}

@media (max-width: 768px) {
  .score-preview-dialog {
    padding: 10px;
  }
  
  .dialog-content {
    width: 95vw;
    max-height: 95vh;
  }
  
  .score-table-container {
    padding: 16px;
  }
  
  .table-actions {
    flex-direction: column;
  }
  
  .score-table-wrapper {
    max-height: 300px;
  }
  
  .score-table th,
  .score-table td {
    padding: 8px 4px;
    font-size: 0.8rem;
  }
  
  .score-summary {
    flex-direction: column;
    gap: 12px;
  }
  
  .dialog-actions {
    flex-direction: column;
  }
}
</style>