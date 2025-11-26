import { createRouter, createWebHistory } from 'vue-router'
import ExamListView from '../views/home/examlist.vue'
import LoginView from '../views/home/LoginView.vue'
import ExamDetailView from '../views/ExamDetail.vue'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: ExamListView },
  { path: '/login', component: LoginView },
  { path: '/exam/:exam_id', name: 'ExamDetail', component: ExamDetailView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router