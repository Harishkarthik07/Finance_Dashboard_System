from tests.conftest import make_user, auth_header
from app.models.user import UserRole


def test_register_creates_viewer(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "full_name": "New User",
        "password": "pass1234",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "viewer"


def test_register_duplicate_email(client, db):
    make_user(db, "dup@test.com", UserRole.VIEWER)
    res = client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "full_name": "Dup User",
        "password": "pass1234",
    })
    assert res.status_code == 409


def test_register_short_password(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "x@x.com",
        "full_name": "X",
        "password": "abc",
    })
    assert res.status_code == 422


def test_login_success(client, db):
    make_user(db, "login@test.com", UserRole.VIEWER, password="mypassword")
    res = client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "mypassword",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client, db):
    make_user(db, "wrong@test.com", UserRole.VIEWER, password="correct")
    res = client.post("/api/v1/auth/login", json={
        "email": "wrong@test.com",
        "password": "wrong",
    })
    assert res.status_code == 401


def test_get_me(client, db):
    user = make_user(db, "me@test.com", UserRole.ANALYST)
    res = client.get("/api/v1/users/me", headers=auth_header(user))
    assert res.status_code == 200
    assert res.json()["email"] == "me@test.com"


def test_get_me_no_token(client):
    res = client.get("/api/v1/users/me")
    assert res.status_code == 403
