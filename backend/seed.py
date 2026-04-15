from __future__ import annotations

from sqlalchemy import select

from backend.database import Base, SessionLocal, engine
from backend.models import StudentProfile, User
from backend.security import hash_password


def seed_admin(email: str = "admin@example.com", password: str = "Admin12345!") -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            return
        admin = User(email=email, password_hash=hash_password(password), role="admin")
        admin.profile = StudentProfile(
            full_name="Platform Admin",
            preferred_branch="IADATA",
            program_info={"seeded": True},
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
