from tests.conftest import make_user, auth_header
from app.models.user import UserRole

RECORD_PAYLOAD = {
    "amount": 1500.00,
    "type": "income",
    "category": "salary",
    "date": "2024-03-15",
    "description": "Monthly salary",
}


def test_admin_can_create_record(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    res = client.post("/api/v1/records/", json=RECORD_PAYLOAD, headers=auth_header(admin))
    assert res.status_code == 201
    assert res.json()["amount"] == 1500.0
    assert res.json()["type"] == "income"


def test_viewer_cannot_create_record(client, db):
    viewer = make_user(db, "viewer@test.com", UserRole.VIEWER)
    res = client.post("/api/v1/records/", json=RECORD_PAYLOAD, headers=auth_header(viewer))
    assert res.status_code == 403


def test_analyst_cannot_create_record(client, db):
    analyst = make_user(db, "analyst@test.com", UserRole.ANALYST)
    res = client.post("/api/v1/records/", json=RECORD_PAYLOAD, headers=auth_header(analyst))
    assert res.status_code == 403


def test_viewer_can_list_records(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    viewer = make_user(db, "viewer@test.com", UserRole.VIEWER)
    client.post("/api/v1/records/", json=RECORD_PAYLOAD, headers=auth_header(admin))

    res = client.get("/api/v1/records/", headers=auth_header(viewer))
    assert res.status_code == 200
    assert res.json()["total"] == 1


def test_filter_by_type(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    client.post("/api/v1/records/", json=RECORD_PAYLOAD, headers=auth_header(admin))
    client.post("/api/v1/records/", json={**RECORD_PAYLOAD, "type": "expense", "category": "food"},
                headers=auth_header(admin))

    res = client.get("/api/v1/records/?type=income", headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["type"] == "income"


def test_admin_can_update_record(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    create_res = client.post("/api/v1/records/", json=RECORD_PAYLOAD, headers=auth_header(admin))
    record_id = create_res.json()["id"]

    res = client.patch(f"/api/v1/records/{record_id}", json={"amount": 2000.00},
                       headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["amount"] == 2000.0


def test_admin_can_soft_delete_record(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    create_res = client.post("/api/v1/records/", json=RECORD_PAYLOAD, headers=auth_header(admin))
    record_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/records/{record_id}", headers=auth_header(admin))
    assert del_res.status_code == 204

    # Should no longer appear in list
    list_res = client.get("/api/v1/records/", headers=auth_header(admin))
    assert list_res.json()["total"] == 0


def test_invalid_amount_rejected(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    res = client.post("/api/v1/records/", json={**RECORD_PAYLOAD, "amount": -100},
                      headers=auth_header(admin))
    assert res.status_code == 422


def test_pagination(client, db):
    admin = make_user(db, "admin@test.com", UserRole.ADMIN)
    for i in range(5):
        client.post("/api/v1/records/", json={**RECORD_PAYLOAD, "amount": 100 * (i + 1)},
                    headers=auth_header(admin))

    res = client.get("/api/v1/records/?page=1&page_size=2", headers=auth_header(admin))
    assert res.json()["total"] == 5
    assert len(res.json()["items"]) == 2
