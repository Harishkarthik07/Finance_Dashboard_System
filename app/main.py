from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables and seed data on startup."""
    init_db()
    seed_initial_data()
    yield


def seed_initial_data():
    """Create a default admin user if none exists."""
    from app.db.database import SessionLocal
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == UserRole.ADMIN).first():
            admin = User(
                email="admin@finance.com",
                full_name="System Admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            db.commit()
            print("✅ Default admin created: admin@finance.com / admin123")
    finally:
        db.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
 Finance Dashboard System

A role-based access control backend for managing financial records and analytics.

 Roles
| Role     | Permissions |
|----------|-------------|
| viewer  | Read records only |
| analyst | Read records + dashboard analytics |
| admin   | Full access: users, records, dashboard |

 Quick Start
1. Login with `POST /api/v1/auth/login` using `admin@finance.com` / `admin123`
2. Copy the `access_token` from the response
3. Click "Authorize" above and enter: `Bearer <your_token>`
4. Explore the API !
""",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


app.include_router(api_router)


@app.get("/", tags=["Health"], summary="Health check")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
