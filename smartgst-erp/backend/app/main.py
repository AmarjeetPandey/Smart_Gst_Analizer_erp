from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import engine, Base, ensure_schema_compatibility, resolved_database_url
from app.models.database import User, OTP, UserSession, Branch, Customer, Vendor, Product, Inventory, Invoice, InvoiceItem, Purchase, PurchaseItem, Payment, VendorPayment, GSTRecord, Ledger, Transaction, AuditLog, Notification
from app.api.routes import ai, auth, dashboard, erp

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup and shutdown"""
    # Startup
    print("Starting SmartGST AI ERP...")
    Path("uploads").mkdir(parents=True, exist_ok=True)
    if settings.ENVIRONMENT == "development" and resolved_database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        ensure_schema_compatibility()
        print("Development SQLite database tables created successfully")
    elif settings.ENVIRONMENT == "development":
        ensure_schema_compatibility()
        print("Using pre-initialized PostgreSQL database")
    else:
        print("Production database schema must be prepared before startup")
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
    allowed_hosts = ["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_HOSTS
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
    app.include_router(erp.router, prefix="/api/v1", tags=["ERP"])
    app.include_router(ai.router, prefix="/api/v1", tags=["AI"])
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
