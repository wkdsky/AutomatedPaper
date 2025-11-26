# 试卷图片分析和AI阅卷实验平台

## 项目概述

这是一个专为教育技术实验设计的简化版考试管理平台，为学生提供了实现AI阅卷功能的基础框架。平台支持考试管理、学生管理、图片上传等基础功能，并预留了标准的AI阅卷扩展接口。

### 核心功能

- ✅ **考试管理**: 创建、编辑、删除考试
- ✅ **学生管理**: 添加、编辑、删除学生信息
- ✅ **图片上传**: 为每个考试上传学生答题图片
- ✅ **成绩展示**: 模拟AI阅卷结果展示
- 🔧 **AI阅卷接口**: 预留标准化接口供学生实现
- 📊 **数据管理**: 完整的数据存储和管理

### 技术栈

**后端**:
- Python 3.7+
- FastAPI - Web框架
- MySQL - 数据库
- SQLAlchemy - ORM框架

**前端**:
- Vue 3 - 前端框架
- Element Plus - UI组件库
- Axios - HTTP客户端

## 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.7+
- Node.js 16+
- MySQL 5.7+

### 2. 数据库配置

创建数据库并初始化表结构：

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE exam_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 执行表结构脚本
mysql -u root -p exam_platform < database_schema.sql
```

修改数据库配置（`backend/src/app_main.py`）:
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # 修改为你的密码
    'database': 'exam_platform'
}
```

### 3. 后端启动

```bash
cd backend

# 安装依赖
pip install fastapi uvicorn sqlalchemy pymysql python-multipart

# 启动后端服务
python src/app_main.py
```

后端服务将运行在 `http://localhost:8000`

### 4. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将运行在 `http://localhost:5173`

## 系统使用指南

### 1. 创建考试

1. 访问首页 `http://localhost:5173`
2. 点击"创建考试"按钮
3. 填写考试信息：
   - 考试名称
   - 考试描述
   - 题目数量
   - 总分
4. 点击"创建"完成

### 2. 管理学生

1. 进入学生管理页面
2. 点击"添加学生"按钮
3. 填写学生信息：
   - 姓名
   - 学号
   - 班级
   - 联系方式

### 3. 考试详情管理

点击考试卡片中的"管理考试"按钮，进入考试详情页面：

#### 学生管理
- 添加学生到考试
- 查看考试中的学生列表
- 移除学生

#### 图片上传
- 选择学生
- 上传该学生的答题图片
- 支持批量上传
- 支持 jpg、png、bmp 格式

#### 题目管理
- 添加考试题目
- 设置题目类型：选择题、填空题、主观题、计算题
- 填写参考答案和分值

#### 成绩查看
- 查看所有学生的成绩
- 查看详细得分情况
- 触发AI阅卷功能

### 4. AI阅卷功能

#### 当前实现（模拟）
点击"开始AI阅卷"按钮，系统将：
1. 模拟AI阅卷过程
2. 为每个学生生成随机分数
3. 展示阅卷结果

#### 学生需要实现的功能
学生需要修改 `backend/src/app_main.py` 文件中的 `simulate_ai_grading_interface` 函数：

```python
async def simulate_ai_grading_interface(exam_id, student_id, images, questions):
    """
    学生需要在这里实现AI阅卷逻辑

    步骤：
    1. 读取学生答题图片
    2. 使用OCR识别图片文字内容
    3. 提取和解析学生答案
    4. 与参考答案对比计算得分
    5. 返回标准格式的评分结果
    """

    # 实现你的AI阅卷代码...

    return {
        "success": True,
        "total_score": 85.5,
        "detail_scores": {
            "1": {"score": 4, "max_score": 4, "confidence": 0.95},
            # 更多题目...
        },
        "confidence": 0.91,
        "processing_time": 1500
    }
```

## 项目结构

```
aupappersys/
├── backend/                    # 后端代码
│   └── src/
│       ├── app_main.py         # 主应用文件（简化版）
│       └── main.py            # 原始应用文件
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── Home.vue       # 首页（考试管理）
│   │   │   ├── ExamDetail.vue # 考试详情
│   │   │   └── StudentManage.vue # 学生管理
│   │   └── router/
│   │       ├── index.js       # 原始路由
│   │       └── index_new.js   # 简化版路由
├── database_schema.sql         # 数据库表结构
├── AI_GRADING_INTERFACE_GUIDE.md # AI阅卷接口指南
└── README.md                   # 项目说明文档
```

## AI阅卷实现指南

详细的技术实现指南请参考：[AI_GRADING_INTERFACE_GUIDE.md](./AI_GRADING_INTERFACE_GUIDE.md)

### 主要实现步骤

1. **图像预处理**
   - 图像去噪、增强对比度
   - 倾斜校正、尺寸标准化

2. **OCR文字识别**
   - 使用百度OCR、腾讯OCR等商业API
   - 或使用Tesseract、PaddleOCR等开源方案

3. **答案提取**
   - 根据题号定位答案区域
   - 解析不同题型的答案格式
   - 答案标准化处理

4. **智能评分**
   - 选择题：精确匹配
   - 填空题：相似度计算
   - 主观题：AI语义分析

5. **结果整合**
   - 计算总分和详细得分
   - 提供置信度指标
   - 生成评分报告

## 实验要求

### 基础要求
1. **OCR识别**: 实现图片文字识别功能
2. **答案提取**: 从识别结果中提取学生答案
3. **评分算法**: 实现基础的评分逻辑
4. **结果输出**: 按照指定格式返回评分结果

### 进阶要求
1. **多题型支持**: 支持选择题、填空题、主观题
2. **准确率优化**: 提高OCR识别和评分准确性
3. **性能优化**: 优化处理速度和并发能力
4. **错误处理**: 完善异常处理和容错机制

### 创新要求
1. **智能预处理**: 图像质量自动优化
2. **多模型融合**: 结合多种OCR和评分模型
3. **学习优化**: 根据人工校对结果优化算法
4. **可视化分析**: 提供评分过程可视化

## API接口文档

### 考试管理
- `GET /api/exams` - 获取考试列表
- `POST /api/exams` - 创建考试
- `PUT /api/exams/{id}` - 更新考试
- `DELETE /api/exams/{id}` - 删除考试

### 学生管理
- `GET /api/students` - 获取学生列表
- `POST /api/students` - 添加学生
- `PUT /api/students/{id}` - 更新学生
- `DELETE /api/students/{id}` - 删除学生

### 图片管理
- `POST /api/exams/{exam_id}/images` - 上传考试图片
- `GET /api/exams/{exam_id}/images` - 获取图片列表

### 题目管理
- `POST /api/exams/{exam_id}/questions` - 添加题目
- `GET /api/exams/{exam_id}/questions` - 获取题目列表

### 成绩管理
- `POST /api/exams/{exam_id}/grade` - 触发AI阅卷
- `GET /api/exams/{exam_id}/scores` - 获取成绩列表

### 系统
- `GET /api/health` - 健康检查
- `GET /api/ai-grading-demo` - AI阅卷接口说明

## 常见问题

### Q: 数据库连接失败怎么办？
A: 检查数据库配置信息，确保MySQL服务已启动，用户名密码正确。

### Q: 前端无法访问后端API怎么办？
A: 检查后端服务是否正常启动（端口8000），检查网络连接。

### Q: 图片上传失败怎么办？
A: 检查上传目录权限，确保目录存在且可写。

### Q: AI阅卷接口如何测试？
A: 可以使用模拟数据进行测试，逐步实现各个功能模块。

## 技术支持

- 项目源码：当前目录
- AI阅卷指南：`AI_GRADING_INTERFACE_GUIDE.md`
- 数据库结构：`database_schema.sql`

## 版本信息

- 版本：1.0.0
- 更新日期：2025-11-25
- 作者：Claude Code

---

**注意**: 这是一个基础平台，学生需要在此基础上实现完整的AI阅卷功能。建议先熟悉平台功能，然后按照接口指南逐步实现AI阅卷算法。

---

## 原系统说明（备份）

以下为原始自动化批改系统的说明，仍可参考：

### 原功能特性
- **视频处理**: 自动从录制的视频中提取答题卡帧
- **智能分组**: 将提取的图片按学生自动分组整理
- **OCR识别**: 使用百度OCR API识别手写文字答案
- **AI答案生成**: 支持多个AI平台自动生成参考答案
- **自动评分**:
  - 选择题：精确匹配评分
  - 填空题：模糊匹配评分（相似度>70%）
  - 大题：支持AI智能评分

### 原技术栈
- **Python 3.x**
- **OpenCV** - 视频处理和图像操作
- **百度OCR API** - 手写文字识别
- **MySQL** - 数据存储
- **正则表达式** - 答案解析
- **difflib** - 文本相似度匹配