from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib
from sqlalchemy import text
import logging

from backend.database import engine

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== Pydantic模型定义 ====================

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

# ==================== 用户认证逻辑 ====================

def hash_password(password: str) -> str:
    """密码哈希函数"""
    # 使用简单的SHA-256哈希（生产环境建议使用bcrypt）
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed_password

@router.post("/api/register")
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

@router.post("/api/login")
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
