import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/Home.vue'
import ExamDetailView from '../views/ExamDetail.vue'
import StudentManageView from '../views/StudentManage.vue'
import ImageView from '../views/ImageView.vue'
import ScoreView from '../views/ScoreView.vue'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'Home',
    component: HomeView,
    meta: { title: '考试管理' }
  },
  {
    path: '/exam/:exam_id',
    name: 'ExamDetail',
    component: ExamDetailView,
    meta: { title: '考试详情' }
  },
  {
    path: '/students',
    name: 'StudentManage',
    component: StudentManageView,
    meta: { title: '学生管理' }
  },
  {
    path: '/exam/:exam_id/images',
    name: 'ImageView',
    component: ImageView,
    meta: { title: '图片管理' }
  },
  {
    path: '/exam/:exam_id/scores',
    name: 'ScoreView',
    component: ScoreView,
    meta: { title: '成绩管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router