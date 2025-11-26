-- 基础教育平台数据库表结构
-- 简化版本，专为试卷图片分析和AI阅卷实验平台设计

-- 创建数据库
CREATE DATABASE IF NOT EXISTS exam_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE exam_platform;

-- 1. 考试表
CREATE TABLE exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_name VARCHAR(255) NOT NULL COMMENT '考试名称',
    description TEXT COMMENT '考试描述',
    exam_date DATETIME NULL COMMENT '开考时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    status ENUM('created', 'uploading', 'processing', 'completed', 'graded') DEFAULT 'created' COMMENT '考试状态',
    total_questions INT DEFAULT NULL COMMENT '总题数（参考答案识别成功后自动设置）',
    total_score INT DEFAULT NULL COMMENT '总分（参考答案识别成功后自动设置）'
) COMMENT '考试信息表';

-- 2. 学生表
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '学生姓名',
    student_number VARCHAR(50) UNIQUE COMMENT '学号',
    class VARCHAR(100) COMMENT '班级',
    contact_info TEXT COMMENT '联系方式',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '学生信息表';

-- 3. 考试学生关联表
CREATE TABLE exam_students (
    exam_student_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_exam_student (exam_id, student_id)
) COMMENT '考试学生关联表';

-- 4. 图片表
CREATE TABLE exam_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    image_path VARCHAR(500) NOT NULL COMMENT '图片存储路径',
    original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    status ENUM('uploaded', 'processing', 'processed', 'error') DEFAULT 'uploaded' COMMENT '处理状态',
    file_size INT COMMENT '文件大小(字节)',
    image_width INT COMMENT '图片宽度',
    image_height INT COMMENT '图片高度',
    processing_result TEXT COMMENT '处理结果(JSON格式)',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
) COMMENT '考试图片表';

-- 5. 题目表（参考答案）
CREATE TABLE questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    question_number INT NOT NULL COMMENT '题号',
    question_type ENUM('choice', 'fill_blank', 'essay', 'calculation') NOT NULL COMMENT '题目类型',
    question_title TEXT COMMENT '题目标题',
    reference_answer TEXT COMMENT '参考答案',
    total_score INT DEFAULT 0 COMMENT '本题满分',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    UNIQUE KEY unique_exam_question (exam_id, question_number)
) COMMENT '题目信息表';

-- 6. 成绩表（AI阅卷结果）
CREATE TABLE scores (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    total_score DECIMAL(5,2) DEFAULT 0 COMMENT '总分',
    max_score DECIMAL(5,2) DEFAULT 100 COMMENT '满分',
    detail_scores JSON COMMENT '详细得分(JSON格式)',
    grading_status ENUM('pending', 'processing', 'completed', 'error') DEFAULT 'pending' COMMENT '阅卷状态',
    graded_at TIMESTAMP NULL COMMENT '阅完成时间',
    ai_model_used VARCHAR(100) COMMENT '使用的AI模型',
    grading_confidence DECIMAL(3,2) COMMENT '阅卷置信度(0-1)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_exam_student_score (exam_id, student_id)
) COMMENT '学生成绩表';

-- 7. AI阅卷接口调用记录表
CREATE TABLE ai_grading_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    image_id INT NOT NULL,
    api_endpoint VARCHAR(255) COMMENT '调用的API端点',
    request_data JSON COMMENT '请求数据',
    response_data JSON COMMENT '响应数据',
    status_code INT COMMENT 'HTTP状态码',
    processing_time INT COMMENT '处理时间(毫秒)',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES exam_images(image_id) ON DELETE CASCADE
) COMMENT 'AI阅卷调用日志表';

-- 8. 系统配置表
CREATE TABLE system_config (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description TEXT COMMENT '配置说明',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '系统配置表';

-- 0. 用户表（新增）
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    role ENUM('admin', 'teacher', 'student') DEFAULT 'teacher' COMMENT '用户角色',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login TIMESTAMP NULL COMMENT '最后登录时间'
) COMMENT '用户信息表';

-- 插入默认管理员用户（密码: admin123）
INSERT INTO users (username, password_hash, email, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpm', 'admin@example.com', 'admin');

-- 插入默认配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('ai_grading_endpoint', 'http://localhost:8080/api/grade', 'AI阅卷接口地址'),
('ai_grading_timeout', '30000', 'AI阅卷接口超时时间(毫秒)'),
('max_image_size', '10485760', '最大图片文件大小(字节)'),
('allowed_image_types', 'jpg,jpeg,png', '允许的图片格式'),
('upload_path', '/uploads/exam_images/', '图片上传存储路径');

-- 创建索引优化查询性能
CREATE INDEX idx_exam_students_exam_id ON exam_students(exam_id);
CREATE INDEX idx_exam_students_student_id ON exam_students(student_id);
CREATE INDEX idx_exam_images_exam_id ON exam_images(exam_id);
CREATE INDEX idx_exam_images_student_id ON exam_images(student_id);
CREATE INDEX idx_exam_images_status ON exam_images(status);
CREATE INDEX idx_questions_exam_id ON questions(exam_id);
CREATE INDEX idx_scores_exam_id ON scores(exam_id);
CREATE INDEX idx_scores_student_id ON scores(student_id);
CREATE INDEX idx_scores_grading_status ON scores(grading_status);
CREATE INDEX idx_ai_grading_logs_exam_id ON ai_grading_logs(exam_id);
CREATE INDEX idx_ai_grading_logs_student_id ON ai_grading_logs(student_id);
CREATE INDEX idx_ai_grading_logs_created_at ON ai_grading_logs(created_at);

-- 9. 试卷表（新增）
CREATE TABLE papers (
    paper_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    seat_number VARCHAR(50) COMMENT '座位号',
    total_score DECIMAL(5,2) DEFAULT 0 COMMENT '总分',
    status ENUM('ungraded', 'partial', 'graded', 'error') DEFAULT 'ungraded' COMMENT '阅卷状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_exam_student_paper (exam_id, student_id)
) COMMENT '试卷信息表';

-- 10. 试卷详情表（新增）
CREATE TABLE paper_details (
    detail_id INT AUTO_INCREMENT PRIMARY KEY,
    paper_id INT NOT NULL,
    question_number INT NOT NULL COMMENT '题号',
    answer_text TEXT COMMENT '学生答案',
    score DECIMAL(5,2) COMMENT '得分',
    total_score DECIMAL(5,2) DEFAULT 0 COMMENT '本题满分',
    confidence DECIMAL(3,2) COMMENT '置信度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE,
    UNIQUE KEY unique_paper_question (paper_id, question_number)
) COMMENT '试卷详情表';

-- 11. 参考答案表（新增）
CREATE TABLE reference_answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    question_number INT NOT NULL COMMENT '题号',
    answer_text TEXT NOT NULL COMMENT '标准答案',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    UNIQUE KEY unique_exam_question_answer (exam_id, question_number)
) COMMENT '标准答案表';

-- 创建新增表的索引
CREATE INDEX idx_papers_exam_id ON papers(exam_id);
CREATE INDEX idx_papers_student_id ON papers(student_id);
CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_paper_details_paper_id ON paper_details(paper_id);
CREATE INDEX idx_paper_details_question_number ON paper_details(question_number);
CREATE INDEX idx_reference_answers_exam_id ON reference_answers(exam_id);
CREATE INDEX idx_reference_answers_question_number ON reference_answers(question_number);