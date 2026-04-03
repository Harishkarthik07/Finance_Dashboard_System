from tests.conftest import make_user, auth_header
from app.models.user import UserRole


def test_admin_can_list_users(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    make_user(db, "viewer@test.com", UserRole.VIEWER)
    res = client.get("/api/v1/users/", headers=auth_header(admin))
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_viewer_cannot_list_users(client, db):
    viewer = make_user(db, "viewer@test.com", UserRole.VIEWER)
    res = client.get("/api/v1/users/", headers=auth_header(viewer))
    assert res.status_code == 403


def test_admin_can_create_user_with_role(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    res = client.post("/api/v1/users/", json={
        "email": "newanalyst@test.com",
        "full_name": "New Analyst",
        "password": "pass1234",
        "role": "analyst",
    }, headers=auth_header(admin))
    assert res.status_code == 201
    assert res.json()["role"] == "analyst"


def test_admin_can_deactivate_user(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    user = make_user(db, "target@test.com", UserRole.VIEWER)
    res = client.patch(f"/api/v1/users/{user.id}", json={"is_active": False},
                       headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["is_active"] is False


def test_deactivated_user_cannot_login(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    user = make_user(db, "inactive@test.com", UserRole.VIEWER, password="pass1234")
    client.patch(f"/api/v1/users/{user.id}", json={"is_active": False},
                 headers=auth_header(admin))

    res = client.post("/api/v1/auth/login", json={
        "email": "inactive@test.com",
        "password": "pass1234",
    })
    assert res.status_code == 403


def test_admin_cannot_delete_self(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    res = client.delete(f"/api/v1/users/{admin.id}", headers=auth_header(admin))
    assert res.status_code == 400


def test_admin_can_delete_other_user(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    user = make_user(db, "todelete@test.com", UserRole.VIEWER)
    res = client.delete(f"/api/v1/users/{user.id}", headers=auth_header(admin))
    assert res.status_code == 204
