<template>
  <div class="question-manager">
    <div class="tab-actions">
      <el-button type="primary" @click="openAddQuestionDialog">
        添加题目
      </el-button>
      <el-button type="success" @click="showImportQuestionDialog = true">
        <el-icon><Upload /></el-icon>
        从文件导入题目
      </el-button>
      <el-button @click="fetchQuestions">刷新</el-button>
    </div>

    <el-table 
      ref="questionTableRef"
      :data="questions" 
      style="width: 100%"
      row-key="id"
      @row-dblclick="handleQuestionDblClick"
      class="question-table"
    >
      <el-table-column label="题号" width="80">
        <template #default="scope">
          <span>{{ scope.row.question_order || questions.indexOf(scope.row) + 1 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="题型" width="100">
        <template #default="scope">
          <el-tag :type="getQuestionTypeColor(scope.row.type)">
            {{ getQuestionTypeText(scope.row.type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="题目内容" min-width="200">
        <template #default="scope">
          <div class="truncate-text" :title="scope.row.content">{{ scope.row.content }}</div>
        </template>
      </el-table-column>
      <el-table-column label="分值" width="80">
        <template #default="scope">
          <span>{{ scope.row.score }}</span>
        </template>
      </el-table-column>
      <el-table-column label="参考答案" min-width="150">
        <template #default="scope">
          <div class="truncate-text" :title="scope.row.reference_answer">{{ scope.row.reference_answer }}</div>
        </template>
      </el-table-column>
      <el-table-column label="赋分规则" min-width="150">
        <template #default="scope">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <div class="truncate-text" :title="scope.row.scoring_rules">{{ scope.row.scoring_rules || '无' }}</div>
            <el-icon class="drag-handle" style="cursor: move; color: #909399;"><Rank /></el-icon>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top: 10px; font-size: 12px; color: #909399;">
      提示：双击任意行可编辑题目。拖动 <el-icon><Rank /></el-icon> 可调整题目顺序（题号会自动更新）。
    </div>

    <!-- 题目编辑/添加对话框 -->
    <el-dialog
      v-model="showQuestionDialog"
      :title="isEditMode ? '编辑题目' : '添加题目'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="currentQuestion" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="题号" required>
              <el-input-number 
                v-model="currentQuestion.question_number" 
                :min="1" 
                :max="isEditMode ? questions.length : questions.length + 1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="题型" required>
              <el-select v-model="currentQuestion.question_type" style="width: 100%">
                <el-option label="选择题" value="choice" />
                <el-option label="填空题" value="fill_blank" />
                <el-option label="主观题" value="essay" />
                <el-option label="计算题" value="calculation" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="分值" required>
          <el-input-number v-model="currentQuestion.total_score" :min="0" :precision="1" />
        </el-form-item>

        <el-form-item label="题目内容" required>
          <el-input
            v-model="currentQuestion.question_title"
            type="textarea"
            :rows="4"
            placeholder="请输入题目内容"
          />
        </el-form-item>
        
        <el-form-item label="参考答案">
          <el-input
            v-model="currentQuestion.reference_answer"
            type="textarea"
            :rows="3"
            placeholder="请输入参考答案"
          />
        </el-form-item>
        
        <el-form-item label="赋分规则">
          <el-input
            v-model="currentQuestion.scoring_rules"
            type="textarea"
            :rows="3"
            placeholder="请输入赋分规则"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuestionDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveQuestion">保存</el-button>
      </template>
    </el-dialog>

    <!-- 题目导入对话框 -->
    <el-dialog
      v-model="showImportQuestionDialog"
      title="从文件导入题目"
      width="600px"
      :close-on-click-modal="false"
    >
      <div style="text-align: center; padding: 40px;">
        <el-upload
          class="upload-demo"
          drag
          action=""
          :auto-upload="false"
          :on-change="handleQuestionFileChange"
          :show-file-list="true"
          accept=".doc,.docx,.xlsx,.xls,.txt,.csv"
          style="margin-bottom: 20px;"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 Word (.doc, .docx)、Excel (.xlsx, .xls)、文本文件 (.txt, .csv)
            </div>
          </template>
        </el-upload>

        <div style="margin-top: 30px; text-align: left;">
          <h4>题目导入格式说明 (Word/文本):</h4>
          <ul style="list-style: none; padding: 0; font-size: 13px; color: #666;">
            <li>• 每行为一道题目 (以回车换行区分)</li>
            <li>• 字段间用 @@@ 分隔</li>
            <li>• 格式: 题号@@@题型@@@题目内容@@@分值@@@参考答案@@@赋分规则</li>
            <li>• 题号: 可为空 (自动排序)</li>
            <li>• 题型: 可为空 (支持"选择题", "判断题"等)</li>
            <li>• 题目内容: 必填</li>
            <li>• 分值: 必填 (数字)</li>
            <li>• 参考答案: 可为空</li>
            <li>• 赋分规则: 可为空</li>
            <li>• 包含图片的行将自动跳过</li>
          </ul>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportQuestionDialog = false">取消</el-button>
          <el-button type="primary" @click="importQuestionsFromFile" :disabled="!selectedQuestionFile">
            开始导入
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, UploadFilled, Rank } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  examId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:questions'])

const questions = ref([])
const questionTableRef = ref(null)

// Dialogs
const showQuestionDialog = ref(false)
const showImportQuestionDialog = ref(false)

// State
const isEditMode = ref(false)
const currentQuestion = ref({
  id: null,
  question_number: 1,
  question_type: 'choice',
  question_title: '',
  reference_answer: '',
  scoring_rules: '',
  total_score: 4
})
const selectedQuestionFile = ref(null)

// 获取题目列表
const fetchQuestions = async () => {
  try {
    const response = await axios.get(`http://localhost:8001/api/exams/${props.examId}/questions`)
    questions.value = (response.data.data || []).sort((a, b) => a.question_order - b.question_order)
    emit('update:questions', questions.value)
  } catch (error) {
    console.error('获取题目列表失败:', error)
  }
}

// 打开添加题目对话框
const openAddQuestionDialog = () => {
  isEditMode.value = false
  currentQuestion.value = {
    id: null,
    question_number: questions.value.length + 1,
    question_type: 'choice',
    question_title: '',
    reference_answer: '',
    scoring_rules: '',
    total_score: 4
  }
  showQuestionDialog.value = true
}

// 双击题目行打开编辑
const handleQuestionDblClick = (row) => {
  isEditMode.value = true
  const index = questions.value.findIndex(q => q.id === row.id)
  
  currentQuestion.value = {
    id: row.id,
    question_number: index + 1,
    question_type: row.type,
    question_title: row.content,
    reference_answer: row.reference_answer,
    scoring_rules: row.scoring_rules,
    total_score: row.score
  }
  showQuestionDialog.value = true
}

// 保存题目
const handleSaveQuestion = async () => {
  if (!currentQuestion.value.question_title) {
    ElMessage.error('题目内容不能为空')
    return
  }

  try {
    if (isEditMode.value) {
      await axios.put(`http://localhost:8001/api/questions/${currentQuestion.value.id}`, {
        question_type: currentQuestion.value.question_type,
        content: currentQuestion.value.question_title,
        score: currentQuestion.value.total_score,
        reference_answer: currentQuestion.value.reference_answer,
        scoring_rules: currentQuestion.value.scoring_rules
      })

      // Handle Reorder if number changed
      const oldIndex = questions.value.findIndex(q => q.id === currentQuestion.value.id)
      const newIndex = currentQuestion.value.question_number - 1
      
      if (oldIndex !== -1 && oldIndex !== newIndex) {
        const items = [...questions.value]
        const [item] = items.splice(oldIndex, 1)
        items.splice(newIndex, 0, item)
        
        const questionIds = items.map(q => q.id)
        await axios.post(`http://localhost:8001/api/exams/${props.examId}/questions/reorder`, questionIds)
      }
      
      ElMessage.success('更新成功')
    } else {
      await axios.post(`http://localhost:8001/api/exams/${props.examId}/questions`, {
        question_order: currentQuestion.value.question_number,
        question_type: currentQuestion.value.question_type,
        content: currentQuestion.value.question_title,
        score: currentQuestion.value.total_score,
        reference_answer: currentQuestion.value.reference_answer,
        scoring_rules: currentQuestion.value.scoring_rules
      })
      ElMessage.success('添加成功')
    }

    showQuestionDialog.value = false
    await fetchQuestions()
  } catch (error) {
    console.error('保存题目失败:', error)
    ElMessage.error('保存题目失败')
  }
}

// 题目文件选择
const handleQuestionFileChange = (file) => {
  selectedQuestionFile.value = file.raw
}

// 导入题目
const importQuestionsFromFile = async () => {
  if (!selectedQuestionFile.value) {
    ElMessage.error('请选择文件')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedQuestionFile.value)

  try {
    ElMessage.info('正在导入题目，请稍候...')
    const response = await axios.post(`http://localhost:8001/api/exams/${props.examId}/import-questions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.code === 1) {
      ElMessage.success(`题目导入成功！共导入 ${response.data.data.count} 道题目`)
      showImportQuestionDialog.value = false
      selectedQuestionFile.value = null
      await fetchQuestions()
    } else {
      ElMessage.error(response.data.msg || '题目导入失败')
    }
  } catch (error) {
    console.error('题目导入失败:', error)
    if (error.response && error.response.data && error.response.data.detail) {
      ElMessage.error(`导入失败: ${error.response.data.detail}`)
    } else {
      ElMessage.error('题目导入失败')
    }
  }
}

// Reorder Logic
const reorderExamQuestions = async () => {
  try {
    const questionIds = questions.value.map(q => q.id)
    await axios.post(`http://localhost:8001/api/exams/${props.examId}/questions/reorder`, questionIds)
    await fetchQuestions()
  } catch (error) {
    console.error('更新排序失败:', error)
    ElMessage.error('更新排序失败')
  }
}

// Helpers
const getQuestionTypeColor = (type) => {
  const typeMap = {
    choice: 'primary',
    fill_blank: 'success',
    essay: 'warning',
    calculation: 'info'
  }
  return typeMap[type] || ''
}

const getQuestionTypeText = (type) => {
  const typeMap = {
    choice: '选择题',
    fill_blank: '填空题',
    essay: '主观题',
    calculation: '计算题'
  }
  return typeMap[type] || '未知'
}

// Drag and Drop
const ensureRowsDraggable = () => {
  if (!questionTableRef.value) return
  const trs = questionTableRef.value.$el.querySelectorAll('.el-table__body-wrapper tbody tr')
  trs.forEach(tr => {
    tr.setAttribute('draggable', 'true')
  })
}

const initDragAndDrop = () => {
  if (!questionTableRef.value) return

  const tbody = questionTableRef.value.$el.querySelector('.el-table__body-wrapper tbody')
  if (!tbody) return

  if (tbody.getAttribute('data-dnd-initialized')) return
  tbody.setAttribute('data-dnd-initialized', 'true')

  let draggingIndex = -1

  tbody.addEventListener('dragstart', (e) => {
    const tr = e.target.closest('tr')
    if (!tr) return
    
    draggingIndex = tr.sectionRowIndex
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', draggingIndex)
    tr.classList.add('dragging')
  })

  tbody.addEventListener('dragend', (e) => {
    const tr = e.target.closest('tr')
    if (tr) tr.classList.remove('dragging')
    draggingIndex = -1
  })

  tbody.addEventListener('dragover', (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  })

  tbody.addEventListener('dragenter', (e) => {
    const destTr = e.target.closest('tr')
    if (!destTr || draggingIndex === -1 || destTr.sectionRowIndex === draggingIndex) return
    
    const destIndex = destTr.sectionRowIndex
    
    const items = [...questions.value]
    const movedItem = items[draggingIndex]
    items.splice(draggingIndex, 1)
    items.splice(destIndex, 0, movedItem)
    questions.value = items
    
    draggingIndex = destIndex
  })

  tbody.addEventListener('drop', async (e) => {
    e.preventDefault()
    if (draggingIndex !== -1) {
      await reorderExamQuestions()
    }
  })
}

watch(questions, () => {
  nextTick(() => {
    ensureRowsDraggable()
    initDragAndDrop()
  })
}, { deep: true })

onMounted(async () => {
  await fetchQuestions()
  nextTick(() => {
    initDragAndDrop()
    ensureRowsDraggable()
  })
})
</script>

<style scoped>
.tab-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.truncate-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
:deep(.el-table__body tr.dragging) {
  opacity: 0.5;
  background: #f0f9eb;
}
.drag-handle {
  cursor: move;
  margin-left: 8px;
}
</style>
