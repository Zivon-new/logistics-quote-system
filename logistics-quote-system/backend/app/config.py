# backend/app/config.py
"""
项目配置文件
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "国际物流报价系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置（从 .env 读取，无默认密码）
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str
    DB_NAME: str = "price_test_v2"

    # 数据库连接URL
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    # 智谱 GLM API
    ZHIPU_API_KEY: str = ""

    # JWT配置（从 .env 读取，无默认值）
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1天（原7天，缩短降低Token窃取风险）

    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost:5173",  # Vue开发服务器
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
