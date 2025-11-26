<template>
  <div class="paper-detail-container">
    <header class="main-header">
      <div class="title">自动阅卷系统</div>
      <div class="header-actions">
        <div class="mode-selector">
          <button 
            @click="judgingMode = 'byStudent'" 
            :class="{'active': judgingMode === 'byStudent'}"
          >按学生切换</button>
          <button 
            @click="judgingMode = 'byQuestion'" 
            :class="{'active': judgingMode === 'byQuestion'}"
          >按题目切换</button>
        </div>
        <button @click="goBack" class="back-btn">返回试卷列表</button>
      </div>
    </header>

    <div class="paper-content">
      <div class="paper-info-panel">
        <h1 class="paper-title">{{ paperName }}</h1>

        <div class="grading-status-container">
          <div class="grading-status" v-if="details.length > 0">
            <span v-if="isGradingComplete" class="complete-status">
              <i class="check-icon">✓</i> 已完成打分
            </span>
            <span v-else class="incomplete-status">
              <i class="warning-icon">!</i> 还有{{ ungraded.length }}题未打分: 题号 {{ ungraded.join(', ') }}
            </span>
          </div>
        </div>
      </div>

      <!-- 学生/题目导航栏 -->
      <div class="navigation-bar">
        <!-- 按学生切换模式 - 显示学生列表 -->
        <div v-if="judgingMode === 'byStudent'" class="student-nav">
          <h3>当前题号: {{ currentQuestionNumber }}</h3>
          <div class="nav-items">
            <div 
              v-for="paper in examPapers" 
              :key="paper.paper_id"
              @click="switchStudent(paper.paper_id)"
              :class="{'active': paper.paper_id === Number(currentPaperId)}"
              class="nav-item"
            >
              {{ getStudentName(paper.student_id) }}
            </div>
          </div>
        </div>
        
        <!-- 按题目切换模式 - 显示题目列表 -->
        <div v-else class="question-nav">
          <h3>当前学生: {{ currentStudentName }}</h3>
          <div class="nav-items">
            <div 
              v-for="detail in sortedDetails" 
              :key="detail.detail_id"
              @click="switchQuestion(detail.question_number)"
              :class="{'active': detail.question_number === currentQuestionNumber, 'graded': detail.score !== null}"
              class="nav-item"
            >
              题{{ detail.question_number }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
        <p>加载中，请稍候...</p>
      </div>

      <div v-else-if="details.length === 0" class="no-data">
        <div class="empty-icon">📝</div>
        <p>暂无答题详情</p>
        <p class="sub-text">请确认该试卷是否存在</p>
      </div>

      <div v-else class="questions-container">
        <!-- 当前正在判卷的题目 -->
        <div class="question-card">
          <div class="question-header">
            <div class="question-number">题号 {{ currentDetail.question_number }}</div>
            <div class="scoring-panel">
              <div class="score-input-group">
                <label>得分:</label>
                <input 
                  v-model="currentDetail.inputScore" 
                  @input="validateScore(currentDetail)"
                  @blur="formatScore(currentDetail)"
                  type="text" 
                  class="score-input"
                  :class="{'invalid-score': currentDetail.scoreError}"
                />
                <span class="total-score">/ {{ currentDetail.total_score }}</span>
              </div>

              <button 
                @click="saveScore(currentDetail)" 
                class="save-btn"
                :disabled="currentDetail.scoreError"
              >
                <i class="save-icon">✓</i> 保存
              </button>

              <div class="feedback-message">
                <span v-if="currentDetail.saveMsg" :class="currentDetail.saveStatus">{{ currentDetail.saveMsg }}</span>
                <span v-if="currentDetail.scoreError" class="error">{{ currentDetail.scoreError }}</span>
              </div>
            </div>
          </div>

          <div class="question-body">
            <h3 class="question-title">{{ currentDetail.question_title }}</h3>

            <div class="answer-section">
              <div class="student-answer">
                <div class="section-header">
                  <i class="answer-icon">A</i>
                  <h4>学生答案</h4>
                </div>
                <pre class="answer-content">{{ currentDetail.answer_text }}</pre>
                <div class="answer-image-container">
                  <img
                    :src="`/answers/${currentDetail.detail_id}.jpg`"
                    :alt="`学生答案原图${currentDetail.detail_id}`"
                    @error="imgError = true"
                    v-if="!imgError"
                    class="answer-photo"
                    @click="openImagePreview(`/answers/${currentDetail.detail_id}.jpg`)"
                  />
                  <div v-if="!imgError" class="zoom-hint">点击放大查看</div>
                </div>
              </div>

              <div class="reference-answer" v-if="currentDetail.reference_answer">
                <div class="section-header">
                  <i class="reference-icon">R</i>
                  <h4>参考答案</h4>
                </div>
                <pre class="answer-content">{{ currentDetail.reference_answer }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮上方添加学生原始试卷图片区域 -->
      <div class="original-papers-section">
        <h3 class="section-title">学生原始试卷</h3>
        <div v-if="loadingOriginalImages" class="loading-container">
          <div class="spinner"></div>
          <p>加载试卷图片中...</p>
        </div>
        <div v-else-if="originalImages.length === 0" class="no-images-message">
          未找到原始试卷图片
        </div>
        <div v-else class="original-images-grid">
          <div 
            v-for="(image, index) in filteredOriginalImages" 
            :key="index" 
            class="original-image-container"
            @click="openImagePreview(image.url)"
          >
            <img 
              :src="image.url" 
              :alt="`原始试卷 ${index + 1}`" 
              class="original-image"
              @error="handleImageError(image)"
              v-if="!image.error"
            />
            <div v-if="!image.error" class="image-label">第 {{ index + 1 }} 页</div>
            <div v-else class="image-error">图片加载失败</div>
          </div>
        </div>
        <div v-if="originalImageLoadFailed" class="reload-images">
          <button @click="retryLoadImages" class="retry-btn">重新加载图片</button>
        </div>
      </div>

      <div class="bottom-actions">
        <button class="submit-btn" @click="submitAllScores">提交</button>
        <button class="finish-btn" @click="finishGrading">完成</button>
      </div>
    </div>

    <!-- 添加AI聊天框 -->
    <div class="ai-chat-container">
      <div class="chat-header" @click="toggleChat">
        <h3>AI助手</h3>
        <span class="toggle-icon">{{ chatExpanded ? '▼' : '▲' }}</span>
      </div>
      <div v-if="chatExpanded" class="chat-body">
        <div class="chat-messages" ref="chatMessagesEl">
          <div v-for="(message, index) in chatMessages" :key="index" :class="['message', message.role]">
            <div class="message-content">{{ message.content }}</div>
          </div>
          <div v-if="aiThinking" class="message ai thinking">
            <div class="thinking-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <input 
            v-model="chatInput" 
            @keyup.enter="sendMessage"
            placeholder="询问关于判分、题目或参考答案的问题..."
            :disabled="aiThinking"
          />
          <button @click="sendMessage" :disabled="!chatInput.trim() || aiThinking">发送</button>
        </div>
        <div class="chat-suggestions">
          <div class="suggestion-label">常见问题:</div>
          <button 
            v-for="(suggestion, index) in chatSuggestions" 
            :key="index" 
            @click="usesuggestion(suggestion)"
            class="suggestion-btn"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>
    </div>

    <!-- 添加图片预览弹窗 -->
    <div v-if="showImagePreview" class="image-preview-overlay" @click="closeImagePreview">
      <div class="image-preview-container">
        <img :src="previewImageSrc" alt="放大预览图" class="preview-image" />
        <button class="close-preview-btn" @click.stop="closeImagePreview">×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const details = ref([])
const examPapers = ref([]) // 同一场考试的所有试卷
const students = ref([]) // 所有学生
const paperName = ref('')
const loading = ref(true)
const exam_id = route.query.exam_id
const currentPaperId = ref(route.params.paper_id)
const currentQuestionNumber = ref(1) // 当前正在查看的题号
const judgingMode = ref('byQuestion') // 默认按题目切换
const imgError = ref(false)
const originalImages = ref([])
const loadingOriginalImages = ref(false)
const originalImageLoadFailed = ref(false)

// 如果 exam_id 可能为空，添加兜底逻辑
const safeExamId = exam_id || localStorage.getItem('lastExamId') || '1'

// 按题号排序的题目
const sortedDetails = computed(() => {
  return [...details.value].sort((a, b) => a.question_number - b.question_number)
})

// 当前学生姓名
const currentStudentName = computed(() => {
  const paper = examPapers.value.find(p => p.paper_id === Number(currentPaperId.value))
  if (!paper) return '未知学生'
  return getStudentName(paper.student_id)
})

// 当前正在查看/判分的题目详情
const currentDetail = computed(() => {
  const detail = details.value.find(d => d.question_number === currentQuestionNumber.value)
  return detail || {}
})

// 验证分数输入
const validateScore = (detail) => {
  // 清除先前的错误
  detail.scoreError = null

  // 检查是否为空
  if (!detail.inputScore.trim()) {
    detail.scoreError = '请输入分数'
    return false
  }

  // 检查是否为数字
  const score = Number(detail.inputScore)
  if (isNaN(score) || !/^\d+$/.test(detail.inputScore.trim())) {
    detail.scoreError = '请输入有效数字'
    return false
  }

  // 检查范围
  if (score < 0) {
    detail.scoreError = '分数不能为负'
    return false
  }

  if (score > detail.total_score) {
    detail.scoreError = `分数不能超过${detail.total_score}分`
    return false
  }

  return true
}

// 格式化分数（失去焦点时）
const formatScore = (detail) => {
  if (!detail.scoreError && detail.inputScore.trim() !== '') {
    detail.inputScore = String(Number(detail.inputScore))
  }
}

// 保存分数
const saveScore = async (detail) => {
  // 验证分数
  if (!validateScore(detail)) {
    return
  }

  detail.saveMsg = '保存中...'
  detail.saveStatus = 'saving'

  try {
    const scoreNum = Number(detail.inputScore)
    await axios.post(`http://localhost:8001/api/paper-details/${detail.detail_id}/score`, scoreNum)
    detail.score = scoreNum // 更新实际得分
    detail.saveMsg = '保存成功'
    detail.saveStatus = 'success'

    setTimeout(() => {
      detail.saveMsg = ''
    }, 2000)
  } catch (e) {
    detail.saveMsg = '保存失败'
    detail.saveStatus = 'error'
  }
}

// 未打分的题目
const ungraded = computed(() => {
  const ungradedQuestions = details.value
    .filter(d => d.score === null || d.score === undefined)
    .map(d => d.question_number)
    .sort((a, b) => a - b)
  return ungradedQuestions
})

// 是否完成打分
const isGradingComplete = computed(() => {
  return ungraded.value.length === 0 && details.value.length > 0
})

// 获取学生姓名
const getStudentName = (student_id) => {
  const s = students.value.find(stu => stu.id === student_id || stu.student_id === student_id)
  return s ? s.name : student_id
}

// 切换到其他学生的同一题目
const switchStudent = async (paperId) => {
  // 如果当前有未保存的分数，提示用户
  const unsavedDetail = details.value.find(d => 
    d.inputScore !== String(d.score ?? '') && !d.scoreError
  )

  if (unsavedDetail) {
    if (!confirm('有未保存的分数，是否继续切换？')) {
      return
    }
  }

  currentPaperId.value = paperId
  // 加载新的试卷详情
  await loadPaperDetails(paperId)
  // 保持题目编号不变
  const detail = details.value.find(d => d.question_number === currentQuestionNumber.value)
  if (!detail && details.value.length > 0) {
    // 如果当前题号在新试卷中不存在，则选择第一题
    currentQuestionNumber.value = sortedDetails.value[0].question_number
  }
}

// 切换到同一学生的其他题目
const switchQuestion = (questionNumber) => {
  // 保存当前题目的分数，如果有修改
  const currentDetail = details.value.find(d => d.question_number === currentQuestionNumber.value)
  if (currentDetail && currentDetail.inputScore !== String(currentDetail.score ?? '') && !currentDetail.scoreError) {
    if (confirm('当前题目分数已修改但未保存，是否先保存？')) {
      saveScore(currentDetail)
    }
  }
  
  currentQuestionNumber.value = questionNumber
}

// 返回上一页
const goBack = () => {
  console.log('返回时的 exam_id:', exam_id)
  console.log('返回时的 safeExamId:', safeExamId)
  
  // 使用 safeExamId 而不是 exam_id
  if (!safeExamId) {
    console.warn('未找到 exam_id，将返回首页')
    router.push('/home')
    return
  }
  
  // 返回到特定考试的试卷列表，并传递考试名称
  const currentExam = examPapers.value.find(p => p.exam_id === Number(safeExamId))
  const examName = currentExam?.exam_name || ''
  
  router.push({ 
    name: 'PaperList', 
    params: { exam_id: safeExamId },
    query: { examName: examName }
  })
}

// 加载试卷详情
const loadPaperDetails = async (paperId = currentPaperId.value) => {
  loading.value = true

  try {
    // 修改API路径，使用paper-details而不是papers/{id}/details
    const res = await axios.get(`http://localhost:8001/api/paper-details/${paperId}`)
    console.log('paper_id:', paperId);
    console.log('details:', res.data);
    // 处理每个试题，添加输入分数和验证属性
    details.value = (res.data.data || []).map(d => ({
      ...d,
      inputScore: d.score !== null ? String(d.score) : '',
      scoreError: null,
      saveMsg: '',
      saveStatus: ''
    }))
    
    // 设置默认查看的题号（如果未设置）
    if (details.value.length > 0 && !currentQuestionNumber.value) {
      currentQuestionNumber.value = sortedDetails.value[0].question_number
    }
  } catch (e) {
    console.error('获取答题详情失败', e)
  } finally {
    loading.value = false
  }
}

// 获取同一场考试下的所有试卷
const loadExamPapers = async () => {
  if (!safeExamId) return
  
  try {
    // 修改API路径，使用papers/{exam_id}而不是exams/{id}/papers
    const res = await axios.get(`http://localhost:8001/api/papers/${safeExamId}`)
    examPapers.value = res.data.data || []
    
    // 获取当前试卷名称
    const currentPaper = examPapers.value.find(p => p.paper_id === Number(currentPaperId.value))
    if (currentPaper) {
      paperName.value = currentPaper.paper_name
    }
  } catch (e) {
    console.error('获取考试试卷列表失败', e)
  }
}

// 批量提交所有未保存的分数
const submitAllScores = async () => {
  let hasError = false;
  for (const detail of details.value) {
    // 如果分数有修改且未保存，或有错误
    if (
      detail.inputScore !== String(detail.score ?? '') ||
      detail.scoreError
    ) {
      // 先校验
      if (!validateScore(detail)) {
        hasError = true;
        continue;
      }
      // 提交
      try {
        const scoreNum = Number(detail.inputScore);
        await axios.post(`http://localhost:8001/api/paper-details/${detail.detail_id}/score`, scoreNum);
        detail.score = scoreNum;
        detail.saveMsg = '保存成功';
        detail.saveStatus = 'success';
      } catch (e) {
        detail.saveMsg = '保存失败';
        detail.saveStatus = 'error';
        hasError = true;
      }
    }
  }
  if (hasError) {
    alert('有分数未填写或保存失败，请检查！');
  } else {
    alert('所有分数已成功提交！');
  }
};

// 完成阅卷，返回上一页
const finishGrading = () => {
  // 返回到特定考试的试卷列表，并传递考试名称
  const currentExam = examPapers.value.find(p => p.exam_id === Number(safeExamId))
  const examName = currentExam?.exam_name || ''
  
  router.push({ 
    name: 'PaperList', 
    params: { exam_id: safeExamId },
    query: { examName: examName }
  })
};

// 图片预览相关
const showImagePreview = ref(false)
const previewImageSrc = ref('')

// AI聊天相关
const chatExpanded = ref(true)
const chatMessages = ref([
  { role: 'ai', content: '你好！我是AI助手，可以帮你解答关于阅卷的问题。' }
])
const chatInput = ref('')
const aiThinking = ref(false)

// 聊天建议问题
const chatSuggestions = [
  "这道题应该怎么评分？",
  "标准答案是什么意思？",
  "这个学生的答案对吗？",
  "如何判断部分给分？"
]

// 打开图片预览
const openImagePreview = (src) => {
  previewImageSrc.value = src
  showImagePreview.value = true
}

// 关闭图片预览
const closeImagePreview = () => {
  showImagePreview.value = false
  previewImageSrc.value = ''
}

// 加载原始试卷图片
const loadOriginalImages = async () => {
  if (!currentPaperId.value || !safeExamId) return
  
  loadingOriginalImages.value = true
  originalImages.value = []
  originalImageLoadFailed.value = false
  
  try {
    // 首先尝试获取后端可能提供的原始试卷图片列表
    const res = await axios.get(`http://localhost:8001/api/paper/${currentPaperId.value}/original-images`)
    
    if (res.data.code === 1 && res.data.data && res.data.data.length > 0) {
      // 如果后端返回了图片列表
      originalImages.value = res.data.data.map(img => ({
        url: img.url,
        error: false,
        loaded: false
      }))
      console.log(`后端返回了 ${originalImages.value.length} 张试卷图片`)
    } else {
      console.log('后端未返回试卷图片，尝试本地拼接路径')
      // 如果后端没有提供图片列表，则尝试通用命名格式
      const paper = examPapers.value.find(p => p.paper_id === Number(currentPaperId.value))
      if (paper) {
        const studentId = paper.student_id
        
        // 从studentId中提取数字部分
        const studentNumber = studentId.split('_')[1] || studentId
        
        // 尝试多种可能的路径
        const possiblePaths = [
          // 格式1: 考试文件夹/学生文件夹/student数字_answer_sheet_页码.jpg (无下划线格式)
          `/student_answers/exam_${safeExamId}/student_${studentNumber}/student${studentNumber}_answer_sheet_`,
          // 格式2: 考试ID_时间戳/student_数字/student数字_answer_sheet_页码.jpg (无下划线格式)
          `/student_answers/exam_${safeExamId}_*/student_${studentNumber}/student${studentNumber}_answer_sheet_`,
          // 格式3: student_数字/student数字_answer_sheet_页码.jpg (无下划线格式)
          `/student_answers/student_${studentNumber}/student${studentNumber}_answer_sheet_`
        ]
        
        // 尝试加载前4页试卷（通常不会超过这个数量）
        for (let i = 1; i <= 4; i++) {
          for (const basePath of possiblePaths) {
            const imageUrl = `${basePath}${i}.jpg`
            originalImages.value.push({
              url: imageUrl,
              error: false,
              loaded: false
            })
          }
        }
      }
    }
  } catch (e) {
    console.error('获取原始试卷图片失败:', e)
    originalImageLoadFailed.value = true
    // 使用通用命名格式作为备选方案
    const studentIdNumber = currentPaperId.value % 100 // 简单推算学生ID
    for (let i = 1; i <= 4; i++) {
      originalImages.value.push({
        url: `/student_answers/exam_${safeExamId}/student_${studentIdNumber}/student${studentIdNumber}_answer_sheet_${i}.jpg`,
        error: false,
        loaded: false
      })
    }
  } finally {
    loadingOriginalImages.value = false
  }
}

// 处理图片加载错误
const handleImageError = (image) => {
  image.error = true
  // 检查是否所有图片都加载失败
  const allFailed = originalImages.value.every(img => img.error)
  if (allFailed && originalImages.value.length > 0) {
    originalImageLoadFailed.value = true
  }
}

// 重试加载图片
const retryLoadImages = () => {
  loadOriginalImages()
}

// 过滤掉加载失败的图片
const filteredOriginalImages = computed(() => {
  return originalImages.value.filter(img => !img.error)
})

// 切换聊天框展开/收起
const toggleChat = () => {
  chatExpanded.value = !chatExpanded.value
}

// 发送消息
const sendMessage = async () => {
  if (!chatInput.value.trim() || aiThinking.value) return
  
  // 添加用户消息
  chatMessages.value.push({ role: 'user', content: chatInput.value })
  
  // 清空输入框
  const userQuestion = chatInput.value
  chatInput.value = ''
  
  // 设置AI思考状态
  aiThinking.value = true
  
  // 滚动到底部
  nextTick(() => {
    if (chatMessagesEl.value) {
      chatMessagesEl.value.scrollTop = chatMessagesEl.value.scrollHeight
    }
  })
  
  try {
    // 准备上下文信息
    const context = {
      currentQuestion: currentDetail.value ? {
        questionNumber: currentDetail.value.question_number,
        title: currentDetail.value.question_title,
        studentAnswer: currentDetail.value.answer_text,
        referenceAnswer: currentDetail.value.reference_answer || '暂无标准答案',
        totalScore: currentDetail.value.total_score
      } : null,
      exam: examPapers.value.find(p => p.exam_id === Number(safeExamId)),
      student: currentStudentName.value
    }
    
    // 调用AI API
    const response = await axios.post('http://localhost:8001/api/ai-chat', {
      question: userQuestion,
      context: context
    })
    
    // 添加AI回复
    if (response.data && response.data.answer) {
      chatMessages.value.push({ role: 'ai', content: response.data.answer })
    } else {
      chatMessages.value.push({ role: 'ai', content: '抱歉，我无法处理您的请求。' })
    }
  } catch (error) {
    console.error('AI聊天请求失败:', error)
    chatMessages.value.push({ 
      role: 'ai', 
      content: '抱歉，发生了一些技术问题。请稍后再试。' 
    })
  } finally {
    aiThinking.value = false
    
    // 滚动到底部
    nextTick(() => {
      if (chatMessagesEl.value) {
        chatMessagesEl.value.scrollTop = chatMessagesEl.value.scrollHeight
      }
    })
  }
}

// 使用建议问题
const usesuggestion = (suggestion) => {
  chatInput.value = suggestion
  sendMessage()
}

// 添加DOM引用
const chatMessagesEl = ref(null)

onMounted(async () => {
  if (!localStorage.getItem('username')) {
    router.push('/login')
    return
  }

  if (!route.params.paper_id) {
    router.push('/home')
    return
  }

  // 获取所有学生
  try {
    const res = await axios.get('http://localhost:8001/api/students')
    students.value = res.data.data || []
  } catch (e) {
    console.error('获取学生列表失败', e)
    students.value = []
  }
  
  // 加载试卷详情
  await loadPaperDetails()
  // 加载同一场考试的所有试卷
  await loadExamPapers()
  // 加载原始试卷图片
  await loadOriginalImages()

  // 如果 query 里有 exam_id，保存下来以备后用
  if (route.query.exam_id) {
    localStorage.setItem('lastExamId', route.query.exam_id)
    console.log('保存 exam_id:', route.query.exam_id)
  }
})

// 观察 currentPaperId 变化，更新当前试卷信息
watch(currentPaperId, async (newVal) => {
  if (newVal) {
    await loadPaperDetails(newVal)
    await loadOriginalImages() // 当切换学生时重新加载原始试卷图片
  }
})

// 观察 currentDetail 变化，重置 imgError
watch(currentDetail, () => {
  imgError.value = false;
})
</script>

<style scoped>
.paper-detail-container {
  min-height: 100vh;
  background: transparent;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  width: 100vw;
  display: flex;
  flex-direction: column;
  position: relative;
}

.paper-detail-container::before {
  content: "";
  background-image: url('/2.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -2;
  opacity: 0.85;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(30, 41, 59, 0.9);
  color: #fff;
  padding: 0 2rem;
  height: 64px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  width: 100%;
}

.title {
  font-size: 1.6rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.mode-selector {
  display: flex;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 2px;
}

.mode-selector button {
  background: transparent;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.mode-selector button.active {
  background: rgba(255, 255, 255, 0.2);
  font-weight: 500;
}

.back-btn {
  background: #f59e0b;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
}

.back-btn:hover {
  background: #d97706;
}

.paper-content {
  width: 100%;
  padding: 2rem 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.paper-info-panel,
.no-data,
.questions-container {
  width: 95%;
  max-width: 1200px;
  margin-bottom: 2rem;
}

.paper-info-panel {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 1.5rem 2rem;
  box-shadow: 0 1px 5px rgba(0,0,0,0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
}

.paper-title {
  font-size: 1.8rem;
  margin: 0;
  color: #111827;
}

.grading-status-container {
  margin-top: 0;
}

@media (max-width: 768px) {
  .grading-status-container {
    margin-top: 1rem;
  }
}

.grading-status {
  padding: 0.6rem 1rem;
  border-radius: 4px;
  background: #f9fafb;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.complete-status {
  color: #10b981;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.incomplete-status {
  color: #f59e0b;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.check-icon {
  font-weight: bold;
  font-size: 1.1rem;
}

.warning-icon {
  font-weight: bold;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #f59e0b;
  color: white;
  font-size: 0.9rem;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-data {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  min-height: 300px;
  font-size: 1.2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.sub-text {
  color: #6b7280;
  font-size: 0.9rem;
}

.questions-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.question-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 1px 5px rgba(0,0,0,0.2);
  overflow: hidden;
  width: 100%;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 1rem;
}

.question-number {
  font-size: 1.1rem;
  font-weight: 600;
  color: #475569;
  padding: 0.4rem 0.8rem;
  background: #e2e8f0;
  border-radius: 4px;
}

.scoring-panel {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.score-input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-input-group label {
  font-weight: 500;
  color: #475569;
}

.score-input {
  width: 60px;
  padding: 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  text-align: center;
  font-size: 1rem;
  transition: border 0.2s;
}

.score-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.total-score {
  color: #64748b;
}

.invalid-score {
  border-color: #ef4444 !important;
  background-color: #fee2e2;
}

.save-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: #10b981;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover {
  background: #059669;
}

.save-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.save-icon {
  font-size: 0.9rem;
}

.feedback-message {
  min-height: 1.5rem;
  min-width: 120px;
}

.question-body {
  padding: 1.5rem;
}

.question-title {
  font-size: 1.1rem;
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #111827;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.answer-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.student-answer, .reference-answer {
  background: #f9fafb;
  border-radius: 6px;
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.section-header h4 {
  margin: 0;
  color: #4b5563;
  font-weight: 500;
}

.answer-icon, .reference-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-style: normal;
  font-weight: bold;
  font-size: 0.8rem;
}

.answer-icon {
  background: #3b82f6;
  color: white;
}

.reference-icon {
  background: #8b5cf6;
  color: white;
}

.answer-content {
  margin: 0;
  padding: 0.75rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  white-space: pre-wrap;
  line-height: 1.6;
  font-family: inherit;
  color: #374151;
  overflow-x: auto;
}

.saving {
  color: #3b82f6;
}

.success {
  color: #10b981;
}

.error {
  color: #ef4444;
}

.bottom-actions {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin: 2rem 0;
}

.submit-btn, .finish-btn {
  padding: 0.8rem 2.5rem;
  font-size: 1.2rem;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.submit-btn {
  background: #10b981;
  color: #fff;
}

.submit-btn:hover {
  background: #059669;
}

.finish-btn {
  background: #3b82f6;
  color: #fff;
}

.finish-btn:hover {
  background: #2563eb;
}

@media (max-width: 768px) {
  .paper-content {
    padding: 1rem;
    width: 100%;
  }

  .paper-info-panel {
    padding: 1rem;
    flex-direction: column;
    align-items: flex-start;
  }

  .grading-status-container {
    width: 100%;
  }

  .question-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .scoring-panel {
    width: 100%;
    margin-top: 0.5rem;
  }
}

/* 导航栏样式 */
.navigation-bar {
  width: 95%;
  max-width: 1200px;
  margin-bottom: 1rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 5px rgba(0,0,0,0.2);
}

.navigation-bar h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #333;
}

.nav-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.nav-item {
  padding: 0.5rem 1rem;
  background: #f1f5f9;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #e2e8f0;
}

.nav-item.active {
  background: #3b82f6;
  color: white;
}

.nav-item.graded {
  position: relative;
}

.nav-item.graded::after {
  content: "✓";
  position: absolute;
  top: -5px;
  right: -5px;
  background: #10b981;
  color: white;
  width: 16px;
  height: 16px;
  font-size: 10px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.answer-image-container {
  position: relative;
  display: inline-block;
  margin-top: 10px;
}

.answer-photo {
  max-width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: zoom-in;
  transition: transform 0.2s;
}

.answer-photo:hover {
  transform: scale(1.02);
}

.zoom-hint {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.answer-image-container:hover .zoom-hint {
  opacity: 1;
}

.image-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.image-preview-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
}

.preview-image {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
}

.close-preview-btn {
  position: absolute;
  top: -40px;
  right: 0;
  background: transparent;
  border: none;
  color: white;
  font-size: 2rem;
  cursor: pointer;
}

/* 原始试卷图片区域样式 */
.original-papers-section {
  width: 95%;
  max-width: 1200px;
  margin: 0 auto 2rem auto;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 5px rgba(0,0,0,0.2);
}

.section-title {
  font-size: 1.3rem;
  margin-top: 0;
  margin-bottom: 1rem;
  color: #1e293b;
}

.original-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.original-image-container {
  position: relative;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  cursor: zoom-in;
  aspect-ratio: 3/4;
  background: #f9fafb;
}

.original-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.2s;
}

.original-image-container:hover .original-image {
  transform: scale(1.05);
}

.image-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 4px 8px;
  font-size: 0.8rem;
  text-align: center;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #ef4444;
  font-size: 0.9rem;
  text-align: center;
  padding: 1rem;
}

.no-images-message {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
  font-style: italic;
}

.reload-images {
  text-align: center;
  margin-top: 1rem;
}

.retry-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

/* AI聊天框样式 */
.ai-chat-container {
  position: fixed;
  bottom: 0;
  right: 20px;
  width: 350px;
  background: white;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
  overflow: hidden;
  transition: height 0.3s ease;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
}

.chat-header h3 {
  margin: 0;
  font-size: 1rem;
}

.toggle-icon {
  font-size: 0.8rem;
}

.chat-body {
  display: flex;
  flex-direction: column;
  height: 400px;
}

.chat-messages {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message {
  max-width: 80%;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 0.9rem;
  line-height: 1.4;
}

.message.user {
  align-self: flex-end;
  background: #e9f2ff;
  border-bottom-right-radius: 4px;
}

.message.ai {
  align-self: flex-start;
  background: #f0f2f5;
  border-bottom-left-radius: 4px;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  background: #aaa;
  border-radius: 50%;
  display: inline-block;
  animation: pulse 1.5s infinite ease-in-out;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 1; }
}

.chat-input {
  display: flex;
  padding: 10px;
  border-top: 1px solid #eee;
}

.chat-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 8px;
}

.chat-input button {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0 15px;
  cursor: pointer;
}

.chat-input button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.chat-suggestions {
  padding: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border-top: 1px solid #eee;
  background: #f9fafb;
}

.suggestion-label {
  width: 100%;
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 5px;
}

.suggestion-btn {
  background: #e9f2ff;
  border: 1px solid #d1e0ff;
  border-radius: 12px;
  padding: 5px 10px;
  font-size: 0.8rem;
  cursor: pointer;
}

.suggestion-btn:hover {
  background: #d1e0ff;
}

@media (max-width: 768px) {
  .ai-chat-container {
    width: 100%;
    right: 0;
  }
}
</style>