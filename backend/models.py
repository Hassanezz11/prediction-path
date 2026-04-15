from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), default="user", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    profile: Mapped["StudentProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_branch: Mapped[str | None] = mapped_column(String(20), nullable=True)
    program_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")
    grade_submissions: Mapped[list["GradeSubmission"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    cv_uploads: Mapped[list["CVUpload"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    opportunity_searches: Mapped[list["OpportunitySearch"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class GradeSubmission(Base):
    __tablename__ = "grade_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(50))
    preferred_branch: Mapped[str] = mapped_column(String(20))
    module_grades: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped[StudentProfile] = relationship(back_populates="grade_submissions")
    prediction_result: Mapped["PredictionResult"] = relationship(back_populates="grade_submission", uselist=False, cascade="all, delete-orphan")


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grade_submission_id: Mapped[int] = mapped_column(ForeignKey("grade_submissions.id"), unique=True, index=True)
    predicted_branch: Mapped[str] = mapped_column(String(20), index=True)
    probabilities: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(255))
    gap_analysis: Mapped[dict] = mapped_column(JSON)
    recommended_courses: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grade_submission: Mapped[GradeSubmission] = relationship(back_populates="prediction_result")


class CVUpload(Base):
    __tablename__ = "cv_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped[StudentProfile] = relationship(back_populates="cv_uploads")
    analyses: Mapped[list["CVAnalysis"]] = relationship(back_populates="cv_upload", cascade="all, delete-orphan")


class CVAnalysis(Base):
    __tablename__ = "cv_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cv_upload_id: Mapped[int] = mapped_column(ForeignKey("cv_uploads.id"), index=True)
    recommended_branch: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extracted_text_checksum: Mapped[str] = mapped_column(String(128))
    full_analysis_output: Mapped[str] = mapped_column(Text)
    ollama_model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    cv_upload: Mapped[CVUpload] = relationship(back_populates="analyses")


class OpportunitySearch(Base):
    __tablename__ = "opportunity_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    branch: Mapped[str] = mapped_column(String(20))
    gpa: Mapped[str] = mapped_column(String(20))
    result_snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped[StudentProfile] = relationship(back_populates="opportunity_searches")
