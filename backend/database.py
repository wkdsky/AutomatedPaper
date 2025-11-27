from sqlalchemy import create_engine
from .config import DATABASE_CONFIG

# 创建数据库连接
engine = create_engine(
    f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:3306/{DATABASE_CONFIG['database']}",
    echo=True
)
