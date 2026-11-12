from typing import Any

from sqlalchemy.orm import Session

from app.models.database import AuditLog, User


def record_audit(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
) -> None:
    db.add(AuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
    ))
