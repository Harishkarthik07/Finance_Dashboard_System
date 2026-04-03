from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.dashboard import DashboardSummary, CategoryTotal, MonthlyTrend, RecentActivity


class DashboardService:

    @staticmethod
    def _active_records(db: Session):
        return db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)  # noqa: E712

    @staticmethod
    def get_summary(db: Session) -> DashboardSummary:
        base = DashboardService._active_records(db)

        # Totals
        totals = base.with_entities(
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        ).group_by(FinancialRecord.type).all()

        total_income = 0.0
        total_expense = 0.0
        for row in totals:
            if row.type == RecordType.INCOME:
                total_income = float(row.total or 0)
            else:
                total_expense = float(row.total or 0)

        # Category breakdowns
        cat_rows = base.with_entities(
            FinancialRecord.type,
            FinancialRecord.category,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        ).group_by(FinancialRecord.type, FinancialRecord.category).all()

        income_by_category = [
            CategoryTotal(category=r.category.value, total=float(r.total or 0), count=r.count)
            for r in cat_rows if r.type == RecordType.INCOME
        ]
        expense_by_category = [
            CategoryTotal(category=r.category.value, total=float(r.total or 0), count=r.count)
            for r in cat_rows if r.type == RecordType.EXPENSE
        ]

        # Monthly trends (last 12 months)
        monthly_rows = base.with_entities(
            extract("year", FinancialRecord.date).label("year"),
            extract("month", FinancialRecord.date).label("month"),
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        ).group_by("year", "month", FinancialRecord.type).order_by("year", "month").all()

        # Aggregate into month buckets
        trends: dict[tuple, dict] = {}
        for row in monthly_rows:
            key = (int(row.year), int(row.month))
            if key not in trends:
                trends[key] = {"income": 0.0, "expense": 0.0}
            if row.type == RecordType.INCOME:
                trends[key]["income"] = float(row.total or 0)
            else:
                trends[key]["expense"] = float(row.total or 0)

        monthly_trends = [
            MonthlyTrend(
                year=k[0],
                month=k[1],
                income=v["income"],
                expense=v["expense"],
                net=v["income"] - v["expense"],
            )
            for k, v in sorted(trends.items())
        ]

        # Recent activity (last 10)
        recent_records = (
            base.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc()).limit(10).all()
        )
        recent_activity = [
            RecentActivity(
                id=r.id,
                amount=float(r.amount),
                type=r.type.value,
                category=r.category.value,
                date=str(r.date),
                description=r.description,
            )
            for r in recent_records
        ]

        return DashboardSummary(
            total_income=total_income,
            total_expense=total_expense,
            net_balance=total_income - total_expense,
            total_records=base.count(),
            income_by_category=income_by_category,
            expense_by_category=expense_by_category,
            monthly_trends=monthly_trends,
            recent_activity=recent_activity,
        )
