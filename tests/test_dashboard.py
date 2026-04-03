from tests.conftest import make_user, auth_header
from app.models.user import UserRole

INCOME = {"amount": 3000, "type": "income", "category": "salary", "date": "2024-03-01"}
EXPENSE = {"amount": 500, "type": "expense", "category": "food", "date": "2024-03-05"}


def seed_records(client, admin_headers):
    client.post("/api/v1/records/", json=INCOME, headers=admin_headers)
    client.post("/api/v1/records/", json=EXPENSE, headers=admin_headers)


def test_analyst_can_see_dashboard(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    analyst = make_user(db, "analyst@test.com", UserRole.ANALYST)
    seed_records(client, auth_header(admin))

    res = client.get("/api/v1/dashboard/summary", headers=auth_header(analyst))
    assert res.status_code == 200
    data = res.json()
    assert data["total_income"] == 3000.0
    assert data["total_expense"] == 500.0
    assert data["net_balance"] == 2500.0
    assert data["total_records"] == 2


def test_admin_can_see_dashboard(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    seed_records(client, auth_header(admin))

    res = client.get("/api/v1/dashboard/summary", headers=auth_header(admin))
    assert res.status_code == 200


def test_viewer_cannot_see_dashboard(client, db):
    viewer = make_user(db, "viewer@test.com", UserRole.VIEWER)
    res = client.get("/api/v1/dashboard/summary", headers=auth_header(viewer))
    assert res.status_code == 403


def test_dashboard_category_breakdown(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    seed_records(client, auth_header(admin))

    res = client.get("/api/v1/dashboard/summary", headers=auth_header(admin))
    data = res.json()
    assert len(data["income_by_category"]) == 1
    assert data["income_by_category"][0]["category"] == "salary"
    assert len(data["expense_by_category"]) == 1
    assert data["expense_by_category"][0]["category"] == "food"


def test_dashboard_recent_activity(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    seed_records(client, auth_header(admin))

    res = client.get("/api/v1/dashboard/summary", headers=auth_header(admin))
    assert len(res.json()["recent_activity"]) == 2
