from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os

# 声明基类，所有模型都要继承它
class Base(DeclarativeBase):
    pass

# 数据库 URL 从环境变量读取
DB_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DB_URL,
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "0") == "1",
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
