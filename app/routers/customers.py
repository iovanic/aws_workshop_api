from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Order
from app.schemas import CustomerCreate, CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)) -> list[Customer]:
    return list(db.scalars(select(Customer).order_by(Customer.email)).all())


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    """Crea o actualiza por email (registro web / sincronización de perfil)."""
    email = body.email.strip()
    name = body.name.strip()
    shipping_address = body.shipping_address.strip()
    phone_number = body.phone_number.strip()[:32]

    existing = db.scalar(select(Customer).where(Customer.email == email))
    if existing is not None:
        existing.name = name
        existing.shipping_address = shipping_address
        existing.phone_number = phone_number
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Could not update customer") from None
        db.refresh(existing)
        return existing

    customer = Customer(
        email=email,
        name=name,
        shipping_address=shipping_address,
        phone_number=phone_number,
    )
    db.add(customer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Customer with this email already exists") from None

    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: UUID, db: Session = Depends(get_db)) -> None:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    n_orders = db.scalar(
        select(func.count()).select_from(Order).where(Order.customer_id == customer_id)
    )
    if n_orders and n_orders > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete customer with existing orders",
        )

    db.delete(customer)
    db.commit()
