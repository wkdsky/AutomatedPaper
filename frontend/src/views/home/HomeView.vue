<template>
  <div class="home-container">
    <header class="main-header">
      <div class="title">自动阅卷系统</div>
      <div class="user-info">
        <span>欢迎，教师</span>
        <button @click="logout">退出</button>
      </div>
      <img src="/vite.svg" alt="Vite Logo" />
    </header>
    <div class="main-content">
      <!-- 左侧考试列表 -->
      <aside class="sidebar">
<!-- 新增：导入视频按钮 -->
        <button @click="showUploadDialog = true" class="import-btn">导入视频</button>
        <h3>考试列表</h3>
        <ul>
          <li
            v-for="exam in exams"
            :key="exam.id"
            @click="selectExam(exam)"
            :class="{selected: selectedExam && selectedExam.id === exam.id}"
          >
            {{ exam.name }}
            <span v-if="examProgressMap[exam.id]" class="exam-progress-label">
              {{ examProgressMap[exam.id].graded }}/{{ examProgressMap[exam.id].total }}
            </span>
          </li>
        </ul>
      </aside>

      <!-- 右侧内容区域 -->
      <section class="content-area">
        <!-- 未选择考试时 -->
        <div v-if="!selectedExam" class="select-prompt">
          <h2>请选择一场考试</h2>
        </div>

        <!-- 选择考试后但未选择试卷 -->
        <div v-else>
          <h2>{{ selectedExam.name }}</h2>
          <h3>试卷列表</h3>

          <!-- 新增：整体判卷进度 -->
          <div v-if="gradingStats.total > 0" class="grading-progress">
            <span v-if="gradingStats.allGraded" class="all-graded">🎉 都改完了！</span>
            <span v-else>
              共 {{ gradingStats.total }} 套，已改完 {{ gradingStats.graded }} 套
              <span class="not-all-graded">（还有未判完的试卷）</span>
            </span>
          </div>

          <div v-if="papers.length === 0" class="no-data">
            暂无试卷数据
          </div>

          <div v-else class="paper-grid">
            <div
              v-for="paper in papers"
              :key="paper.paper_id"
              @click="selectPaper(paper)"
              class="paper-card"
            >
              <div class="paper-title">{{ paper.paper_name }}</div>
              <div class="paper-student">学生: {{ getStudentName(paper.student_id) }}</div>
              <!-- 新增：判卷状态标签 -->
              <div class="grading-status-label" v-if="paper.gradingStatus">
                <span v-if="paper.gradingStatus === 'ungraded'" class="status-ungraded">未判卷</span>
                <span v-else-if="paper.gradingStatus === 'partial'" class="status-partial">判卷中</span>
                <span v-else-if="paper.gradingStatus === 'graded'" class="status-graded">已判卷</span>
              </div>
            </div>
          </div>

          <button
            @click="exportScores"
            class="export-btn"
          >
            导出成绩 Excel
          </button>

        </div>
      </section>
    </div>

    <!-- 弹窗：上传视频和填写考试名称 -->
    <div v-if="showUploadDialog" class="upload-dialog">
      <div class="dialog-content">
        <h3>导入考试视频</h3>
        <label>考试名称：</label>
        <input v-model="uploadExamName" placeholder="请输入考试名称" />
        <label>选择视频文件：</label>
        <input type="file" @change="onFileChange" accept="video/*" />
        <div class="dialog-actions">
          <button @click="handleUpload" :disabled="!uploadExamName || !uploadFile">上传</button>
          <button @click="showUploadDialog = false">取消</button>
        </div>
        <div v-if="uploading">上传中，请稍候...</div>
        <div v-if="uploadMsg">{{ uploadMsg }}</div>
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const exams = ref([])
const papers = ref([])
const students = ref([])
const selectedExam = ref(null)
const gradingStats = ref({ total: 0, graded: 0, allGraded: false, loading: false })
const examProgressMap = ref({}) // { [examId]: { graded, total } }
const showUploadDialog = ref(false)
const uploadExamName = ref('')
const uploadFile = ref(null)
const uploading = ref(false)
const uploadMsg = ref('')


// 判卷状态获取
const fetchGradingStatus = async (paper) => {
  try {
    const res = await axios.get(`http://localhost:8001/api/papers/${paper.paper_id}/details`)
    const details = res.data
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
    paper.gradingStatus = 'ungraded'
  }
}

const fetchExamProgress = async (examId) => {
  try {
    const res = await axios.get(`http://localhost:8001/api/exams/${examId}/papers`)
    const papers = res.data
    let graded = 0
    let total = papers.length
    // 并发获取每份试卷的判卷状态
    await Promise.all(
      papers.map(async (paper) => {
        const detailRes = await axios.get(`http://localhost:8001/api/papers/${paper.paper_id}/details`)
        const details = detailRes.data
        if (
          details.length > 0 &&
          details.every(d => d.score !== null && d.score !== undefined)
        ) {
          graded += 1
        }
      })
    )
    examProgressMap.value[examId] = { graded, total }
  } catch (e) {
    examProgressMap.value[examId] = { graded: 0, total: 0 }
  }
}

// 加载试卷并统计进度
const selectExam = async (exam) => {
  selectedExam.value = exam
  papers.value = []
  gradingStats.value = { total: 0, graded: 0, allGraded: false, loading: true }
  try {
    const res = await axios.get(`http://localhost:8001/api/exams/${exam.id}/papers`)
    papers.value = res.data
    if (students.value.length === 0) {
      const res2 = await axios.get('http://localhost:8001/api/students')
      students.value = res2.data
    }
    // 判卷状态
    await Promise.all(papers.value.map(fetchGradingStatus))
    // 统计
    const total = papers.value.length
    const graded = papers.value.filter(p => p.gradingStatus === 'graded').length
    gradingStats.value = {
      total,
      graded,
      allGraded: total > 0 && total === graded,
      loading: false
    }
    // 加载每个考试的进度
    fetchExamProgress(exam.id)
  } catch (e) {
    console.error('获取试卷失败', e)
    gradingStats.value = { total: 0, graded: 0, allGraded: false, loading: false }
  }
}

const selectPaper = (paper) => {
  router.push(`/paper/${paper.paper_id}`)
}

const getStudentName = (student_id) => {
  const student = students.value.find(s => s.id === student_id || s.student_id === student_id)
  return student ? student.name : student_id
}

const logout = () => {
  localStorage.removeItem('username')
  router.push('/login')
}

const exportScores = async () => {
  // 检查是否有未判卷
  const ungraded = papers.value.filter(p => p.gradingStatus !== 'graded')
  if (ungraded.length > 0) {
    if (!confirm(`还有${ungraded.length}份试卷未判卷，确定要导出吗？`)) {
      return
    }
  }
  try {
    const res = await axios.get(
      `http://localhost:8001/api/exams/${selectedExam.value.id}/scores/export`,
      { responseType: 'blob' }
    )
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `exam_${selectedExam.value.id}_scores.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    alert('导出失败')
  }
}

const onFileChange = (e) => {
  uploadFile.value = e.target.files[0]
}

const handleUpload = async () => {
  if (!uploadExamName.value || !uploadFile.value) return
  uploading.value = true
  uploadMsg.value = ''
  try {
    const formData = new FormData()
    formData.append('exam_name', uploadExamName.value)
    formData.append('video', uploadFile.value)
    await axios.post('http://localhost:8001/api/exam/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    uploadMsg.value = '上传成功，正在处理！请稍后刷新页面查看新考试。'
    // 可选：自动刷新考试列表
    setTimeout(() => {
      showUploadDialog.value = false
      uploadExamName.value = ''
      uploadFile.value = null
      uploading.value = false
      uploadMsg.value = ''
      // 重新加载考试列表
      location.reload()
    }, 2000)
  } catch (e) {
    uploadMsg.value = '上传失败，请重试'
    uploading.value = false
  }
}



onMounted(async () => {
  if (!localStorage.getItem('username')) {
    router.push('/login')
    return
  }
  try {
    const res = await axios.get('http://localhost:8001/api/exams')
    exams.value = res.data
    // 加载每个考试的进度
    for (const exam of exams.value) {
      fetchExamProgress(exam.id)
    }
  } catch (e) {
    console.error('获取考试列表失败', e)
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  width: 100vw;
  background: #f7f8fa;
}
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #23395d;
  color: #fff;
  padding: 0 32px;
  height: 56px;
}
.title {
  font-size: 1.8rem;
  font-weight: bold;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-info button {
  background: #f39c12;
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
}
.main-content {
  display: flex;
  height: calc(100vh - 56px);
  width: 100vw;
  min-width: 0;
}
.sidebar {
  width: 240px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  padding: 16px 0;
}
.sidebar h3 {
  text-align: center;
  margin-bottom: 16px;
}
.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.sidebar li {
  padding: 10px 24px;
  cursor: pointer;
  border-left: 4px solid transparent;
  transition: background 0.2s, border-color 0.2s;
}
.sidebar li:hover {
  background: #f0f4fa;
  border-left: 4px solid #f39c12;
  font-weight: bold;
}
.sidebar li.selected {
  background: #f0f4fa;
  border-left: 4px solid #f39c12;
  font-weight: bold;
}
.content-area {
  flex: 1;
  padding: 32px 40px;
  background: #f7f8fa;
  overflow-y: auto;
}
.select-prompt {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #666;
}
.no-data {
  text-align: center;
  padding: 40px;
  color: #666;
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
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.paper-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.paper-title {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 1.1rem;
}
.paper-student {
  color: #666;
}
.grading-progress {
  margin-bottom: 16px;
  font-size: 1.1rem;
  font-weight: 500;
}
.all-graded {
  color: #10b981;
}
.not-all-graded {
  color: #f59e0b;
  font-size: 0.95em;
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
.exam-progress-label {
  margin-left: 8px;
  background: #e5e7eb;
  color: #2563eb;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 0.95em;
  font-weight: 500;
}
.export-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  font-weight: 600;
  margin-bottom: 20px;
  cursor: pointer;
}
.import-btn {
  background: #10b981;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  font-weight: 600;
  margin-left: 16px;
  cursor: pointer;
}
.upload-dialog {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.dialog-content {
  background: #fff;
  padding: 32px 24px;
  border-radius: 8px;
  min-width: 320px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.dialog-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

</style>