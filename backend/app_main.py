"""
简化版考试管理系统后端API
专为试卷图片分析和AI阅卷实验平台设计

功能包括：
1. 考试管理 - 创建、查看、更新考试
2. 学生管理 - 添加、查看、更新学生信息
3. 图片上传 - 为每个考试上传学生答题图片
4. 成绩展示 - 模拟AI阅卷结果展示
5. 扩展接口 - 为AI阅卷功能预留标准化接口

作者：Claude Code
日期：2025-11-25
"""


import os
import shutil
import json
import time
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any
import hashlib
import secrets
import pandas as pd
import io
import docx
import re

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="考试管理平台API", version="1.0.0", description="试卷图片分析和AI阅卷实验平台")

# 允许本地前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # 请根据实际情况修改，如果无密码则留空
    'database': 'exam_platform'
}

# 创建数据库连接
engine = create_engine(
    f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:3306/{DATABASE_CONFIG['database']}",
    echo=True
)

# 文件上传配置
UPLOAD_DIR = "/home/wkd/aupappersys/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================== Pydantic模型定义 ====================

class ExamRequest(BaseModel):
    exam_name: str
    description: Optional[str] = ""
    exam_date: Optional[str] = None
    total_questions: Optional[int] = None
    total_score: Optional[int] = None

class ExamUpdate(BaseModel):
    exam_name: Optional[str] = None
    description: Optional[str] = None
    exam_date: Optional[str] = None
    total_questions: Optional[int] = None
    total_score: Optional[int] = None
    status: Optional[str] = None

class StudentRequest(BaseModel):
    name: str
    student_number: Optional[str] = ""
    class_name: Optional[str] = ""
    contact_info: Optional[str] = ""

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    student_number: Optional[str] = None
    class_name: Optional[str] = None
    contact_info: Optional[str] = None

class QuestionRequest(BaseModel):
    question_order: int
    question_type: Optional[str] = ""
    content: str
    score: float
    reference_answer: str
    scoring_rules: Optional[str] = ""

class AIGradingRequest(BaseModel):
    """AI阅卷请求模型 - 供学生实现接口使用"""
    exam_id: int
    student_id: int
    image_ids: List[int]
    questions: List[Dict[str, Any]]  # 题目信息
    api_endpoint: Optional[str] = ""  # AI接口地址
    api_config: Optional[Dict[str, Any]] = {}  # AI接口配置

class AIGradingResponse(BaseModel):
    """AI阅卷响应模型 - 供学生实现接口使用"""
    success: bool
    total_score: float
    detail_scores: Dict[str, Any]  # 详细得分
    confidence: Optional[float] = 0.0  # 置信度
    processing_time: Optional[int] = 0  # 处理时间(毫秒)
    error_message: Optional[str] = ""

class UserRegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str
    password: str
    email: Optional[str] = None

class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str

class UserResponse(BaseModel):
    """用户响应模型"""
    user_id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class BatchStudentRequest(BaseModel):
    """批量添加学生请求模型"""
    students: List[StudentRequest]

# ==================== 用户认证API ====================

def hash_password(password: str) -> str:
    """密码哈希函数"""
    # 使用简单的SHA-256哈希（生产环境建议使用bcrypt）
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed_password

@app.post("/api/register")
async def register_user(user: UserRegisterRequest):
    """用户注册"""
    try:
        # 验证输入
        if len(user.username) < 1 or len(user.username) > 50:
            raise HTTPException(status_code=400, detail="用户名长度必须在1-50字符之间")
        if len(user.password) < 1 or len(user.password) > 255:
            raise HTTPException(status_code=400, detail="密码长度必须在1-255字符之间")

        with engine.connect() as conn:
            # 检查用户名是否已存在
            existing_user = conn.execute(
                text("SELECT user_id FROM users WHERE username = :username"),
                {"username": user.username}
            ).fetchone()

            if existing_user:
                raise HTTPException(status_code=400, detail="用户名已存在")

            # 检查邮箱是否已存在（如果提供了邮箱）
            if user.email:
                existing_email = conn.execute(
                    text("SELECT user_id FROM users WHERE email = :email"),
                    {"email": user.email}
                ).fetchone()

                if existing_email:
                    raise HTTPException(status_code=400, detail="邮箱已被使用")

            # 创建新用户
            password_hash = hash_password(user.password)
            result = conn.execute(
                text("""
                INSERT INTO users (username, password_hash, email, role)
                VALUES (:username, :password_hash, :email, 'teacher')
                """),
                {
                    "username": user.username,
                    "password_hash": password_hash,
                    "email": user.email
                }
            )
            conn.commit()
            user_id = result.lastrowid

            return {
                "code": 1,
                "msg": "注册成功",
                "data": {"user_id": user_id}
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail="注册失败，请重试")

@app.post("/api/login")
async def login_user(user: UserLoginRequest):
    """用户登录"""
    try:
        if not user.username or not user.password:
            raise HTTPException(status_code=400, detail="用户名和密码不能为空")

        with engine.connect() as conn:
            # 查找用户
            result = conn.execute(
                text("""
                SELECT user_id, username, password_hash, email, role, is_active, last_login
                FROM users WHERE username = :username
                """),
                {"username": user.username}
            )
            user_data = result.fetchone()

            if not user_data:
                raise HTTPException(status_code=401, detail="用户名或密码错误")

            user_dict = dict(zip(result.keys(), user_data))

            # 检查用户是否激活
            if not user_dict['is_active']:
                raise HTTPException(status_code=401, detail="用户账号已被禁用")

            # 验证密码
            if not verify_password(user.password, user_dict['password_hash']):
                raise HTTPException(status_code=401, detail="用户名或密码错误")

            # 更新最后登录时间
            conn.execute(
                text("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = :user_id"),
                {"user_id": user_dict['user_id']}
            )
            conn.commit()

            # 返回用户信息（不包含密码）
            return {
                "code": 1,
                "msg": "登录成功",
                "data": {
                    "user_id": user_dict['user_id'],
                    "username": user_dict['username'],
                    "email": user_dict['email'],
                    "role": user_dict['role']
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="登录失败，请重试")

# ==================== 考试管理API ====================

@app.get("/api/exams")
def get_exams():
    """获取所有考试列表"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM exams ORDER BY created_at DESC"))
            rows = result.fetchall()
            exams = []
            for row in rows:
                exam = {
                    'exam_id': row.exam_id,
                    'exam_name': row.exam_name,
                    'description': row.description,
                    'exam_date': row.exam_date.isoformat() if row.exam_date else None,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                    'status': row.status,
                    'total_questions': row.total_questions,
                    'total_score': row.total_score
                }
                exams.append(exam)

            # 获取每个考试的学生数量
            for exam in exams:
                student_count = conn.execute(
                    text("SELECT COUNT(*) as count FROM exam_students WHERE exam_id = :exam_id"),
                    {"exam_id": exam['exam_id']}
                ).scalar()
                exam['student_count'] = student_count

            return {"code": 1, "msg": "获取成功", "data": exams}
    except Exception as e:
        logger.error(f"获取考试列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试列表失败: {str(e)}")

@app.post("/api/exams")
def create_exam(exam: ExamRequest):
    """创建新考试"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                INSERT INTO exams (exam_name, description, exam_date, total_questions, total_score, status)
                VALUES (:exam_name, :description, :exam_date, :total_questions, :total_score, 'created')
                """),
                {
                    "exam_name": exam.exam_name,
                    "description": exam.description,
                    "exam_date": exam.exam_date,
                    "total_questions": exam.total_questions,
                    "total_score": exam.total_score
                }
            )
            conn.commit()
            exam_id = result.lastrowid

            return {"code": 1, "msg": "创建成功", "data": {"exam_id": exam_id}}
    except Exception as e:
        logger.error(f"创建考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建考试失败: {str(e)}")

@app.put("/api/exams/{exam_id}")
def update_exam(exam_id: int, exam: ExamUpdate):
    """更新考试信息"""
    try:
        with engine.connect() as conn:
            # 构建动态更新语句
            update_fields = []
            update_params = {"exam_id": exam_id}

            if exam.exam_name is not None:
                update_fields.append("exam_name = :exam_name")
                update_params["exam_name"] = exam.exam_name
            if exam.description is not None:
                update_fields.append("description = :description")
                update_params["description"] = exam.description
            if exam.exam_date is not None:
                update_fields.append("exam_date = :exam_date")
                update_params["exam_date"] = exam.exam_date
            if exam.total_questions is not None:
                update_fields.append("total_questions = :total_questions")
                update_params["total_questions"] = exam.total_questions
            if exam.total_score is not None:
                update_fields.append("total_score = :total_score")
                update_params["total_score"] = exam.total_score
            if exam.status is not None:
                update_fields.append("status = :status")
                update_params["status"] = exam.status
                update_fields.append("updated_at = CURRENT_TIMESTAMP")

            if not update_fields:
                return {"code": 0, "msg": "没有更新字段"}

            query = f"UPDATE exams SET {', '.join(update_fields)} WHERE exam_id = :exam_id"
            conn.execute(text(query), update_params)
            conn.commit()

            return {"code": 1, "msg": "更新成功"}
    except Exception as e:
        logger.error(f"更新考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新考试失败: {str(e)}")

@app.delete("/api/exams/{exam_id}")
def delete_exam(exam_id: int):
    """删除考试"""
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id})
            conn.commit()
            return {"code": 1, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除考试失败: {str(e)}")

# ==================== 学生管理API ====================

@app.get("/api/students")
def get_students():
    """获取所有学生列表"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM students ORDER BY name"))
            students = [dict(row) for row in result.fetchall()]
            return {"code": 1, "msg": "获取成功", "data": students}
    except Exception as e:
        logger.error(f"获取学生列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生列表失败: {str(e)}")

@app.post("/api/students")
def create_student(student: StudentRequest):
    """添加新学生"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                INSERT INTO students (name, student_number, class, contact_info)
                VALUES (:name, :student_number, :class_name, :contact_info)
                """),
                {
                    "name": student.name,
                    "student_number": student.student_number,
                    "class_name": student.class_name,
                    "contact_info": student.contact_info
                }
            )
            conn.commit()
            student_id = result.lastrowid

            return {"code": 1, "msg": "添加成功", "data": {"student_id": student_id}}
    except Exception as e:
        logger.error(f"添加学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加学生失败: {str(e)}")

@app.put("/api/students/{student_id}")
def update_student(student_id: int, student: StudentUpdate):
    """更新学生信息"""
    try:
        with engine.connect() as conn:
            # Check if student number exists for another student
            if student.student_number is not None:
                existing = conn.execute(
                    text("SELECT student_id FROM students WHERE student_number = :student_number AND student_id != :student_id"),
                    {"student_number": student.student_number, "student_id": student_id}
                ).fetchone()
                if existing:
                    raise HTTPException(status_code=400, detail=f"学号 {student.student_number} 已存在")

            update_fields = []
            update_params = {"student_id": student_id}

            if student.name is not None:
                update_fields.append("name = :name")
                update_params["name"] = student.name
            if student.student_number is not None:
                update_fields.append("student_number = :student_number")
                update_params["student_number"] = student.student_number
            if student.class_name is not None:
                update_fields.append("class = :class_name")
                update_params["class_name"] = student.class_name
            if student.contact_info is not None:
                update_fields.append("contact_info = :contact_info")
                update_params["contact_info"] = student.contact_info

            if not update_fields:
                return {"code": 0, "msg": "没有更新字段"}

            query = f"UPDATE students SET {', '.join(update_fields)} WHERE student_id = :student_id"
            conn.execute(text(query), update_params)
            conn.commit()

            return {"code": 1, "msg": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新学生失败: {str(e)}")

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int):
    """删除学生"""
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM students WHERE student_id = :student_id"), {"student_id": student_id})
            conn.commit()
            return {"code": 1, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除学生失败: {str(e)}")

# ==================== 考试学生关联API ====================

class BatchAddStudentsRequest(BaseModel):
    """批量添加学生请求模型"""
    students: List[Dict[str, str]]

@app.post("/api/exams/{exam_id}/batch-add-students")
async def batch_add_students_to_exam(exam_id: int, request: BatchStudentRequest):
    """批量添加学生到考试"""
    try:
        # 验证考试是否存在
        with engine.connect() as conn:
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

        added_count = 0
        errors = []

        with engine.connect() as conn:
            for student_data in request.students:
                try:
                    student_number = student_data.student_number
                    name = student_data.name
                    class_name = student_data.class_name
                    contact_info = student_data.contact_info

                    if not student_number:
                        errors.append(f"学号缺失: {student_data.name or '未知姓名'}")
                        continue
                    
                    if not name:
                        errors.append(f"姓名缺失: 学号 {student_number}")
                        continue

                    # 检查学生是否已存在
                    existing_student = conn.execute(
                        text("SELECT student_id, name FROM students WHERE student_number = :student_number"),
                        {"student_number": student_number}
                    ).fetchone()

                    if existing_student:
                        # 存在同名学号，检查姓名是否一致
                        db_student_id, db_name = existing_student
                        if db_name != name:
                            errors.append(f"学号冲突: 学号 {student_number} 已存在且属于学生 {db_name}，与当前 {name} 不符")
                            continue
                        student_id = db_student_id
                    else:
                        # 创建新学生
                        insert_result = conn.execute(
                            text("""
                                INSERT INTO students (name, student_number, class, contact_info)
                                VALUES (:name, :student_number, :class_name, :contact_info)
                            """),
                            {
                                "name": name,
                                "student_number": student_number,
                                "class_name": class_name,
                                "contact_info": contact_info
                            }
                        )
                        student_id = insert_result.lastrowid

                    # 检查是否已经在考试中
                    existing_exam_student = conn.execute(
                        text("SELECT * FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                        {"exam_id": exam_id, "student_id": student_id}
                    ).fetchone()

                    if not existing_exam_student:
                        # 添加学生到考试
                        conn.execute(
                            text("INSERT INTO exam_students (exam_id, student_id) VALUES (:exam_id, :student_id)"),
                            {"exam_id": exam_id, "student_id": student_id}
                        )
                        added_count += 1
                    else:
                        errors.append(f"重复添加: 学生 {name} ({student_number}) 已在考试中")

                except Exception as e:
                    errors.append(f"系统错误 {name}: {str(e)}")
                    continue

            conn.commit()

        return {
            "code": 1,
            "msg": f"批量添加成功，共添加 {added_count} 个学生",
            "data": {
                "added_count": added_count,
                "errors": errors
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量添加学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量添加学生失败: {str(e)}")

@app.post("/api/exams/{exam_id}/students")
def add_student_to_exam(exam_id: int, student_id: int = Body(...)):
    """将学生添加到考试中"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 检查学生是否存在
            student_result = conn.execute(text("SELECT student_id FROM students WHERE student_id = :student_id"), {"student_id": student_id}).fetchone()
            if not student_result:
                raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

            # 添加关联
            try:
                conn.execute(
                    text("INSERT INTO exam_students (exam_id, student_id) VALUES (:exam_id, :student_id)"),
                    {"exam_id": exam_id, "student_id": student_id}
                )
                conn.commit()
                return {"code": 1, "msg": "添加成功"}
            except:
                # 如果已存在，返回成功
                return {"code": 1, "msg": "学生已在该考试中"}
    except Exception as e:
        logger.error(f"添加学生到考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加学生到考试失败: {str(e)}")

@app.delete("/api/exams/{exam_id}/students/{student_id}")
def remove_student_from_exam(exam_id: int, student_id: int):
    """将学生从考试中移除"""
    try:
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                {"exam_id": exam_id, "student_id": student_id}
            )
            conn.commit()
            return {"code": 1, "msg": "移除成功"}
    except Exception as e:
        logger.error(f"移除学生从考试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"移除学生从考试失败: {str(e)}")

@app.get("/api/exams/{exam_id}/students")
def get_exam_students(exam_id: int):
    """获取考试的学生列表"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 获取考试的所有学生
            result = conn.execute(
                text("""
                SELECT s.student_id, s.name, s.student_number, s.class as class_name, s.contact_info, s.created_at, s.updated_at, es.sort_order
                FROM students s
                INNER JOIN exam_students es ON s.student_id = es.student_id
                WHERE es.exam_id = :exam_id
                ORDER BY es.sort_order ASC, s.student_number ASC
                """),
                {"exam_id": exam_id}
            )
            students = []
            for row in result.fetchall():
                student = {
                    'student_id': row.student_id,
                    'name': row.name,
                    'student_number': row.student_number,
                    'class_name': row.class_name,
                    'contact_info': row.contact_info,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                    'sort_order': row.sort_order
                }
                students.append(student)

            return {"code": 1, "msg": "获取成功", "data": students}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考试学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试学生失败: {str(e)}")

@app.post("/api/exams/{exam_id}/students/reorder")
def reorder_exam_students(exam_id: int, student_ids: List[int] = Body(...)):
    """重新排序考试学生"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 批量更新排序
            for index, student_id in enumerate(student_ids):
                conn.execute(
                    text("UPDATE exam_students SET sort_order = :sort_order WHERE exam_id = :exam_id AND student_id = :student_id"),
                    {"sort_order": index + 1, "exam_id": exam_id, "student_id": student_id}
                )
            
            conn.commit()
            return {"code": 1, "msg": "排序更新成功"}
    except Exception as e:
        logger.error(f"更新学生排序失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新学生排序失败: {str(e)}")

@app.get("/api/exams/{exam_id}/available-students")
def get_available_students(exam_id: int, search: Optional[str] = None):
    """获取未分配到该考试的学生列表"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 构建查询条件
            where_clause = "WHERE s.student_id NOT IN (SELECT es.student_id FROM exam_students es WHERE es.exam_id = :exam_id)"
            params = {"exam_id": exam_id}

            if search:
                where_clause += " AND (s.name LIKE :search OR s.student_number LIKE :search OR s.class LIKE :search)"
                params.update({"search": f"%{search}%"})

            # 获取未分配到该考试的学生
            result = conn.execute(
                text(f"""
                SELECT s.student_id, s.name, s.student_number, s.class as class_name, s.contact_info
                FROM students s
                {where_clause}
                ORDER BY s.name
                """),
                params
            )
            students = []
            for row in result.fetchall():
                student = {
                    'student_id': row.student_id,
                    'name': row.name,
                    'student_number': row.student_number,
                    'class_name': row.class_name,
                    'contact_info': row.contact_info
                }
                students.append(student)

            return {"code": 1, "msg": "获取成功", "data": students}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取可用学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可用学生失败: {str(e)}")

@app.post("/api/exams/{exam_id}/import-students")
async def import_students_from_file(exam_id: int, file: UploadFile = File(...)):
    """从文件导入学生信息到考试"""
    try:
        # 验证考试是否存在
        with engine.connect() as conn:
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

        # 验证文件类型
        file_extension = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = {".xlsx", ".xls", ".txt", ".csv"}
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的文件格式。支持: xlsx, xls, txt, csv")

        # 读取文件内容
        content = await file.read()
        students_to_add = []

        try:
            if file_extension in {".xlsx", ".xls"}:
                # 处理Excel文件
                df = pd.read_excel(io.BytesIO(content))
                # 假设列顺序为：学号, 班级, 姓名, 联系方式
                for _, row in df.iterrows():
                    if len(row) >= 3 and pd.notna(row.iloc[0]) and pd.notna(row.iloc[2]):
                        students_to_add.append({
                            "student_number": str(row.iloc[0]).strip(),
                            "class": str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "",
                            "name": str(row.iloc[2]).strip(),
                            "contact_info": str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                        })
            else:
                # 处理文本文件
                text_content = content.decode('utf-8')
                lines = text_content.strip().split('\n')

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 支持逗号和制表符分隔
                    if '\t' in line:
                        parts = line.split('\t')
                    else:
                        parts = line.split(',')

                    if len(parts) >= 3 and parts[0].strip() and parts[2].strip():
                        students_to_add.append({
                            "student_number": parts[0].strip(),
                            "class": parts[1].strip(),
                            "name": parts[2].strip(),
                            "contact_info": parts[3].strip() if len(parts) > 3 else ""
                        })
        except Exception as parse_error:
            raise HTTPException(status_code=400, detail=f"文件解析失败: {str(parse_error)}")

        if not students_to_add:
            raise HTTPException(status_code=400, detail="文件中没有找到有效的学生信息")

        # 添加学生到数据库
        imported_count = 0
        with engine.connect() as conn:
            for student_data in students_to_add:
                try:
                    # 检查学号是否已存在
                    existing = conn.execute(
                        text("SELECT student_id FROM students WHERE student_number = :student_number"),
                        {"student_number": student_data["student_number"]}
                    ).fetchone()

                    student_id = None
                    if not existing:
                        # 创建新学生
                        result = conn.execute(
                            text("""INSERT INTO students (name, student_number, class, contact_info)
                                 VALUES (:name, :student_number, :class, :contact_info)"""),
                            {
                                "name": student_data["name"],
                                "student_number": student_data["student_number"],
                                "class": student_data.get("class", ""),
                                "contact_info": student_data.get("contact_info", "")
                            }
                        )
                        student_id = result.lastrowid
                    else:
                        student_id = existing[0]

                    # 将学生添加到考试（如果还没有）
                    existing_relation = conn.execute(
                        text("SELECT * FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                        {"exam_id": exam_id, "student_id": student_id}
                    ).fetchone()

                    if not existing_relation:
                        conn.execute(
                            text("INSERT INTO exam_students (exam_id, student_id) VALUES (:exam_id, :student_id)"),
                            {"exam_id": exam_id, "student_id": student_id}
                        )
                        imported_count += 1

                    conn.commit()
                except Exception as student_error:
                    logger.warning(f"添加学生失败 {student_data}: {str(student_error)}")
                    continue

        return {"code": 1, "msg": "导入成功", "data": {"imported_count": imported_count}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件导入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件导入失败: {str(e)}")

@app.post("/api/exams/{exam_id}/add-existing-students")
def add_existing_students_to_exam(exam_id: int, student_ids: List[int] = Body(...)):
    """添加已存在的学生到考试"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            added_count = 0
            already_in_exam = []

            for student_id in student_ids:
                try:
                    # 检查学生是否存在
                    student_result = conn.execute(
                        text("SELECT student_id FROM students WHERE student_id = :student_id"),
                        {"student_id": student_id}
                    ).fetchone()

                    if not student_result:
                        logger.warning(f"学生 {student_id} 不存在，跳过")
                        continue

                    # 检查是否已经在该考试中
                    existing_relation = conn.execute(
                        text("SELECT * FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                        {"exam_id": exam_id, "student_id": student_id}
                    ).fetchone()

                    if existing_relation:
                        already_in_exam.append(student_id)
                        continue

                    # 添加学生到考试
                    conn.execute(
                        text("INSERT INTO exam_students (exam_id, student_id) VALUES (:exam_id, :student_id)"),
                        {"exam_id": exam_id, "student_id": student_id}
                    )
                    added_count += 1

                except Exception as student_error:
                    logger.warning(f"添加学生失败 {student_id}: {str(student_error)}")
                    continue

            conn.commit()

            return {"code": 1, "msg": f"成功添加 {added_count} 个学生", "data": {"added_count": added_count}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加已存在学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加已存在学生失败: {str(e)}")

@app.post("/api/exams/{exam_id}/students/remove-batch")
def remove_students_batch(exam_id: int, student_ids: List[int] = Body(...)):
    """批量删除学生从考试"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            removed_count = 0

            for student_id in student_ids:
                try:
                    # 直接尝试删除关联
                    result = conn.execute(
                        text("DELETE FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                        {"exam_id": exam_id, "student_id": student_id}
                    )
                    if result.rowcount > 0:
                        removed_count += 1

                except Exception as student_error:
                    logger.warning(f"删除学生失败 {student_id}: {str(student_error)}")
                    continue

            conn.commit()

            return {"code": 1, "msg": "删除成功", "data": {"removed_count": removed_count}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除学生失败: {str(e)}")

@app.post("/api/exams/{exam_id}/add-existing-students")
def add_existing_students_to_exam(exam_id: int, student_ids: List[int] = Body(...)):
    """添加已存在的学生到考试"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            added_count = 0
            already_in_exam = []

            for student_id in student_ids:
                try:
                    # 检查学生是否存在
                    student_result = conn.execute(
                        text("SELECT student_id FROM students WHERE student_id = :student_id"),
                        {"student_id": student_id}
                    ).fetchone()

                    if not student_result:
                        logger.warning(f"学生 {student_id} 不存在，跳过")
                        continue

                    # 检查是否已经在该考试中
                    existing_relation = conn.execute(
                        text("SELECT * FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                        {"exam_id": exam_id, "student_id": student_id}
                    ).fetchone()

                    if existing_relation:
                        already_in_exam.append(student_id)
                        continue

                    # 添加学生到考试
                    conn.execute(
                        text("INSERT INTO exam_students (exam_id, student_id) VALUES (:exam_id, :student_id)"),
                        {"exam_id": exam_id, "student_id": student_id}
                    )
                    added_count += 1

                except Exception as student_error:
                    logger.warning(f"添加学生失败 {student_id}: {str(student_error)}")
                    continue

            conn.commit()

            return {"code": 1, "msg": f"成功添加 {added_count} 个学生", "data": {"added_count": added_count}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加已存在学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加已存在学生失败: {str(e)}")
    """批量删除学生从考试"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            removed_count = 0
            for student_id in student_ids:
                try:
                    # 检查学生是否存在
                    student_result = conn.execute(text("SELECT student_id FROM students WHERE student_id = :student_id"), {"student_id": student_id}).fetchone()

                    if not student_result:
                        logger.warning(f"学生 {student_id} 不存在，跳过")
                        continue

                    # 检查是否已经在该考试中
                    existing_relation = conn.execute(
                        text("SELECT * FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                        {"exam_id": exam_id, "student_id": student_id}
                    ).fetchone()

                    if existing_relation:
                        already_in_exam.append(student_id)
                        continue

                    # 从考试中移除学生
                    conn.execute(text("DELETE FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"), {"exam_id": exam_id, "student_id": student_id})

                    # 删除学生记录（如果存在）
                    delete_student_result = conn.execute(
                        text("DELETE FROM students WHERE student_id = :student_id"),
                        {"student_id": student_id}
                    )

                    if delete_student_result.rowcount > 0:
                        logger.info(f"同时删除了学生 {student_id} 的学生记录")
                        removed_count += 1

                except Exception as student_error:
                    logger.warning(f"删除学生失败 {student_id}: {str(student_error)}")
                    continue

            conn.commit()

            return {"code": 1, "msg": f"成功删除 {removed_count} 个学生", "data": {"removed_count": removed_count, "deleted_students": deleted_students}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除学生失败: {str(e)}")
    """批量添加学生到考试"""
    try:
        # 验证考试是否存在
        with engine.connect() as conn:
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

        added_count = 0
        with engine.connect() as conn:
            for student_data in request.students:
                try:
                    # 检查学号是否已存在
                    existing = conn.execute(
                        text("SELECT student_id FROM students WHERE student_number = :student_number"),
                        {"student_number": student_data.student_number}
                    ).fetchone()

                    student_id = None
                    if not existing:
                        # 创建新学生
                        result = conn.execute(
                            text("""INSERT INTO students (name, student_number, class)
                                 VALUES (:name, :student_number, :class)"""),
                            {
                                "name": student_data.name,
                                "student_number": student_data.student_number,
                                "class": student_data.class_name
                            }
                        )
                        student_id = result.lastrowid
                    else:
                        student_id = existing[0]

                    # 将学生添加到考试（如果还没有）
                    existing_relation = conn.execute(
                        text("SELECT * FROM exam_students WHERE exam_id = :exam_id AND student_id = :student_id"),
                        {"exam_id": exam_id, "student_id": student_id}
                    ).fetchone()

                    if not existing_relation:
                        conn.execute(
                            text("INSERT INTO exam_students (exam_id, student_id) VALUES (:exam_id, :student_id)"),
                            {"exam_id": exam_id, "student_id": student_id}
                        )
                        added_count += 1

                    conn.commit()
                except Exception as student_error:
                    logger.warning(f"添加学生失败 {student_data}: {str(student_error)}")
                    continue

        return {"code": 1, "msg": "批量添加成功", "data": {"added_count": added_count}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量添加学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量添加学生失败: {str(e)}")

# ==================== 图片管理API ====================

@app.post("/api/exams/{exam_id}/images")
async def upload_exam_images(exam_id: int, student_id: int = Form(...), files: List[UploadFile] = File(...)):
    """上传考试图片"""
    try:
        # 验证考试和学生是否存在
        with engine.connect() as conn:
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            student_result = conn.execute(text("SELECT student_id FROM students WHERE student_id = :student_id"), {"student_id": student_id}).fetchone()
            if not student_result:
                raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

        # 创建考试专用目录
        exam_upload_dir = os.path.join(UPLOAD_DIR, f"exam_{exam_id}", f"student_{student_id}")
        os.makedirs(exam_upload_dir, exist_ok=True)

        uploaded_files = []

        with engine.connect() as conn:
            for file in files:
                # 验证文件扩展名
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")

                # 生成唯一文件名
                timestamp = int(time.time())
                unique_filename = f"{timestamp}_{file.filename}"
                file_path = os.path.join(exam_upload_dir, unique_filename)

                # 保存文件
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # 记录到数据库
                result = conn.execute(
                    text("""
                    INSERT INTO exam_images (exam_id, student_id, image_path, original_filename, file_size, status)
                    VALUES (:exam_id, :student_id, :image_path, :original_filename, :file_size, 'uploaded')
                    """),
                    {
                        "exam_id": exam_id,
                        "student_id": student_id,
                        "image_path": file_path,
                        "original_filename": file.filename,
                        "file_size": os.path.getsize(file_path)
                    }
                )
                conn.commit()
                image_id = result.lastrowid

                uploaded_files.append({
                    "image_id": image_id,
                    "filename": file.filename,
                    "path": file_path
                })

        return {
            "code": 1,
            "msg": f"成功上传 {len(uploaded_files)} 个文件",
            "data": uploaded_files
        }
    except Exception as e:
        logger.error(f"上传图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传图片失败: {str(e)}")

@app.get("/api/exams/{exam_id}/images")
def get_exam_images(exam_id: int, student_id: Optional[int] = None):
    """获取考试图片列表"""
    try:
        with engine.connect() as conn:
            query = """
            SELECT ei.*, s.name as student_name
            FROM exam_images ei
            LEFT JOIN students s ON ei.student_id = s.student_id
            WHERE ei.exam_id = :exam_id
            """
            params = {"exam_id": exam_id}

            if student_id is not None:
                query += " AND ei.student_id = :student_id"
                params["student_id"] = student_id

            query += " ORDER BY ei.upload_time DESC"

            result = conn.execute(text(query), params)
            images = [dict(row) for row in result.fetchall()]

            return {"code": 1, "msg": "获取成功", "data": images}
    except Exception as e:
        logger.error(f"获取考试图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试图片失败: {str(e)}")

# ==================== 题目管理API ====================

@app.post("/api/exams/{exam_id}/questions")
def create_question(exam_id: int, question: QuestionRequest):
    """为考试添加题目"""
    try:
        with engine.connect() as conn:
            # 开启事务
            trans = conn.begin()
            try:
                # 1. 插入题目信息
                result = conn.execute(
                    text("""
                    INSERT INTO questions (type, content, score, reference_answer, scoring_rules)
                    VALUES (:type, :content, :score, :reference_answer, :scoring_rules)
                    """),
                    {
                        "type": question.question_type,
                        "content": question.content,
                        "score": question.score,
                        "reference_answer": question.reference_answer,
                        "scoring_rules": question.scoring_rules
                    }
                )
                question_id = result.lastrowid

                # 2. 插入考试题目关联
                conn.execute(
                    text("""
                    INSERT INTO exam_questions (exam_id, question_id, question_order)
                    VALUES (:exam_id, :question_id, :question_order)
                    """),
                    {
                        "exam_id": exam_id,
                        "question_id": question_id,
                        "question_order": question.question_order
                    }
                )
                
                trans.commit()
                return {"code": 1, "msg": "添加成功", "data": {"question_id": question_id}}
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        logger.error(f"添加题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加题目失败: {str(e)}")

@app.get("/api/exams/{exam_id}/questions")
def get_exam_questions(exam_id: int):
    """获取考试题目列表"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT q.*, eq.question_order 
                FROM questions q
                JOIN exam_questions eq ON q.id = eq.question_id
                WHERE eq.exam_id = :exam_id 
                ORDER BY eq.question_order
                """),
                {"exam_id": exam_id}
            )
            questions = []
            for row in result.fetchall():
                q = {
                    "id": row.id,
                    "question_order": row.question_order,
                    "type": row.type,
                    "content": row.content,
                    "score": float(row.score) if row.score is not None else 0,
                    "reference_answer": row.reference_answer,
                    "scoring_rules": row.scoring_rules,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
                questions.append(q)

            return {"code": 1, "msg": "获取成功", "data": questions}
    except Exception as e:
        logger.error(f"获取考试题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试题目失败: {str(e)}")

@app.post("/api/exams/{exam_id}/questions/reorder")
def reorder_exam_questions(exam_id: int, question_ids: List[int] = Body(...)):
    """重新排序考试题目"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 批量更新排序
            for index, question_id in enumerate(question_ids):
                conn.execute(
                    text("UPDATE exam_questions SET question_order = :question_order WHERE exam_id = :exam_id AND question_id = :question_id"),
                    {"question_order": index + 1, "exam_id": exam_id, "question_id": question_id}
                )
            
            conn.commit()
            return {"code": 1, "msg": "排序更新成功"}
    except Exception as e:
        logger.error(f"更新题目排序失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新题目排序失败: {str(e)}")

@app.post("/api/exams/{exam_id}/import-questions")
async def import_questions_from_file(exam_id: int, file: UploadFile = File(...)):
    """从文件导入题目"""
    try:
        # 验证考试是否存在
        with engine.connect() as conn:
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")
            
            # 获取当前最大序号，用于追加
            max_order_res = conn.execute(text("SELECT MAX(question_order) FROM exam_questions WHERE exam_id = :exam_id"), {"exam_id": exam_id}).scalar()
            current_max_order = max_order_res if max_order_res is not None else 0

        filename = file.filename.lower()
        file_ext = os.path.splitext(filename)[1]
        content = await file.read()
        questions_to_add = []

        # 定义分隔符
        SEPARATOR = "@@@"

        try:
            if file_ext == '.docx':
                # 处理 Word 文档
                doc = docx.Document(io.BytesIO(content))
                for para in doc.paragraphs:
                    if 'w:drawing' in para._p.xml or 'w:object' in para._p.xml:
                        logger.info(f"跳过包含图片的段落: {para.text[:20]}...")
                        continue

                    text_content = para.text.strip()
                    if not text_content:
                        continue
                    
                    parts = text_content.split(SEPARATOR)
                    parts = [p.strip() for p in parts]
                    
                    if len(parts) < 4:
                        continue

                    try:
                        # 解析序号 (如果第一列是数字)
                        order_part = re.sub(r'\D', '', parts[0])
                        order = int(order_part) if order_part else None
                        
                        q_type = ""
                        content_str = ""
                        score = 0.0
                        ref_answer = ""
                        rules = ""

                        if len(parts) >= 6:
                            # 完整格式：题号, 题型, 内容, 分值, 答案, 规则
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                            rules = parts[5]
                        elif len(parts) == 5:
                            # 5个字段: 题号, 题型, 内容, 分值, 答案
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                        else: # len == 4
                            # 4个字段: 题号, 内容, 分值, 答案 (无题型)
                            content_str = parts[1]
                            score = float(re.sub(r'[^\d.]', '', parts[2]) or 0)
                            ref_answer = parts[3]
                        
                        if not content_str or score <= 0:
                            continue

                        # 题型映射：使用原始中文，前端负责展示转换
                        # 常见题型标准化（可选，或者直接存）
                        # 这里直接存原始值，或做简单映射
                        type_map = {
                            "选择题": "choice", "选择": "choice",
                            "填空题": "fill_blank", "填空": "fill_blank",
                            "主观题": "essay", "简答题": "essay", "解答题": "essay", "问答题": "essay",
                            "计算题": "calculation", "计算": "calculation"
                        }
                        # 优先使用映射，如果没有则存原始值
                        final_type = type_map.get(q_type, q_type if q_type else "essay")

                        questions_to_add.append({
                            "question_order": order,
                            "question_type": final_type,
                            "content": content_str,
                            "score": score,
                            "reference_answer": ref_answer,
                            "scoring_rules": rules
                        })

                    except ValueError:
                        continue

            elif file_ext in {'.xlsx', '.xls'}:
                # 处理 Excel
                df = pd.read_excel(io.BytesIO(content))
                for _, row in df.iterrows():
                    # 至少要有题号(可空), 内容, 分值
                    if pd.isna(row.iloc[2]) or pd.isna(row.iloc[3]):
                        continue
                    
                    order_val = row.iloc[0]
                    order = int(order_val) if pd.notna(order_val) and str(order_val).isdigit() else None
                    
                    raw_type = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                    type_map = {
                            "选择题": "choice", "选择": "choice",
                            "填空题": "fill_blank", "填空": "fill_blank",
                            "主观题": "essay", "简答题": "essay", "解答题": "essay", "问答题": "essay",
                            "计算题": "calculation", "计算": "calculation"
                    }
                    final_type = type_map.get(raw_type, raw_type if raw_type else "essay")

                    questions_to_add.append({
                        "question_order": order,
                        "question_type": final_type,
                        "content": str(row.iloc[2]),
                        "score": float(row.iloc[3]),
                        "reference_answer": str(row.iloc[4]),
                        "scoring_rules": str(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else ""
                    })

            elif file_ext in {'.txt', '.csv'}:
                # 处理文本/CSV
                text_content = content.decode('utf-8')
                lines = text_content.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    parts = line.split(SEPARATOR)
                    parts = [p.strip() for p in parts]
                    
                    if len(parts) < 4: continue
                    
                    try:
                        order_part = re.sub(r'\D', '', parts[0])
                        order = int(order_part) if order_part else None
                        
                        q_type = ""
                        content_str = ""
                        score = 0.0
                        ref_answer = ""
                        rules = ""

                        if len(parts) >= 6:
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                            rules = parts[5]
                        elif len(parts) == 5:
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                        else:
                            content_str = parts[1]
                            score = float(re.sub(r'[^\d.]', '', parts[2]) or 0)
                            ref_answer = parts[3]
                            
                        type_map = {
                            "选择题": "choice", "选择": "choice",
                            "填空题": "fill_blank", "填空": "fill_blank",
                            "主观题": "essay", "简答题": "essay", "解答题": "essay", "问答题": "essay",
                            "计算题": "calculation", "计算": "calculation"
                        }
                        final_type = type_map.get(q_type, q_type if q_type else "essay")

                        questions_to_add.append({
                            "question_order": order,
                            "question_type": final_type,
                            "content": content_str,
                            "score": score,
                            "reference_answer": ref_answer,
                            "scoring_rules": rules
                        })
                    except:
                        continue
            else:
                raise HTTPException(status_code=400, detail="不支持的文件格式")

        except Exception as parse_error:
            logger.error(f"解析文件失败: {str(parse_error)}")
            raise HTTPException(status_code=400, detail=f"解析文件失败: {str(parse_error)}")

        if not questions_to_add:
            raise HTTPException(status_code=400, detail="未解析到有效题目数据")

        imported_count = 0
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # 获取已存在的序号
                existing_orders = set()
                res = conn.execute(text("SELECT question_order FROM exam_questions WHERE exam_id = :exam_id"), {"exam_id": exam_id})
                for row in res.fetchall():
                    existing_orders.add(row[0])

                for q in questions_to_add:
                    # 处理序号冲突或空序号
                    target_order = q["question_order"]
                    if target_order is None or target_order in existing_orders:
                        current_max_order += 1
                        target_order = current_max_order
                    
                    existing_orders.add(target_order) # 更新已存在集合，防止本次批量导入内部冲突

                    # 插入题目
                    res = conn.execute(
                        text("""
                        INSERT INTO questions (type, content, score, reference_answer, scoring_rules)
                        VALUES (:type, :content, :score, :reference_answer, :scoring_rules)
                        """),
                        {
                            "type": q["question_type"],
                            "content": q["content"],
                            "score": q["score"],
                            "reference_answer": q["reference_answer"],
                            "scoring_rules": q["scoring_rules"]
                        }
                    )
                    qid = res.lastrowid
                    
                    # 插入关联
                    conn.execute(
                        text("""
                        INSERT INTO exam_questions (exam_id, question_id, question_order)
                        VALUES (:exam_id, :question_id, :question_order)
                        """),
                        {
                            "exam_id": exam_id,
                            "question_id": qid,
                            "question_order": target_order
                        }
                    )
                    imported_count += 1
                
                trans.commit()
            except Exception as db_err:
                trans.rollback()
                raise db_err

        return {"code": 1, "msg": f"成功导入 {imported_count} 道题目", "data": {"count": imported_count}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入题目失败: {str(e)}")

# ==================== AI阅卷扩展接口 ====================

@app.post("/api/exams/{exam_id}/grade")
async def trigger_ai_grading(exam_id: int, student_id: Optional[int] = None):
    """
    触发AI阅卷 - 这是供学生实现的扩展接口

    当前实现：模拟AI阅卷过程，返回随机分数
    学生需要实现的功能：
    1. 获取学生的答题图片
    2. 调用OCR或AI服务识别图片内容
    3. 与参考答案进行对比
    4. 计算得分并返回结果
    """
    try:
        with engine.connect() as conn:
            # 获取需要阅卷的学生
            if student_id:
                students = [{"student_id": student_id}]
            else:
                result = conn.execute(
                    text("SELECT DISTINCT student_id FROM exam_images WHERE exam_id = :exam_id"),
                    {"exam_id": exam_id}
                )
                students = [{"student_id": row[0]} for row in result.fetchall()]

            # 获取考试题目
            questions_result = conn.execute(
                text("SELECT * FROM questions WHERE exam_id = :exam_id ORDER BY question_number"),
                {"exam_id": exam_id}
            )
            questions = [dict(row) for row in questions_result.fetchall()]

            if not questions:
                raise HTTPException(status_code=400, detail="该考试还没有设置题目")

            # 模拟AI阅卷过程
            graded_count = 0
            for student in students:
                # 获取学生的图片
                images_result = conn.execute(
                    text("SELECT * FROM exam_images WHERE exam_id = :exam_id AND student_id = :student_id"),
                    {"exam_id": exam_id, "student_id": student["student_id"]}
                )
                images = [dict(row) for row in images_result.fetchall()]

                if not images:
                    continue

                # ===== 这是学生需要实现的核心AI阅卷接口 =====
                ai_result = await simulate_ai_grading_interface(
                    exam_id=exam_id,
                    student_id=student["student_id"],
                    images=images,
                    questions=questions
                )
                # ===== 学生接口实现结束 =====

                # 保存阅卷结果
                if ai_result["success"]:
                    conn.execute(
                        text("""
                        INSERT INTO scores (exam_id, student_id, total_score, max_score, detail_scores,
                                          grading_status, ai_model_used, grading_confidence)
                        VALUES (:exam_id, :student_id, :total_score, :max_score, :detail_scores,
                               'completed', 'demo_interface', :confidence)
                        ON DUPLICATE KEY UPDATE
                        total_score = VALUES(total_score),
                        detail_scores = VALUES(detail_scores),
                        grading_status = VALUES(grading_status),
                        ai_model_used = VALUES(ai_model_used),
                        grading_confidence = VALUES(grading_confidence),
                        graded_at = CURRENT_TIMESTAMP
                        """),
                        {
                            "exam_id": exam_id,
                            "student_id": student["student_id"],
                            "total_score": ai_result["total_score"],
                            "max_score": sum(q["total_score"] for q in questions),
                            "detail_scores": json.dumps(ai_result["detail_scores"]),
                            "confidence": ai_result.get("confidence", 0.0)
                        }
                    )
                    conn.commit()
                    graded_count += 1

                # 记录AI调用日志
                conn.execute(
                    text("""
                    INSERT INTO ai_grading_logs (exam_id, student_id, image_id, api_endpoint,
                                               request_data, response_data, status_code, processing_time)
                    VALUES (:exam_id, :student_id, :image_id, :api_endpoint,
                           :request_data, :response_data, :status_code, :processing_time)
                    """),
                    {
                        "exam_id": exam_id,
                        "student_id": student["student_id"],
                        "image_id": images[0]["image_id"],
                        "api_endpoint": "/api/exams/{exam_id}/grade",
                        "request_data": json.dumps({"images": [img["image_id"] for img in images]}),
                        "response_data": json.dumps(ai_result),
                        "status_code": 200,
                        "processing_time": ai_result.get("processing_time", 0)
                    }
                )
                conn.commit()

            return {
                "code": 1,
                "msg": f"AI阅卷完成，处理了 {graded_count} 个学生",
                "data": {
                    "exam_id": exam_id,
                    "graded_count": graded_count,
                    "total_students": len(students)
                }
            }
    except Exception as e:
        logger.error(f"AI阅卷失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI阅卷失败: {str(e)}")

async def simulate_ai_grading_interface(exam_id: int, student_id: int, images: List[Dict], questions: List[Dict]) -> Dict:
    """
    模拟AI阅卷接口 - 学生需要实现的功能

    输入参数：
    - exam_id: 考试ID
    - student_id: 学生ID
    - images: 学生答题图片列表
    - questions: 题目信息列表

    输出格式：
    {
        "success": True,
        "total_score": 85.5,
        "detail_scores": {
            "1": {"score": 4, "max_score": 4, "confidence": 0.95},
            "2": {"score": 3, "max_score": 4, "confidence": 0.88},
            ...
        },
        "confidence": 0.91,
        "processing_time": 1500
    }
    """
    import random

    # 模拟处理时间
    processing_time = random.randint(500, 2000)

    # 模拟AI阅卷结果
    total_score = 0
    max_total_score = sum(q["total_score"] for q in questions)
    detail_scores = {}

    for question in questions:
        q_num = str(question["question_number"])
        max_score = question["total_score"]

        # 模拟AI评分 - 随机生成得分和置信度
        if question["question_type"] == "choice":
            # 选择题准确率高
            score = max_score if random.random() > 0.1 else 0
            confidence = random.uniform(0.95, 1.0)
        elif question["question_type"] == "fill_blank":
            # 填空题准确率中等
            score = int(max_score * random.uniform(0.6, 1.0))
            confidence = random.uniform(0.8, 0.95)
        else:
            # 主观题准确率较低
            score = int(max_score * random.uniform(0.5, 0.9))
            confidence = random.uniform(0.7, 0.9)

        detail_scores[q_num] = {
            "score": score,
            "max_score": max_score,
            "confidence": confidence
        }
        total_score += score

    return {
        "success": True,
        "total_score": round(total_score, 1),
        "detail_scores": detail_scores,
        "confidence": round(sum(d["confidence"] for d in detail_scores.values()) / len(detail_scores), 2),
        "processing_time": processing_time
    }

@app.get("/api/exams/{exam_id}/scores")
def get_exam_scores(exam_id: int, student_id: Optional[int] = None):
    """获取考试成绩"""
    try:
        with engine.connect() as conn:
            query = """
            SELECT sc.*, s.name as student_name, s.class_name, e.exam_name
            FROM scores sc
            LEFT JOIN students s ON sc.student_id = s.student_id
            LEFT JOIN exams e ON sc.exam_id = e.exam_id
            WHERE sc.exam_id = :exam_id
            """
            params = {"exam_id": exam_id}

            if student_id is not None:
                query += " AND sc.student_id = :student_id"
                params["student_id"] = student_id

            query += " ORDER BY sc.total_score DESC"

            result = conn.execute(text(query), params)
            scores = [dict(row) for row in result.fetchall()]

            # 解析detail_scores JSON
            for score in scores:
                if score["detail_scores"]:
                    try:
                        score["detail_scores"] = json.loads(score["detail_scores"])
                    except:
                        score["detail_scores"] = {}
                else:
                    score["detail_scores"] = {}

            return {"code": 1, "msg": "获取成功", "data": scores}
    except Exception as e:
        logger.error(f"获取考试成绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试成绩失败: {str(e)}")

@app.get("/api/ai-grading-demo")
async def ai_grading_demo():
    """
    AI阅卷接口使用说明和示例
    """
    demo_info = {
        "title": "AI阅卷扩展接口使用说明",
        "description": "学生需要在这个平台上实现AI阅卷功能",
        "interface_spec": {
            "endpoint": "POST /api/exams/{exam_id}/grade",
            "input": {
                "exam_id": "考试ID",
                "student_id": "学生ID(可选)",
                "images": "学生答题图片列表",
                "questions": "题目信息列表"
            },
            "output": {
                "success": "是否成功",
                "total_score": "总分",
                "detail_scores": "每题详细得分",
                "confidence": "置信度",
                "processing_time": "处理时间"
            }
        },
        "implementation_steps": [
            "1. 读取学生答题图片",
            "2. 使用OCR或AI服务识别图片中的文字内容",
            "3. 解析学生答案，按题目进行分组",
            "4. 获取题目的参考答案",
            "5. 使用AI对比学生答案和参考答案",
            "6. 计算每题得分和总分",
            "7. 返回标准格式的结果"
        ],
        "example_response": {
            "success": True,
            "total_score": 85.5,
            "detail_scores": {
                "1": {"score": 4, "max_score": 4, "confidence": 0.95},
                "2": {"score": 3, "max_score": 4, "confidence": 0.88},
                "3": {"score": 5, "max_score": 5, "confidence": 0.92}
            },
            "confidence": 0.91,
            "processing_time": 1500
        }
    }

    return {"code": 1, "msg": "AI阅卷接口说明", "data": demo_info}

# ==================== 系统配置API ====================

@app.get("/api/config")
def get_system_config():
    """获取系统配置"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT config_key, config_value, description FROM system_config"))
            configs = {row[0]: {"value": row[1], "description": row[2]} for row in result.fetchall()}

            return {"code": 1, "msg": "获取成功", "data": configs}
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")

# ==================== 试卷管理API ====================

class PaperRequest(BaseModel):
    paper_id: Optional[int] = None
    exam_id: int
    student_name: Optional[str] = ""
    student_number: Optional[str] = ""
    seat_number: Optional[str] = ""
    status: Optional[str] = "ungraded"

class PaperDetailRequest(BaseModel):
    detail_id: Optional[int] = None
    paper_id: int
    question_number: int
    answer_text: Optional[str] = ""
    score: Optional[float] = None
    total_score: Optional[float] = 0

@app.get("/api/papers/{exam_id}")
def get_papers(exam_id: int):
    """获取考试的试卷列表"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            result = conn.execute(
                text("""
                SELECT p.*, s.name as student_name, s.student_number, s.class_name
                FROM papers p
                LEFT JOIN students s ON p.student_id = s.student_id
                WHERE p.exam_id = :exam_id
                ORDER BY p.created_at DESC
                """),
                {"exam_id": exam_id}
            )
            papers = [dict(row) for row in result.fetchall()]
            return {"code": 1, "msg": "获取成功", "data": papers}
    except Exception as e:
        logger.error(f"获取试卷列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取试卷列表失败: {str(e)}")

@app.get("/api/paper-details/{paper_id}")
def get_paper_details(paper_id: int):
    """获取试卷详情"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT pd.*, p.exam_id, p.student_id, s.name as student_name
                FROM paper_details pd
                LEFT JOIN papers p ON pd.paper_id = p.paper_id
                LEFT JOIN students s ON p.student_id = s.student_id
                WHERE pd.paper_id = :paper_id
                ORDER BY pd.question_number
                """),
                {"paper_id": paper_id}
            )
            details = [dict(row) for row in result.fetchall()]
            return {"code": 1, "msg": "获取成功", "data": details}
    except Exception as e:
        logger.error(f"获取试卷详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取试卷详情失败: {str(e)}")

@app.post("/api/papers/grade")
def grade_paper(paper_id: int, scores: Dict[str, Any]):
    """提交试卷评分结果"""
    try:
        with engine.connect() as conn:
            # 更新试卷详情中的分数
            for question_num, score_data in scores.items():
                if isinstance(score_data, dict) and 'score' in score_data:
                    conn.execute(
                        text("""
                        UPDATE paper_details
                        SET score = :score, updated_at = CURRENT_TIMESTAMP
                        WHERE paper_id = :paper_id AND question_number = :question_number
                        """),
                        {
                            "paper_id": paper_id,
                            "question_number": int(question_num),
                            "score": float(score_data['score'])
                        }
                    )

            # 计算总分
            total_score_result = conn.execute(
                text("SELECT SUM(score) as total FROM paper_details WHERE paper_id = :paper_id AND score IS NOT NULL"),
                {"paper_id": paper_id}
            )
            total_score = total_score_result.fetchone()[0] or 0.0

            # 更新试卷状态
            conn.execute(
                text("""
                UPDATE papers
                SET status = 'graded', total_score = :total_score, updated_at = CURRENT_TIMESTAMP
                WHERE paper_id = :paper_id
                """),
                {"paper_id": paper_id, "total_score": total_score}
            )

            conn.commit()
            return {"code": 1, "msg": "评分成功", "data": {"total_score": total_score}}
    except Exception as e:
        logger.error(f"提交评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交评分失败: {str(e)}")

# ==================== 参考答案管理API ====================

@app.post("/api/reference-answers/import")
def import_reference_answers(exam_id: int, answers: Dict[str, str]):
    """导入标准答案"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 删除现有的参考答案
            conn.execute(text("DELETE FROM reference_answers WHERE exam_id = :exam_id"), {"exam_id": exam_id})

            # 插入新的参考答案
            for question_number, answer in answers.items():
                conn.execute(
                    text("""
                    INSERT INTO reference_answers (exam_id, question_number, answer_text)
                    VALUES (:exam_id, :question_number, :answer_text)
                    """),
                    {
                        "exam_id": exam_id,
                        "question_number": int(question_number),
                        "answer_text": str(answer)
                    }
                )

            conn.commit()
            return {"code": 1, "msg": f"成功导入 {len(answers)} 道题目的标准答案"}
    except Exception as e:
        logger.error(f"导入标准答案失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入标准答案失败: {str(e)}")

@app.get("/api/reference-answers/{exam_id}")
def get_reference_answers(exam_id: int):
    """获取标准答案"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT question_number, answer_text
                FROM reference_answers
                WHERE exam_id = :exam_id
                ORDER BY question_number
                """),
                {"exam_id": exam_id}
            )
            answers = {str(row[0]): row[1] for row in result.fetchall()}
            return {"code": 1, "msg": "获取成功", "data": answers}
    except Exception as e:
        logger.error(f"获取标准答案失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标准答案失败: {str(e)}")

# ==================== 学生座位号管理API ====================

@app.post("/api/student-seats/import")
def import_student_seats(exam_id: int, students: List[Dict[str, Any]]):
    """导入学生座位号"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            imported_count = 0
            for student in students:
                student_name = student.get('studentName', '').strip()
                seat_number = student.get('seatNumber', '').strip()
                student_number = student.get('studentId', '').strip()

                if not student_name or not seat_number:
                    continue

                # 检查学生是否已存在，不存在则创建
                existing_student = conn.execute(
                    text("SELECT student_id FROM students WHERE name = :name AND (student_number = :student_number OR student_number IS NULL)"),
                    {"name": student_name, "student_number": student_number if student_number else None}
                ).fetchone()

                if existing_student:
                    student_id = existing_student[0]
                else:
                    # 创建新学生
                    student_result = conn.execute(
                        text("""
                        INSERT INTO students (name, student_number, class, contact_info)
                        VALUES (:name, :student_number, '', '')
                        """),
                        {
                            "name": student_name,
                            "student_number": student_number if student_number else f"AUTO_{int(time.time())}"
                        }
                    )
                    conn.commit()
                    student_id = student_result.lastrowid

                # 创建试卷记录
                try:
                    conn.execute(
                        text("""
                        INSERT INTO papers (exam_id, student_id, seat_number, status)
                        VALUES (:exam_id, :student_id, :seat_number, 'ungraded')
                        """),
                        {
                            "exam_id": exam_id,
                            "student_id": student_id,
                            "seat_number": seat_number
                        }
                    )
                    conn.commit()
                    imported_count += 1
                except:
                    # 座位号可能已存在，跳过
                    continue

            return {"code": 1, "msg": f"成功导入 {imported_count} 名学生的座位号"}
    except Exception as e:
        logger.error(f"导入学生座位号失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入学生座位号失败: {str(e)}")

# ==================== 视频上传API ====================

@app.post("/api/upload-video")
async def upload_video(exam_name: str = Form(...), video: UploadFile = File(...)):
    """上传考试视频并创建考试"""
    try:
        # 创建考试
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                INSERT INTO exams (exam_name, description, status)
                VALUES (:exam_name, '从视频导入的考试', 'created')
                """),
                {"exam_name": exam_name}
            )
            conn.commit()
            exam_id = result.lastrowid

        # 保存视频文件（简化处理）
        video_dir = os.path.join(UPLOAD_DIR, f"exam_{exam_id}")
        os.makedirs(video_dir, exist_ok=True)

        video_path = os.path.join(video_dir, f"video_{int(time.time())}_{video.filename}")
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        return {
            "code": 1,
            "msg": "视频上传成功，考试创建成功",
            "data": {
                "exam_id": exam_id,
                "exam_name": exam_name,
                "video_path": video_path
            }
        }
    except Exception as e:
        logger.error(f"上传视频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传视频失败: {str(e)}")

# ==================== AI评分API ====================

@app.post("/api/ai-grade")
async def ai_grade(request: Dict[str, Any]):
    """AI评分接口"""
    try:
        exam_id = request.get('exam_id')
        paper_id = request.get('paper_id')
        student_answers = request.get('student_answers', {})
        reference_answers = request.get('reference_answers', {})
        question_types = request.get('question_types', {})
        total_scores = request.get('total_scores', {})

        # 这里是AI评分的核心逻辑
        # 简化实现：基于字符串相似度评分
        graded_results = {}

        for question_num, student_answer in student_answers.items():
            if question_num not in reference_answers:
                continue

            ref_answer = reference_answers[question_num]
            q_type = question_types.get(question_num, 'essay')
            max_score = total_scores.get(question_num, 0)

            # 简单的评分算法
            if q_type == 'choice':
                # 选择题：完全匹配
                score = max_score if student_answer.strip().lower() == ref_answer.strip().lower() else 0
                confidence = 1.0 if score > 0 else 0.0
            else:
                # 主观题：基于相似度
                similarity = calculate_text_similarity(student_answer, ref_answer)
                score = max_score * similarity
                confidence = min(0.95, similarity + 0.1)

            graded_results[question_num] = {
                "score": round(score, 1),
                "max_score": max_score,
                "confidence": round(confidence, 2)
            }

        return {
            "code": 1,
            "msg": "AI评分完成",
            "data": graded_results
        }
    except Exception as e:
        logger.error(f"AI评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI评分失败: {str(e)}")

def calculate_text_similarity(text1: str, text2: str) -> float:
    """计算文本相似度（简化实现）"""
    if not text1 or not text2:
        return 0.0

    # 简单的字符级相似度计算
    set1 = set(text1.lower())
    set2 = set(text2.lower())

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0

# ==================== 健康检查 ====================

@app.get("/api/health")
def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # 检查上传目录
        upload_accessible = os.path.exists(UPLOAD_DIR) and os.access(UPLOAD_DIR, os.W_OK)

        return {
            "code": 1,
            "msg": "系统正常",
            "data": {
                "database": "connected",
                "upload_directory": "accessible" if upload_accessible else "not_accessible",
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "code": 0,
            "msg": "系统异常",
            "data": {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)