import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from .config import get_settings
from app.models.database import Base

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parents[2]


def _resolve_database_url(url: str) -> str:
    """Resolve SQLite URLs relative to the backend directory so uvicorn can find the same DB file regardless of cwd."""
    if not url.startswith("sqlite"):
        return url

    if url.startswith("sqlite:///./"):
        relative_path = url[len("sqlite:///./"):]
        db_path = (BASE_DIR / relative_path).resolve()
        return f"sqlite:///{db_path.as_posix()}"

    if url.startswith("sqlite:///"):
        relative_path = url[len("sqlite:///"):]
        if relative_path and not os.path.isabs(relative_path):
            db_path = (BASE_DIR / relative_path).resolve()
            return f"sqlite:///{db_path.as_posix()}"

    return url


resolved_database_url = _resolve_database_url(settings.DATABASE_URL)

# Create engine
engine = create_engine(
    resolved_database_url,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    connect_args={"check_same_thread": False} if resolved_database_url.startswith("sqlite") else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
# Reuse the shared SQLAlchemy Base from the models module so all tables register correctly.


def _ensure_user_scoped_business_identifiers(schema_engine) -> None:
    identifier_indexes = {
        "products": {
            "sku": "uq_products_user_sku",
            "barcode": "uq_products_user_barcode",
        },
        "invoices": {
            "invoice_number": "uq_invoices_user_invoice_number",
        },
        "purchases": {
            "purchase_number": "uq_purchases_user_purchase_number",
        },
    }
    inspector = inspect(schema_engine)
    preparer = schema_engine.dialect.identifier_preparer

    for table_name, identifiers in identifier_indexes.items():
        if not inspector.has_table(table_name):
            continue

        indexes = inspector.get_indexes(table_name)
        constraints = inspector.get_unique_constraints(table_name)
        with schema_engine.begin() as connection:
            for constraint in constraints:
                columns = constraint.get("column_names") or []
                if len(columns) == 1 and columns[0] in identifiers:
                    if schema_engine.dialect.name != "postgresql":
                        raise RuntimeError(
                            f"Cannot safely migrate the legacy {table_name}.{columns[0]} "
                            "unique constraint on this database"
                        )
                    if not constraint.get("name"):
                        raise RuntimeError(f"Cannot identify the legacy {table_name} unique constraint")
                    connection.execute(text(
                        f"ALTER TABLE {preparer.quote(table_name)} "
                        f"DROP CONSTRAINT IF EXISTS {preparer.quote(constraint['name'])}"
                    ))

            for index in indexes:
                columns = index.get("column_names") or []
                if index.get("unique") and index.get("name") and len(columns) == 1 and columns[0] in identifiers:
                    connection.execute(text(
                        f"DROP INDEX IF EXISTS {preparer.quote(index['name'])}"
                    ))

            for column_name, index_name in identifiers.items():
                connection.execute(text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS {preparer.quote(index_name)} "
                    f"ON {preparer.quote(table_name)} "
                    f"({preparer.quote('user_id')}, {preparer.quote(column_name)})"
                ))


def ensure_schema_compatibility(schema_engine=engine) -> None:
    """Apply small additive changes needed by databases created by older builds."""
    _ensure_user_scoped_business_identifiers(schema_engine)
    inspector = inspect(schema_engine)
    if "otp" not in inspector.get_table_names():
        return

    otp_columns = {column["name"] for column in inspector.get_columns("otp")}
    statements = []
    if "code_hash" not in otp_columns:
        statements.append("ALTER TABLE otp ADD COLUMN code_hash VARCHAR(64)")
    if "attempts" not in otp_columns:
        statements.append("ALTER TABLE otp ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0")

    if statements:
        with schema_engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

    if "invoices" in inspector.get_table_names():
        invoice_columns = {column["name"] for column in inspector.get_columns("invoices")}
        if "shop_name" not in invoice_columns:
            with schema_engine.begin() as connection:
                connection.execute(text("ALTER TABLE invoices ADD COLUMN shop_name VARCHAR(255)"))
        if "discount_amount" not in invoice_columns:
            with schema_engine.begin() as connection:
                connection.execute(text("ALTER TABLE invoices ADD COLUMN discount_amount NUMERIC(15, 2) NOT NULL DEFAULT 0"))

    if "branches" in inspector.get_table_names():
        branch_columns = {column["name"] for column in inspector.get_columns("branches")}
        if "state_code" not in branch_columns:
            with schema_engine.begin() as connection:
                connection.execute(text("ALTER TABLE branches ADD COLUMN state_code VARCHAR(10)"))


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
