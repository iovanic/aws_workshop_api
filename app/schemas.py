from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    tagline: str
    description: str
    price: int
    images: list[str]


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    shipping_address: str


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    quantity: int
    unit_price: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer: CustomerOut
    created_at: datetime
    items: list[OrderItemOut]


class OrderItemCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    customer_email: str = Field(..., min_length=3, max_length=320)
    customer_name: str = ""
    shipping_address: str = ""
    items: list[OrderItemCreate] = Field(..., min_length=1)


class ProductCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    tagline: str = ""
    description: str = ""
    price: int = Field(..., ge=0)
    images: list[str] = Field(default_factory=list)


class CustomerCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    name: str = ""
    shipping_address: str = ""
