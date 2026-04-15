from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.domain import ALL_MODULE_KEYS, BRANCH_META, BRANCH_OPTIONS, SEMESTERS


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str
    is_active: bool


class ProfileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    age: int | None
    gender: str | None
    preferred_branch: str | None
    program_info: dict[str, Any] | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary
    profile: ProfileSummary | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class AdminCreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    age: int | None = Field(default=None, ge=17, le=60)
    gender: str | None = None
    preferred_branch: str | None = None
    program_info: dict[str, Any] | None = None
    role: str = Field(default="user")


class PredictionRequest(BaseModel):
    age: int = Field(ge=17, le=60)
    gender: str
    preferred_branch: str
    module_grades: dict[str, float]

    def normalized_grades(self) -> dict[str, float]:
        return {key: float(self.module_grades.get(key, 0.0)) for key in ALL_MODULE_KEYS}


class PredictionResponse(BaseModel):
    submission_id: int
    prediction_id: int
    predicted_branch: str
    predicted_branch_full: str
    probabilities: dict[str, float]
    gap_analysis: dict[str, Any]
    recommended_courses: list[dict[str, Any]]
    created_at: datetime


class CVUploadResponse(BaseModel):
    upload_id: int
    analysis_id: int | None = None
    filename: str
    recommended_branch: str | None = None
    confidence: str | None = None
    analysis_output: str | None = None
    created_at: datetime
    warning: str | None = None


class OpportunitySearchRequest(BaseModel):
    branch: str
    gpa: float = Field(ge=0, le=20)


class OpportunitySearchResponse(BaseModel):
    search_id: int
    branch: str
    gpa: float
    result_snapshot: dict[str, Any]
    created_at: datetime


class StudentListItem(BaseModel):
    user_id: int
    student_id: int
    email: str
    full_name: str
    preferred_branch: str | None = None
    last_activity: datetime | None = None
    predictions_count: int
    cv_count: int


class StudentDetailResponse(BaseModel):
    user: UserSummary
    profile: ProfileSummary
    grade_submissions: list[dict[str, Any]]
    prediction_results: list[dict[str, Any]]
    cv_uploads: list[dict[str, Any]]
    cv_analyses: list[dict[str, Any]]
    opportunity_searches: list[dict[str, Any]]


class DashboardResponse(BaseModel):
    user: UserSummary
    profile: ProfileSummary | None
    latest_prediction: dict[str, Any] | None
    recent_cv_analysis: dict[str, Any] | None
    metrics: dict[str, int]
    branch_meta: dict[str, Any] = BRANCH_META
    semesters: dict[str, Any] = SEMESTERS
    branch_options: list[str] = BRANCH_OPTIONS
