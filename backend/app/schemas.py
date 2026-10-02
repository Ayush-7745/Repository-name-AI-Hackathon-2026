from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    quantity: float = Field(gt=0)
    unit: Optional[str] = None
    brand: Optional[str] = None
    pack_size: Optional[float] = None
    pack_unit: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[float] = None


class ParseRequest(BaseModel):
    message: str = Field(min_length=1)


class ParseResponse(BaseModel):
    message: str
    items: List[OrderItem]
    clarification_needed: bool = False
    clarification_question: Optional[str] = None


class ValidateRequest(BaseModel):
    items: List[OrderItem]


class ValidateResponse(BaseModel):
    items: List[OrderItem]
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    issues: List[str] = []


class ConfirmRequest(BaseModel):
    items: List[OrderItem]


class ConfirmResponse(BaseModel):
    order_id: str
    total: float
    items: List[OrderItem]
    status: str
