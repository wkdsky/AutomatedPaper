<template>
  <div class="student-manage-container">
    <div class="header">
      <el-button @click="goBack" type="text">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1>学生管理</h1>
    </div>

    <div class="actions">
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        添加学生
      </el-button>
      <el-button @click="fetchStudents">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-card class="student-table">
      <el-table :data="students" style="width: 100%" v-loading="loading">
        <el-table-column prop="student_id" label="学生ID" width="100" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="student_number" label="学号" width="120" />
        <el-table-column prop="class" label="班级" width="150" />
        <el-table-column prop="contact_info" label="联系方式" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="editStudent(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteStudent(scope.row.student_id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑学生对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingStudent.student_id ? '编辑学生' : '添加学生'"
      width="500px"
    >
      <el-form :model="editingStudent" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="editingStudent.name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="editingStudent.student_number" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="班级">
          <el-input v-model="editingStudent.class_name" placeholder="请输入班级" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="editingStudent.contact_info" placeholder="请输入联系方式" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="saveStudent">
          {{ editingStudent.student_id ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, ArrowLeft } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const students = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const editingStudent = ref({
  student_id: null,
  name: '',
  student_number: '',
  class_name: '',
  contact_info: ''
})

// 获取学生列表
const fetchStudents = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:8001/api/students')
    students.value = response.data.data || []
  } catch (error) {
    console.error('获取学生列表失败:', error)
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

// 编辑学生
const editStudent = (student) => {
  editingStudent.value = { ...student }
  showCreateDialog.value = true
}

// 保存学生（创建或更新）
const saveStudent = async () => {
  if (!editingStudent.value.name.trim()) {
    ElMessage.error('请输入学生姓名')
    return
  }

  try {
    let response
    if (editingStudent.value.student_id) {
      // 更新学生
      response = await axios.put(
        `http://localhost:8001/api/students/${editingStudent.value.student_id}`,
        editingStudent.value
      )
    } else {
      // 创建学生
      response = await axios.post('http://localhost:8001/api/students', editingStudent.value)
    }

    if (response.data.code === 1) {
      ElMessage.success(editingStudent.value.student_id ? '更新成功' : '创建成功')
      closeDialog()
      await fetchStudents()
    } else {
      ElMessage.error(response.data.msg || '操作失败')
    }
  } catch (error) {
    console.error('保存学生失败:', error)
    ElMessage.error('保存学生失败')
  }
}

// 删除学生
const deleteStudent = async (studentId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个学生吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const response = await axios.delete(`http://localhost:8001/api/students/${studentId}`)
    if (response.data.code === 1) {
      ElMessage.success('删除成功')
      await fetchStudents()
    } else {
      ElMessage.error(response.data.msg || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除学生失败:', error)
      ElMessage.error('删除学生失败')
    }
  }
}

// 关闭对话框
const closeDialog = () => {
  showCreateDialog.value = false
  editingStudent.value = {
    student_id: null,
    name: '',
    student_number: '',
    class_name: '',
    contact_info: ''
  }
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchStudents()
})
</script>

<style scoped>
.student-manage-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.header h1 {
  color: #2c3e50;
  margin: 0;
}

.actions {
  margin-bottom: 24px;
  display: flex;
  gap: 12px;
}

.student-table {
  background: white;
}
</style>