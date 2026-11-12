"""Create the initial application schema before production startup."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.core.database import Base, engine, ensure_schema_compatibility
from app.models import database as _models  # noqa: F401


def main() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.BACKUP_PATH).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
