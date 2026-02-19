import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://lavanderia:lavanderia123@db:5432/lavanderia_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-123456789")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    PROJECT_NAME: str = "Lavanderia Hospitalar"
    API_V1_STR: str = "/api/v1"


settings = Settings()
