import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application
    APP_NAME: str = "SmartGST AI ERP"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "sqlite:///./smartgst_dev.db"
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production-12345"
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
    
    # Super Admin
    SUPER_ADMIN_EMAIL: str = "admin@smartgst.com"
    SUPER_ADMIN_NAME: str = "Super Admin"
    
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
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver", "*"]
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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
