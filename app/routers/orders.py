from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Customer, Order, OrderItem, Product
from app.schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)) -> list[Order]:
    q = (
        select(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.customer),
        )
        .order_by(Order.created_at.desc())
    )
    return list(db.scalars(q).unique().all())


@router.post("", response_model=OrderOut, status_code=201)
def create_order(body: OrderCreate, db: Session = Depends(get_db)) -> Order:
    email = body.customer_email.strip()
    customer = db.scalar(select(Customer).where(Customer.email == email))
    if customer is None:
        customer = Customer(
            email=email,
            name=body.customer_name.strip(),
            shipping_address=body.shipping_address.strip(),
        )
        db.add(customer)
        db.flush()
    else:
        customer.name = body.customer_name.strip()
        customer.shipping_address = body.shipping_address.strip()

    order = Order(customer_id=customer.id)

    for line in body.items:
        product = db.get(Product, line.product_id)
        if product is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown product_id: {line.product_id}",
            )
        order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=line.quantity,
                unit_price=product.price,
            )
        )

    db.add(order)
    db.commit()

    hydrated = db.scalars(
        select(Order)
        .where(Order.id == order.id)
        .options(joinedload(Order.items), joinedload(Order.customer))
    ).unique().one()

    assert hydrated.items is not None
    hydrated.items.sort(key=lambda x: x.id)
    return hydrated


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: UUID, db: Session = Depends(get_db)) -> Order:
    order = db.scalars(
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items), joinedload(Order.customer))
    ).unique().one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    assert order.items is not None
    order.items.sort(key=lambda x: x.id)
    return order


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: UUID, db: Session = Depends(get_db)) -> None:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
