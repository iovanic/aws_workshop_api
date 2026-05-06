from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    tagline: str
    description: str
    price: float
    images: list[str]

    @field_validator("price", mode="before")
    @classmethod
    def _price_to_float(cls, v: object) -> float:
        if isinstance(v, Decimal):
            return float(v)
        return float(v)  # type: ignore[arg-type]


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    shipping_address: str
    phone_number: str


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    quantity: int
    unit_price: float

    @field_validator("unit_price", mode="before")
    @classmethod
    def _unit_price_to_float(cls, v: object) -> float:
        if isinstance(v, Decimal):
            return float(v)
        return float(v)  # type: ignore[arg-type]


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
    """Solo email + líneas: el cliente debe existir en RDS (creado al registrarse)."""

    customer_email: str = Field(..., min_length=3, max_length=320)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class ProductCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    tagline: str = ""
    description: str = ""
    price: Decimal = Field(..., ge=Decimal("0"), max_digits=12, decimal_places=2)
    images: list[str] = Field(default_factory=list)

    @field_validator("price", mode="after")
    @classmethod
    def _quantize_price(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class CustomerCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    name: str = ""
    shipping_address: str = ""
    phone_number: str = ""
