<template>
  <div class="answer-manager">
    <div class="tab-actions">
      <el-button type="primary" @click="showUploadDialog = true">
        上传图片
      </el-button>
      <el-button @click="fetchImages">刷新</el-button>
    </div>

    <el-table :data="images" style="width: 100%">
      <el-table-column prop="image_id" label="图片ID" width="100" />
      <el-table-column prop="student_name" label="学生" width="120" />
      <el-table-column prop="original_filename" label="文件名" />
      <el-table-column prop="file_size" label="文件大小" width="120">
        <template #default="scope">
          {{ formatFileSize(scope.row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="upload_time" label="上传时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.upload_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getImageStatusType(scope.row.status)">
            {{ getImageStatusText(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <!-- 图片上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传图片" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="选择学生" required>
          <el-select v-model="uploadForm.student_id" placeholder="选择学生" style="width: 100%">
            <el-option
              v-for="student in students"
              :key="student.student_id"
              :label="`${student.name} (${student.student_number || '无学号'})`"
              :value="student.student_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择图片" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="10"
            multiple
            accept=".jpg,.jpeg,.png,.bmp"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                只能上传jpg/png文件，且不超过10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadImages">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  examId: {
    type: String,
    required: true
  },
  students: {
    type: Array,
    default: () => []
  }
})

const images = ref([])
const showUploadDialog = ref(false)
const uploadForm = ref({ student_id: '' })
const uploadRef = ref()

// 获取图片列表
const fetchImages = async () => {
  try {
    const response = await axios.get(`http://localhost:8001/api/exams/${props.examId}/images`)
    images.value = response.data.data || []
  } catch (error) {
    console.error('获取图片列表失败:', error)
  }
}

// 上传图片
const uploadImages = async () => {
  if (!uploadForm.value.student_id) {
    ElMessage.error('请选择学生')
    return
  }

  const files = uploadRef.value.uploadFiles
  if (files.length === 0) {
    ElMessage.error('请选择图片文件')
    return
  }

  try {
    const formData = new FormData()
    formData.append('student_id', uploadForm.value.student_id)

    files.forEach(file => {
      formData.append('files', file.raw)
    })

    const response = await axios.post(`http://localhost:8001/api/exams/${props.examId}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.code === 1) {
      ElMessage.success(`上传成功，共 ${response.data.data.length} 个文件`)
      showUploadDialog.value = false
      uploadForm.value = { student_id: '' }
      uploadRef.value.clearFiles()
      await fetchImages()
    } else {
      ElMessage.error(response.data.msg || '上传失败')
    }
  } catch (error) {
    console.error('上传图片失败:', error)
    ElMessage.error('上传图片失败')
  }
}

// Helpers
const getImageStatusType = (status) => {
  const statusMap = {
    uploaded: 'success',
    processing: 'warning',
    processed: 'success',
    error: 'danger'
  }
  return statusMap[status] || ''
}

const getImageStatusText = (status) => {
  const statusMap = {
    uploaded: '已上传',
    processing: '处理中',
    processed: '已处理',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const formatFileSize = (size) => {
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let fileSize = size

  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024
    unitIndex++
  }

  return `${fileSize.toFixed(1)} ${units[unitIndex]}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchImages()
})
</script>

<style scoped>
.tab-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
</style>
