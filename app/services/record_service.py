from datetime import date
from typing import Optional
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.financial_record import FinancialRecord, RecordType
from app.models.user import User, UserRole
from app.schemas.financial_record import RecordCreate, RecordUpdate, RecordFilter, PaginatedRecords


class RecordService:

    @staticmethod
    def create_record(db: Session, data: RecordCreate, actor: User) -> FinancialRecord:
        record = FinancialRecord(
            amount=float(data.amount),
            type=data.type,
            category=data.category,
            date=data.date,
            description=data.description,
            notes=data.notes,
            created_by=actor.id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def _base_query(db: Session):
        """Return non-deleted records only."""
        return db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)  # noqa: E712

    @staticmethod
    def get_record(db: Session, record_id: int) -> FinancialRecord:
        record = RecordService._base_query(db).filter(FinancialRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        return record

    @staticmethod
    def list_records(db: Session, filters: RecordFilter) -> PaginatedRecords:
        query = RecordService._base_query(db)

        if filters.type:
            query = query.filter(FinancialRecord.type == filters.type)
        if filters.category:
            query = query.filter(FinancialRecord.category == filters.category)
        if filters.date_from:
            query = query.filter(FinancialRecord.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(FinancialRecord.date <= filters.date_to)

        total = query.count()
        items = (
            query.order_by(FinancialRecord.date.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .all()
        )
        return PaginatedRecords(total=total, page=filters.page, page_size=filters.page_size, items=items)

    @staticmethod
    def update_record(db: Session, record_id: int, data: RecordUpdate, actor: User) -> FinancialRecord:
        record = RecordService.get_record(db, record_id)

        if data.amount is not None:
            record.amount = float(data.amount)
        if data.type is not None:
            record.type = data.type
        if data.category is not None:
            record.category = data.category
        if data.date is not None:
            record.date = data.date
        if data.description is not None:
            record.description = data.description
        if data.notes is not None:
            record.notes = data.notes

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_record(db: Session, record_id: int, actor: User) -> None:
        record = RecordService.get_record(db, record_id)
        record.is_deleted = True  # soft delete
        db.commit()
