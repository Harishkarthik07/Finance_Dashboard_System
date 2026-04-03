from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from decimal import Decimal
from app.models.financial_record import RecordType, Category


class RecordCreate(BaseModel):
    amount: Decimal
    type: RecordType
    category: Category
    date: date
    description: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class RecordUpdate(BaseModel):
    amount: Optional[Decimal] = None
    type: Optional[RecordType] = None
    category: Optional[Category] = None
    date: Optional[date] = None
    description: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: Category
    date: date
    description: Optional[str]
    notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordFilter(BaseModel):
    type: Optional[RecordType] = None
    category: Optional[Category] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = 1
    page_size: int = 20

    @field_validator("page")
    @classmethod
    def page_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def page_size_limit(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("page_size must be between 1 and 100")
        return v


class PaginatedRecords(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RecordResponse]
