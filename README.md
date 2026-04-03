# Finance Dashboard API

A production-quality REST backend built with **FastAPI** for managing financial records with role-based access control, analytics, and JWT authentication.

---

## Features

| Category | Details |
|---|---|
| **Auth** | JWT Bearer tokens via `/auth/login` and `/auth/register` |
| **RBAC** | Three roles: `viewer`, `analyst`, `admin` — enforced at the dependency layer |
| **Financial Records** | Full CRUD with soft-delete, filtering by type/category/date, pagination |
| **Dashboard Analytics** | Total income/expense, net balance, category breakdowns, monthly trends, recent activity |
| **Validation** | Pydantic v2 schemas with field-level validators and structured error responses |
| **Tests** | 14 integration tests covering auth, RBAC, record CRUD, filtering, and dashboard |

---

## Tech Stack

- **Framework**: FastAPI 0.111
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite (zero setup) — swap `DATABASE_URL` in `.env` for PostgreSQL/MySQL
- **Auth**: `python-jose` (JWT) + `passlib[bcrypt]` (password hashing)
- **Validation**: Pydantic v2
- **Testing**: pytest + HTTPX TestClient with in-memory SQLite

---

## Project Structure

```
finance_api/
├── app/
│   ├── main.py                   # App factory, middleware, error handlers, lifespan
│   ├── api/v1/
│   │   ├── router.py             # Aggregates all routers under /api/v1
│   │   └── endpoints/
│   │       ├── auth.py           # /auth/register, /auth/login
│   │       ├── users.py          # /users/ (admin-managed)
│   │       ├── records.py        # /records/ (CRUD + filters)
│   │       └── dashboard.py      # /dashboard/summary
│   ├── core/
│   │   ├── config.py             # Settings via pydantic-settings (.env support)
│   │   ├── security.py           # JWT encode/decode, password hashing
│   │   └── dependencies.py       # Auth + role enforcement factories
│   ├── db/database.py            # Engine, session, Base, init_db
│   ├── models/
│   │   ├── user.py               # User model + UserRole enum
│   │   └── financial_record.py   # FinancialRecord model + enums
│   ├── schemas/
│   │   ├── user.py               # Request/response schemas
│   │   ├── financial_record.py   # Record schemas + filters
│   │   └── dashboard.py          # Analytics response schemas
│   └── services/
│       ├── user_service.py       # User business logic
│       ├── record_service.py     # Record business logic
│       └── dashboard_service.py  # Analytics aggregations
├── tests/test_api.py             # 14 integration tests
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Setup & Run

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Run tests

```bash
pytest tests/ -v
```

### Optional: .env file

```env
SECRET_KEY=your-very-secret-key
DATABASE_URL=sqlite:///./finance.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost:5432/finance_db
```

---

## Default Credentials

On first startup, a default admin is automatically seeded:

| Field | Value |
|---|---|
| Email | `admin@finance.dev` |
| Password | `admin1234` |
| Role | `admin` |

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | None | Register (always creates `viewer`) |
| `POST` | `/api/v1/auth/login` | None | Login → returns JWT token |

### Users

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | Any | Get own profile |
| `GET` | `/api/v1/users/` | Admin | List all users |
| `POST` | `/api/v1/users/` | Admin | Create user with any role |
| `GET` | `/api/v1/users/{id}` | Admin | Get user by ID |
| `PATCH` | `/api/v1/users/{id}` | Admin | Update name / role / status |
| `DELETE` | `/api/v1/users/{id}` | Admin | Delete user |

### Financial Records

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/records/` | Viewer+ | List (paginated, filterable) |
| `GET` | `/api/v1/records/{id}` | Viewer+ | Get single record |
| `POST` | `/api/v1/records/` | Admin | Create record |
| `PATCH` | `/api/v1/records/{id}` | Admin | Update record |
| `DELETE` | `/api/v1/records/{id}` | Admin | Soft-delete record |

**Query filters:** `type`, `category`, `date_from`, `date_to`, `page`, `page_size`

**Categories:** `salary`, `freelance`, `investment`, `food`, `transport`, `utilities`, `entertainment`, `healthcare`, `education`, `rent`, `other`

### Dashboard

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | Analyst+ | Full analytics summary |

Dashboard response includes: `total_income`, `total_expense`, `net_balance`, `total_records`, `income_by_category`, `expense_by_category`, `monthly_trends`, `recent_activity`.

---

## Role-Based Access Control

```
Viewer   → Read records only
Analyst  → Read records + dashboard analytics
Admin    → Full access: CRUD records + manage all users
```

Implemented as a `require_roles()` factory in `core/dependencies.py`:

```python
def require_roles(*roles: UserRole):
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(403, "Access denied.")
        return current_user
    return role_checker

require_admin            = require_roles(UserRole.ADMIN)
require_analyst_or_above = require_roles(UserRole.ANALYST, UserRole.ADMIN)
require_viewer_or_above  = require_roles(UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN)
```

---

## Assumptions & Design Decisions

| Decision | Rationale |
|---|---|
| Public registration always creates `viewer` | Prevents privilege escalation. Admins upgrade roles via `PATCH /users/{id}`. |
| Soft delete for records | Financial records shouldn't be hard-deleted — preserves audit trail. |
| SQLite as default | Zero setup for evaluation. No code changes needed to switch to PostgreSQL. |
| Admin seeded on startup | Bootstraps the system so you can immediately test all features. |
| Analyst cannot mutate records | Analysts are read-heavy roles. Record mutations are admin-only operations. |
| Single `/dashboard/summary` endpoint | Reduces round-trips for dashboard load. Easily split per widget if needed. |
| `Numeric(12,2)` in DB | Ensures monetary precision at the persistence layer. |
