import os

# 数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # 请根据实际情况修改，如果无密码则留空
    'database': 'exam_platform'
}

# 文件上传配置
UPLOAD_DIR = "/home/wkd/aupappersys/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
