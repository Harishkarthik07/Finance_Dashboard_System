from typing import Annotated, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import CurrentUser, require_analyst_or_above, require_admin
from app.models.user import User
from app.models.financial_record import RecordType, Category
from app.schemas.financial_record import (
    RecordCreate, RecordUpdate, RecordResponse, RecordFilter, PaginatedRecords
)
from app.services.record_service import RecordService

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.get("/", response_model=PaginatedRecords, summary="List records with filters (viewer+)")
def list_records(
    type: Optional[RecordType] = Query(None),
    category: Optional[Category] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: CurrentUser = None,
):
    filters = RecordFilter(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return RecordService.list_records(db, filters)


@router.get("/{record_id}", response_model=RecordResponse, summary="Get record by ID (viewer+)")
def get_record(
    record_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: CurrentUser = None,
):
    return RecordService.get_record(db, record_id)


@router.post("/", response_model=RecordResponse, status_code=201,
             summary="Create a new record (admin only)")
def create_record(
    data: RecordCreate,
    db: Annotated[Session, Depends(get_db)] = None,
    actor: Annotated[User, Depends(require_admin)] = None,
):
    return RecordService.create_record(db, data, actor)


@router.patch("/{record_id}", response_model=RecordResponse,
              summary="Update a record (admin only)")
def update_record(
    record_id: int,
    data: RecordUpdate,
    db: Annotated[Session, Depends(get_db)] = None,
    actor: Annotated[User, Depends(require_admin)] = None,
):
    return RecordService.update_record(db, record_id, data, actor)


@router.delete("/{record_id}", status_code=204, summary="Soft-delete a record (admin only)")
def delete_record(
    record_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    actor: Annotated[User, Depends(require_admin)] = None,
):
    RecordService.delete_record(db, record_id, actor)
