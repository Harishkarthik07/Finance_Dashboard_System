from typing import Optional
from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category: str
    total: float
    count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    net: float


class RecentActivity(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    date: str
    description: Optional[str]


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    total_records: int
    income_by_category: list[CategoryTotal]
    expense_by_category: list[CategoryTotal]
    monthly_trends: list[MonthlyTrend]
    recent_activity: list[RecentActivity]
