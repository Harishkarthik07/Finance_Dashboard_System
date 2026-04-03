from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import require_analyst_or_above
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary,
            summary="Full dashboard summary (analyst+)")
def get_summary(
    db: Annotated[Session, Depends(get_db)] = None,
    _: Annotated[User, Depends(require_analyst_or_above)] = None,
):
    return DashboardService.get_summary(db)
