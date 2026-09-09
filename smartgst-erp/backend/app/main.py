from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import engine, Base
from app.models.database import User, OTP, UserSession, Branch, Customer, Vendor, Product, Inventory, Invoice, InvoiceItem, Purchase, PurchaseItem, Payment, VendorPayment, GSTRecord, Ledger, Transaction, AuditLog, Notification
from app.api.routes import auth, dashboard

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup and shutdown"""
    # Startup
    print("Starting SmartGST AI ERP...")
    Path("uploads").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    yield
    # Shutdown
    print("Shutting down SmartGST AI ERP...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    Path("uploads").mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title=settings.APP_NAME,
        description="Production-ready SaaS ERP platform for GST management, Accounting, and Business Intelligence",
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    allowed_hosts = settings.ALLOWED_HOSTS if settings.ENVIRONMENT != "development" else ["*"]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "app": settings.APP_NAME}
    
    @app.get("/api/v1")
    async def api_version():
        """API version endpoint"""
        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    
    return app


app = create_app()
