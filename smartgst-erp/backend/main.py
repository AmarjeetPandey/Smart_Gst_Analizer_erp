import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.core.database import get_db, engine
from app.core.config import get_settings
from app.services.auth_service import AuthService
from app.models.database import Base

settings = get_settings()


def setup_database():
    """Initialize database tables and super admin"""
    print("Setting up database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Create directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.BACKUP_PATH, exist_ok=True)
    print("✓ Directories created")


def setup_super_admin():
    """Setup super admin account"""
    from sqlalchemy.orm import Session
    
    print("Setting up super admin...")
    db = Session(bind=engine)
    try:
        AuthService.setup_super_admin(db)
        print("✓ Super admin configured")
    finally:
        db.close()


if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"{'='*50}\n")
    
    # Setup
    setup_database()
    setup_super_admin()
    
    print(f"\n✓ Application ready!")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug: {settings.DEBUG}")
    print(f"  Database: {settings.DATABASE_URL}")
    print(f"  Redis: {settings.REDIS_URL}")
    print(f"\nStart server with:")
    print(f"  uvicorn main:app --reload")
    print(f"\nAPI Documentation:")
    print(f"  http://localhost:8000/api/docs\n")
