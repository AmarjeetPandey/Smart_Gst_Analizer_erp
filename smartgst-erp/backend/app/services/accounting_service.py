from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.database import Ledger, Transaction, User


ZERO = Decimal("0.00")


def _ledger(db: Session, user: User, name: str, account_type: str) -> Ledger:
    ledger = db.query(Ledger).filter(Ledger.user_id == user.id, Ledger.account_name == name).first()
    if ledger:
        return ledger
    ledger = Ledger(user_id=user.id, account_name=name, account_type=account_type, opening_balance=ZERO, current_balance=ZERO)
    db.add(ledger)
    db.flush()
    return ledger


def post_entry(
    db: Session,
    user: User,
    transaction_date: date,
    description: str,
    reference_id: str,
    transaction_type: str,
    entries: list[tuple[str, str, Decimal, Decimal]],
) -> None:
    """Post a balanced journal once; repeated requests with the same reference are ignored."""
    if db.query(Transaction).filter(Transaction.user_id == user.id, Transaction.reference_id == reference_id).first():
        return

    total_debit = sum((Decimal(debit) for _, _, debit, _ in entries), ZERO)
    total_credit = sum((Decimal(credit) for _, _, _, credit in entries), ZERO)
    if total_debit != total_credit:
        raise ValueError("Journal entry is not balanced")

    for account_name, account_type, debit, credit in entries:
        ledger = _ledger(db, user, account_name, account_type)
        ledger.current_balance = Decimal(ledger.current_balance or ZERO) + Decimal(debit) - Decimal(credit)
        db.add(Transaction(
            user_id=user.id,
            ledger_id=ledger.id,
            transaction_date=transaction_date,
            description=description,
            debit=debit,
            credit=credit,
            balance=ledger.current_balance,
            reference_id=reference_id,
            transaction_type=transaction_type,
        ))
