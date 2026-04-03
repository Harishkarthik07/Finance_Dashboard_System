"""
Integration tests for the Finance Dashboard API.
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_finance.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    from app.models import user, financial_record  # noqa
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def register_and_login(client, email, password, full_name="Test User"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": password, "full_name": full_name
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com", "password": "pass123", "full_name": "New User",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "viewer"

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@test.com", "password": "pass123", "full_name": "Dup"}
        client.post("/api/v1/auth/register", json=payload)
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_weak_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "weak@test.com", "password": "abc", "full_name": "Weak"
        })
        assert resp.status_code == 422

    def test_login_success(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "logintest@test.com", "password": "pass123", "full_name": "Login Test"
        })
        resp = client.post("/api/v1/auth/login", json={
            "email": "logintest@test.com", "password": "pass123"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "logintest@test.com", "password": "wrongpass"
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "ghost@test.com", "password": "pass123"
        })
        assert resp.status_code == 401


class TestUsers:
    @pytest.fixture(autouse=True)
    def tokens(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "admin@finance.com", "password": "admin123"
        })
        self.admin_token = resp.json()["access_token"]
        self.viewer_token = register_and_login(client, "viewer_u@test.com", "pass123", "Viewer User")

    def test_get_me(self, client):
        resp = client.get("/api/v1/users/me", headers=auth_headers(self.admin_token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_list_users_admin(self, client):
        resp = client.get("/api/v1/users/", headers=auth_headers(self.admin_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_users_viewer_forbidden(self, client):
        resp = client.get("/api/v1/users/", headers=auth_headers(self.viewer_token))
        assert resp.status_code == 403

    def test_admin_create_user_with_role(self, client):
        resp = client.post("/api/v1/users/", headers=auth_headers(self.admin_token), json={
            "email": "analyst_a@test.com", "password": "pass123",
            "full_name": "Analyst A", "role": "analyst",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "analyst"

    def test_update_user_role(self, client):
        create_resp = client.post("/api/v1/users/", headers=auth_headers(self.admin_token), json={
            "email": "promote@test.com", "password": "pass123",
            "full_name": "Promote Me", "role": "viewer"
        })
        user_id = create_resp.json()["id"]
        resp = client.patch(f"/api/v1/users/{user_id}",
                            headers=auth_headers(self.admin_token),
                            json={"role": "analyst"})
        assert resp.status_code == 200
        assert resp.json()["role"] == "analyst"

    def test_deactivate_user(self, client):
        create_resp = client.post("/api/v1/users/", headers=auth_headers(self.admin_token), json={
            "email": "deactivate@test.com", "password": "pass123",
            "full_name": "Deactivate Me", "role": "viewer"
        })
        user_id = create_resp.json()["id"]
        resp = client.patch(f"/api/v1/users/{user_id}",
                            headers=auth_headers(self.admin_token),
                            json={"is_active": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False


class TestRecords:
    @pytest.fixture(autouse=True)
    def tokens(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "admin@finance.com", "password": "admin123"
        })
        self.admin_token = resp.json()["access_token"]
        self.viewer_token = register_and_login(client, "view2@test.com", "pass123", "Viewer 2")
        client.post("/api/v1/users/", headers=auth_headers(self.admin_token), json={
            "email": "analyst2@test.com", "password": "pass123",
            "full_name": "Analyst 2", "role": "analyst"
        })
        resp2 = client.post("/api/v1/auth/login", json={
            "email": "analyst2@test.com", "password": "pass123"
        })
        self.analyst_token = resp2.json()["access_token"]

    def _create_record(self, client, overrides=None):
        payload = {
            "amount": 5000.00, "type": "income",
            "category": "salary", "date": "2024-06-15", "description": "June salary",
        }
        if overrides:
            payload.update(overrides)
        return client.post("/api/v1/records/", headers=auth_headers(self.admin_token), json=payload)

    def test_create_record_admin(self, client):
        resp = self._create_record(client)
        assert resp.status_code == 201
        assert resp.json()["amount"] == 5000.0

    def test_create_record_viewer_forbidden(self, client):
        resp = client.post("/api/v1/records/", headers=auth_headers(self.viewer_token),
                           json={"amount": 100, "type": "expense", "category": "food", "date": "2024-06-01"})
        assert resp.status_code == 403

    def test_create_record_negative_amount(self, client):
        assert self._create_record(client, {"amount": -100}).status_code == 422

    def test_create_record_zero_amount(self, client):
        assert self._create_record(client, {"amount": 0}).status_code == 422

    def test_list_records_viewer(self, client):
        resp = client.get("/api/v1/records/", headers=auth_headers(self.viewer_token))
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_list_records_filter_by_type(self, client):
        resp = client.get("/api/v1/records/?type=income", headers=auth_headers(self.viewer_token))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["type"] == "income"

    def test_list_records_pagination(self, client):
        resp = client.get("/api/v1/records/?page=1&page_size=2", headers=auth_headers(self.viewer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1 and data["page_size"] == 2

    def test_get_record_by_id(self, client):
        record_id = self._create_record(client).json()["id"]
        resp = client.get(f"/api/v1/records/{record_id}", headers=auth_headers(self.viewer_token))
        assert resp.status_code == 200

    def test_get_nonexistent_record(self, client):
        resp = client.get("/api/v1/records/99999", headers=auth_headers(self.viewer_token))
        assert resp.status_code == 404

    def test_update_record_admin(self, client):
        record_id = self._create_record(client).json()["id"]
        resp = client.patch(f"/api/v1/records/{record_id}",
                            headers=auth_headers(self.admin_token), json={"amount": 6000.00})
        assert resp.status_code == 200
        assert resp.json()["amount"] == 6000.0

    def test_update_record_viewer_forbidden(self, client):
        record_id = self._create_record(client).json()["id"]
        resp = client.patch(f"/api/v1/records/{record_id}",
                            headers=auth_headers(self.viewer_token), json={"amount": 9999})
        assert resp.status_code == 403

    def test_delete_record_soft(self, client):
        record_id = self._create_record(client).json()["id"]
        assert client.delete(f"/api/v1/records/{record_id}",
                             headers=auth_headers(self.admin_token)).status_code == 204
        assert client.get(f"/api/v1/records/{record_id}",
                          headers=auth_headers(self.viewer_token)).status_code == 404

    def test_delete_record_viewer_forbidden(self, client):
        record_id = self._create_record(client).json()["id"]
        assert client.delete(f"/api/v1/records/{record_id}",
                             headers=auth_headers(self.viewer_token)).status_code == 403


class TestDashboard:
    @pytest.fixture(autouse=True)
    def tokens(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "admin@finance.com", "password": "admin123"
        })
        self.admin_token = resp.json()["access_token"]
        self.viewer_token = register_and_login(client, "view3@test.com", "pass123", "Viewer 3")
        client.post("/api/v1/users/", headers=auth_headers(self.admin_token), json={
            "email": "analyst3@test.com", "password": "pass123",
            "full_name": "Analyst 3", "role": "analyst"
        })
        resp2 = client.post("/api/v1/auth/login", json={"email": "analyst3@test.com", "password": "pass123"})
        self.analyst_token = resp2.json()["access_token"]

    def test_summary_analyst(self, client):
        resp = client.get("/api/v1/dashboard/summary", headers=auth_headers(self.analyst_token))
        assert resp.status_code == 200
        data = resp.json()
        for key in ("total_income", "total_expense", "net_balance", "monthly_trends", "recent_activity"):
            assert key in data

    def test_summary_admin(self, client):
        assert client.get("/api/v1/dashboard/summary",
                          headers=auth_headers(self.admin_token)).status_code == 200

    def test_summary_viewer_forbidden(self, client):
        assert client.get("/api/v1/dashboard/summary",
                          headers=auth_headers(self.viewer_token)).status_code == 403

    def test_net_balance_math(self, client):
        data = client.get("/api/v1/dashboard/summary",
                          headers=auth_headers(self.admin_token)).json()
        assert round(data["net_balance"], 2) == round(data["total_income"] - data["total_expense"], 2)
