from sqlalchemy.orm import Session
from app.infrastructure.database.models.payment_model import Payment, PaymentStatus, PaymentMethod
from datetime import datetime


def get_payment_status_id(db: Session, name: str) -> int:
    row = (
        db.query(PaymentStatus.payment_status_id)
        .filter(PaymentStatus.payment_status_name == name)
        .scalar()
    )
    if row is None:
        raise ValueError(f"PaymentStatus '{name}' not found")
    return row


def get_payment_methods(db: Session) -> list[PaymentMethod]:
    return db.query(PaymentMethod).all()


def insert_payment(
    db: Session,
    booking_id: int,
    payment_status_id: int,
    payment_method_id: int,
    payment_amount: float,
) -> Payment:
    payment = Payment(
        booking_id=booking_id,
        payment_status_id=payment_status_id,
        payment_method_id=payment_method_id,
        payment_amount=payment_amount,
        payment_date_time=datetime.utcnow(),
    )
    db.add(payment)
    db.commit()
    return payment



def get_total_paid(db: Session, booking_id: int, paid_status_id: int) -> float:
    result = (
        db.query(Payment.payment_amount)
        .filter(
            Payment.booking_id == booking_id,
            Payment.payment_status_id == paid_status_id,
        )
        .all()
    )
    return sum(float(r[0]) for r in result)