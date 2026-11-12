import os
import json
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application
    APP_NAME: str = "SmartGST AI ERP"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/smartgst_db"
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SMTP (Optional for development)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "test@gmail.com"
    SMTP_PASSWORD: str = "test-password"
    SMTP_FROM_EMAIL: str = "test@gmail.com"
    
    # OTP
    OTP_EXPIRY_MINUTES: int = 10
    OTP_LENGTH: int = 6
    OTP_MAX_ATTEMPTS: int = 5
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # File Upload
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_FILE_TYPES: str = "pdf,jpg,jpeg,png,xlsx,xls,doc,docx"
    UPLOAD_DIR: str = "./uploads"
    
    # ML Models
    ML_MODEL_PATH: str = "./ml-models"
    ENABLE_OCR: bool = True
    ENABLE_FRAUD_DETECTION: bool = True
    ENABLE_DEMAND_FORECASTING: bool = True
    
    # Session
    SESSION_TIMEOUT_MINUTES: int = 30
    REMEMBER_LOGIN_DAYS: int = 30
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    
    # Backup
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "daily"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "./backups"
    
    # Notifications
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    SEND_DUE_REMINDERS: bool = True
    SEND_STOCK_ALERTS: bool = True
    SEND_PAYMENT_ALERTS: bool = True
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Currency
    DEFAULT_CURRENCY: str = "INR"
    DECIMAL_PLACES: int = 2
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            if value.strip().startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value):
        if isinstance(value, str):
            if value.strip().startswith("["):
                return json.loads(value)
            return [host.strip() for host in value.split(",") if host.strip()]
        return value

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value):
        if not value or len(value) < 32:
            raise ValueError("SECRET_KEY must be set and contain at least 32 characters")
        return value


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
