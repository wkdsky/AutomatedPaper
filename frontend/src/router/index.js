import { createRouter, createWebHistory } from 'vue-router'
import ExamListView from '../views/home/examlist.vue'
import LoginView from '../views/home/LoginView.vue'
import ExamDetailView from '../views/ExamDetail.vue'
import PaperDetailView from '../views/paperdetail/PaperDetailview.vue'
import PaperListView from '../views/paperlist/PaperListview.vue'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: ExamListView },
  { path: '/login', component: LoginView },
  { path: '/exam/:exam_id', name: 'ExamDetail', component: ExamDetailView },
  { path: '/exam/:exam_id/papers', name: 'PaperList', component: PaperListView },
  { path: '/paper/:paper_id', component: PaperDetailView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router