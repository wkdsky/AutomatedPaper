# 试卷图片分析和AI阅卷实验平台 (Automated Paper Grading & Analysis Platform)

## 项目简介
本项目是一个基于 **Vue.js** 和 **FastAPI** 的试卷图片分析与AI阅卷实验平台。它旨在为教育场景提供一个基础框架，涵盖了考试管理、学生信息管理、题目与参考答案管理等核心功能，并为 **AI阅卷**、**手写文字识别** 和 **智能评分** 等高级功能预留了接口和界面，供学习者在此基础上进行算法实现和二次开发。

## 系统架构
项目采用前后端分离架构：
- **前端**：基于 **Vue 3** + **Vite** 构建，使用 **Element Plus** 组件库实现现代化的用户界面。负责数据的展示、交互以及考试流程的管理。
- **后端**：基于 **Python 3.9** + **FastAPI** 构建。提供高性能的 RESTful API，处理业务逻辑、数据持久化以及未来的AI算法集成。
- **数据库**：使用 **MySQL** 存储考试信息、学生数据、题目详情及阅卷结果。

## 目录结构说明
```text
AutomatedPaper/
├── backend/                # 后端代码目录
│   ├── app_main.py         # 后端核心入口文件，包含所有API接口定义
│   ├── main.py             # 简易入口示例
│   ├── requirements.txt    # Python依赖包列表
│   └── ...
├── frontend/               # 前端代码目录
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   │   ├── ExamDetail.vue        # 考试详情页（功能入口）
│   │   │   ├── home/                 # 首页相关
│   │   │   └── exam/                 # 考试相关子模块
│   │   │       ├── StudentManager.vue    # 学生管理（已实现）
│   │   │       ├── QuestionManager.vue   # 题目管理（已实现）
│   │   │       ├── AnswerManager.vue     # 学生作答管理（接口）
│   │   │       ├── AIGradingConsole.vue  # AI阅卷控制台（接口）
│   │   │       └── ScoreManager.vue      # 成绩管理（接口）
│   └── ...
├── database_schema.sql     # 数据库初始化脚本
└── README.md               # 项目说明文档
```

## 技术栈
### 后端
- **Language**: Python 3.9
- **Framework**: FastAPI
- **Server**: Uvicorn
- **ORM/DB Driver**: SQLAlchemy, PyMySQL
- **Data Processing**: Pandas, OpenPyXL, Python-docx

### 前端
- **Framework**: Vue.js 3
- **Build Tool**: Vite
- **UI Library**: Element Plus
- **State Management**: Pinia
- **Router**: Vue Router
- **HTTP Client**: Axios

## 快速开始

### 1. 环境准备
确保本地已安装以下环境：
- Python 3.9 (建议使用 Miniconda 或 Anaconda)
- Node.js (LTS 版本)
- MySQL (5.7 或 8.0)

### 2. 数据库配置
1. 登录 MySQL，创建一个名为 `exam_platform` 的数据库。
   ```sql
   CREATE DATABASE exam_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. 运行项目根目录下的 `database_schema.sql` 脚本，初始化表结构。
   ```bash
   mysql -u root -p exam_platform < database_schema.sql
   ```

### 3. 后端部署
1. 进入后端目录：
   ```bash
   cd backend
   ```
2. 创建并激活 Python 虚拟环境（推荐）：
   ```bash
   conda create -n automated_paper python=3.9
   conda activate automated_paper
   ```
3. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```
4. **配置数据库连接**：
   打开 `backend/app_main.py`，找到 `DATABASE_CONFIG` 变量，根据你的本地 MySQL 配置修改 `user` 和 `password`。
   ```python
   # backend/app_main.py
   DATABASE_CONFIG = {
       'host': 'localhost',
       'user': 'root',
       'password': 'your_password',  # <--- 修改这里
       'database': 'exam_platform'
   }
   ```
5. 启动后端服务：
   ```bash
   python app_main.py
   ```
   服务将运行在 `http://0.0.0.0:8001`。

### 4. 前端部署
1. 打开一个新的终端窗口，进入前端目录：
   ```bash
   cd frontend
   ```
2. 安装 Node.js 依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
   访问控制台输出的本地地址（通常是 `http://localhost:5173`）即可使用系统。

## 功能实现状态说明

本项目分为 **"已实现功能"** 和 **"待实现接口"** 两部分，旨在引导学习者完成剩余的核心算法部分。

### ✅ 已完全实现的功能
以下模块已具备完整的前后端逻辑、数据库交互和界面操作：

1. **考试管理**
   - 考试的创建、列表展示、编辑和删除。
   - 考试状态管理（创建中、进行中、已结束）。

2. **学生信息管理 (StudentManager.vue)**
   - **基础CRUD**：添加、修改、删除单个学生信息。
   - **批量导入**：支持从 Excel (`.xlsx`, `.xls`) 或文本文件 (`.txt`, `.csv`) 批量导入学生名单。
   - **关联管理**：将学生分配到特定考试，支持从题库中选择已有学生或导入新学生。
   - **查重逻辑**：自动处理学号冲突和重复添加。

3. **参考答案与题目信息管理 (QuestionManager.vue)**
   - **题目编辑**：支持多种题型（选择、填空、主观题等）的增删改查。
   - **文档导入**：支持解析 Word (`.docx`)、Excel 或 文本文件，自动提取题目内容、分值、参考答案和评分标准。
   - **智能排序**：支持题目的拖拽排序或重新编号。

### 🛠 待实现功能（仅提供界面与接口）
以下模块提供了前端界面框架和后端API占位符，**需要同学们结合AI技术自行实现核心逻辑**：

1. **学生作答管理 (AnswerManager.vue)**
   - **当前状态**：提供界面用于查看学生列表。
   - **待实现**：
     - 上传学生的试卷扫描图片（API已预留文件上传接口）。
     - 实现图片预处理（去噪、矫正）。
     - **关键任务**：实现试卷的**版面分析**，将学生的手写答案区域从整张试卷中切割出来，并关联到对应的题目ID。

2. **AI 阅卷 (AIGradingConsole.vue)**
   - **当前状态**：提供"开始阅卷"的按钮和进度条展示界面。
   - **待实现**：
     - **OCR识别**：识别学生手写文字。
     - **语义比对**：将识别结果与 `reference_answer` 进行比对。
     - **自动打分**：根据相似度或关键词匹配算法计算得分。
     - **人工修正**：允许教师对AI打分结果进行微调。

3. **成绩管理 (ScoreManager.vue)**
   - **当前状态**：提供成绩表格展示的空壳。
   - **待实现**：
     - 汇总所有题目的得分，计算总分。
     - 生成班级成绩分布图表。
     - 导出成绩单为 Excel 文件。

## 贡献与实验
欢迎提交 Pull Request 分享你的 AI 阅卷算法实现！建议在 `backend/` 下新建独立的算法模块（如 `grading_service.py`），并在 `app_main.py` 中调用。
