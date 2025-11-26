-- 试卷图片分析和AI阅卷实验平台数据库表结构

-- 创建数据库
CREATE DATABASE IF NOT EXISTS exam_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE exam_platform;

-- 考试表
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

-- 学生表
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '学生姓名',
    student_number VARCHAR(50) UNIQUE COMMENT '学号',
    class VARCHAR(100) COMMENT '班级',
    contact_info TEXT COMMENT '联系方式',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '学生信息表';

-- 考试学生关联表
CREATE TABLE exam_students (
    exam_student_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_exam_student (exam_id, student_id)
) COMMENT '考试学生关联表';

-- 题目表
CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50) NOT NULL COMMENT '题型',
    content TEXT COMMENT '题目内容',
    score DECIMAL(5,2) DEFAULT 0 COMMENT '分值',
    reference_answer TEXT COMMENT '参考答案',
    scoring_rules TEXT COMMENT '赋分规则',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '题目信息表';

-- 考试题目关系表
CREATE TABLE exam_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL COMMENT '题目ID',
    exam_id INT NOT NULL COMMENT '考试ID',
    question_order INT NOT NULL COMMENT '题目序号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    UNIQUE KEY unique_exam_question (exam_id, question_id),
    UNIQUE KEY unique_exam_order (exam_id, question_order)
) COMMENT '考试题目关联表';

-- 用户表
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

-- 创建索引优化查询性能
CREATE INDEX idx_exam_students_exam_id ON exam_students(exam_id);
CREATE INDEX idx_exam_students_student_id ON exam_students(student_id);
