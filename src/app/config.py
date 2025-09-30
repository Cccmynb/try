import os
from dotenv import load_dotenv

# 先加载 .env 文件（在项目根目录）
load_dotenv()

# 是否使用 Mock 逻辑（默认 true，方便本地快速跑通）
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "false"

# 数据库连接
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:123456@localhost:5432/ittc"
)

# Redis 连接
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# LLM 配置
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3")
LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))
