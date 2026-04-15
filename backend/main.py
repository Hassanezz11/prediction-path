from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.config import settings
from backend.database import Base, engine, get_db
from backend.deps import get_current_profile, get_current_user, require_admin
from backend.domain import BRANCH_OPTIONS
from backend.models import CVAnalysis, CVUpload, GradeSubmission, OpportunitySearch, PredictionResult, StudentProfile, User
from backend.schemas import (
    AdminCreateUserRequest,
    AuthResponse,
    CVUploadResponse,
    DashboardResponse,
    LoginRequest,
    OpportunitySearchRequest,
    OpportunitySearchResponse,
    PredictionRequest,
    PredictionResponse,
    ProfileSummary,
    StudentDetailResponse,
    StudentListItem,
    UserSummary,
)
from backend.security import create_access_token, hash_password, verify_password
from backend.services.cv_service import analyze_cv, extract_pdf_text, save_upload
from backend.services.opportunity_service import search_opportunities
from backend.services.prediction_service import predict_branch


def serialize_prediction(result: PredictionResult) -> dict:
    return {
        "id": result.id,
        "predicted_branch": result.predicted_branch,
        "probabilities": result.probabilities,
        "model_version": result.model_version,
        "gap_analysis": result.gap_analysis,
        "recommended_courses": result.recommended_courses,
        "created_at": result.created_at.isoformat(),
        "grade_submission_id": result.grade_submission_id,
    }


def serialize_grade_submission(submission: GradeSubmission) -> dict:
    return {
        "id": submission.id,
        "age": submission.age,
        "gender": submission.gender,
        "preferred_branch": submission.preferred_branch,
        "module_grades": submission.module_grades,
        "created_at": submission.created_at.isoformat(),
    }


def serialize_cv_upload(upload: CVUpload) -> dict:
    return {
        "id": upload.id,
        "original_filename": upload.original_filename,
        "storage_path": upload.storage_path,
        "mime_type": upload.mime_type,
        "size_bytes": upload.size_bytes,
        "uploaded_at": upload.uploaded_at.isoformat(),
    }


def serialize_cv_analysis(analysis: CVAnalysis) -> dict:
    return {
        "id": analysis.id,
        "cv_upload_id": analysis.cv_upload_id,
        "recommended_branch": analysis.recommended_branch,
        "confidence": analysis.confidence,
        "full_analysis_output": analysis.full_analysis_output,
        "ollama_model": analysis.ollama_model,
        "created_at": analysis.created_at.isoformat(),
    }


def serialize_search(search: OpportunitySearch) -> dict:
    return {
        "id": search.id,
        "branch": search.branch,
        "gpa": float(search.gpa),
        "result_snapshot": search.result_snapshot,
        "created_at": search.created_at.isoformat(),
    }


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    Base.metadata.create_all(bind=engine)

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(static_dir / "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.post("/api/auth/login", response_model=AuthResponse)
    def login(payload: LoginRequest, db: Session = Depends(get_db)):
        user = db.scalar(select(User).where(User.email == payload.email))
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        return AuthResponse(
            access_token=create_access_token(user.id, user.role),
            user=UserSummary.model_validate(user),
            profile=ProfileSummary.model_validate(user.profile) if user.profile else None,
        )

    @app.get("/api/me", response_model=AuthResponse)
    def me(current_user: User = Depends(get_current_user)):
        return AuthResponse(
            access_token=create_access_token(current_user.id, current_user.role),
            user=UserSummary.model_validate(current_user),
            profile=ProfileSummary.model_validate(current_user.profile) if current_user.profile else None,
        )

    @app.post("/api/admin/users", response_model=AuthResponse)
    def create_user(
        payload: AdminCreateUserRequest,
        _admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
        user.profile = StudentProfile(
            full_name=payload.full_name,
            age=payload.age,
            gender=payload.gender,
            preferred_branch=payload.preferred_branch,
            program_info=payload.program_info or {},
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return AuthResponse(
            access_token=create_access_token(user.id, user.role),
            user=UserSummary.model_validate(user),
            profile=ProfileSummary.model_validate(user.profile),
        )

    @app.get("/api/admin/students", response_model=list[StudentListItem])
    def list_students(
        query: str | None = Query(default=None),
        branch: str | None = Query(default=None),
        _admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        stmt = (
            select(StudentProfile)
            .join(StudentProfile.user)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.grade_submissions).selectinload(GradeSubmission.prediction_result),
                selectinload(StudentProfile.cv_uploads),
                selectinload(StudentProfile.opportunity_searches),
            )
        )
        if query:
            stmt = stmt.where((StudentProfile.full_name.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
        if branch:
            stmt = stmt.where(StudentProfile.preferred_branch == branch)
        profiles = db.scalars(stmt.order_by(StudentProfile.updated_at.desc())).all()
        items = []
        for profile in profiles:
            latest_dates = []
            if profile.grade_submissions:
                latest_dates.append(max(item.created_at for item in profile.grade_submissions))
            if profile.cv_uploads:
                latest_dates.append(max(item.uploaded_at for item in profile.cv_uploads))
            if profile.opportunity_searches:
                latest_dates.append(max(item.created_at for item in profile.opportunity_searches))
            items.append(
                StudentListItem(
                    user_id=profile.user.id,
                    student_id=profile.id,
                    email=profile.user.email,
                    full_name=profile.full_name,
                    preferred_branch=profile.preferred_branch,
                    last_activity=max(latest_dates) if latest_dates else None,
                    predictions_count=sum(1 for item in profile.grade_submissions if item.prediction_result),
                    cv_count=len(profile.cv_uploads),
                )
            )
        return items

    @app.get("/api/admin/students/{student_id}", response_model=StudentDetailResponse)
    def get_student_detail(student_id: int, _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        profile = db.scalar(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.grade_submissions).selectinload(GradeSubmission.prediction_result),
                selectinload(StudentProfile.cv_uploads).selectinload(CVUpload.analyses),
                selectinload(StudentProfile.opportunity_searches),
            )
        )
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        return StudentDetailResponse(
            user=UserSummary.model_validate(profile.user),
            profile=ProfileSummary.model_validate(profile),
            grade_submissions=[serialize_grade_submission(item) for item in profile.grade_submissions],
            prediction_results=[
                serialize_prediction(item.prediction_result)
                for item in profile.grade_submissions
                if item.prediction_result is not None
            ],
            cv_uploads=[serialize_cv_upload(item) for item in profile.cv_uploads],
            cv_analyses=[
                serialize_cv_analysis(analysis)
                for upload in profile.cv_uploads
                for analysis in upload.analyses
            ],
            opportunity_searches=[serialize_search(item) for item in profile.opportunity_searches],
        )

    @app.get("/api/dashboard", response_model=DashboardResponse)
    def dashboard(current_user: User = Depends(get_current_user), profile: StudentProfile = Depends(get_current_profile)):
        latest_submission = max(profile.grade_submissions, key=lambda item: item.created_at, default=None)
        latest_prediction = None
        if latest_submission and latest_submission.prediction_result:
            latest_prediction = serialize_prediction(latest_submission.prediction_result)
        analyses = [analysis for upload in profile.cv_uploads for analysis in upload.analyses]
        recent_cv_analysis = serialize_cv_analysis(max(analyses, key=lambda item: item.created_at)) if analyses else None
        return DashboardResponse(
            user=UserSummary.model_validate(current_user),
            profile=ProfileSummary.model_validate(profile),
            latest_prediction=latest_prediction,
            recent_cv_analysis=recent_cv_analysis,
            metrics={
                "predictions": len(profile.grade_submissions),
                "cv_uploads": len(profile.cv_uploads),
                "opportunity_searches": len(profile.opportunity_searches),
            },
        )

    @app.post("/api/predictions", response_model=PredictionResponse)
    def create_prediction(
        payload: PredictionRequest,
        profile: StudentProfile = Depends(get_current_profile),
        db: Session = Depends(get_db),
    ):
        if payload.preferred_branch not in BRANCH_OPTIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid preferred branch")
        result = predict_branch(
            age=payload.age,
            gender=payload.gender,
            preferred_branch=payload.preferred_branch,
            module_grades=payload.normalized_grades(),
        )
        profile.age = payload.age
        profile.gender = payload.gender
        profile.preferred_branch = payload.preferred_branch
        submission = GradeSubmission(
            student=profile,
            age=payload.age,
            gender=payload.gender,
            preferred_branch=payload.preferred_branch,
            module_grades=payload.normalized_grades(),
        )
        prediction = PredictionResult(
            grade_submission=submission,
            predicted_branch=result["predicted_branch"],
            probabilities=result["probabilities"],
            model_version=result["model_version"],
            gap_analysis=result["gap_analysis"],
            recommended_courses=result["recommended_courses"],
        )
        db.add_all([submission, prediction])
        db.commit()
        db.refresh(prediction)
        return PredictionResponse(
            submission_id=submission.id,
            prediction_id=prediction.id,
            predicted_branch=prediction.predicted_branch,
            predicted_branch_full=result["predicted_branch_full"],
            probabilities=prediction.probabilities,
            gap_analysis=prediction.gap_analysis,
            recommended_courses=prediction.recommended_courses,
            created_at=prediction.created_at,
        )

    @app.get("/api/predictions")
    def list_predictions(profile: StudentProfile = Depends(get_current_profile)):
        return [
            serialize_prediction(item.prediction_result)
            for item in sorted(profile.grade_submissions, key=lambda row: row.created_at, reverse=True)
            if item.prediction_result
        ]

    @app.post("/api/cv/upload", response_model=CVUploadResponse)
    def upload_cv(
        file: UploadFile = File(...),
        ollama_model: str = Form(default=settings.default_ollama_model),
        profile: StudentProfile = Depends(get_current_profile),
        db: Session = Depends(get_db),
    ):
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported")
        path, size_bytes = save_upload(profile.id, file)
        upload = CVUpload(
            student=profile,
            original_filename=file.filename or path.name,
            storage_path=str(path),
            mime_type=file.content_type or "application/pdf",
            size_bytes=size_bytes,
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)

        warning = None
        analysis = None
        try:
            cv_text = extract_pdf_text(path)
            if cv_text.strip():
                analysis_payload = analyze_cv(cv_text, ollama_model)
                analysis = CVAnalysis(
                    cv_upload=upload,
                    recommended_branch=analysis_payload["recommended_branch"],
                    confidence=analysis_payload["confidence"],
                    extracted_text_checksum=analysis_payload["checksum"],
                    full_analysis_output=analysis_payload["output"],
                    ollama_model=analysis_payload["ollama_model"],
                )
                db.add(analysis)
                db.commit()
                db.refresh(analysis)
            else:
                warning = "The PDF was stored, but no extractable text was found."
        except requests.RequestException:
            warning = "The PDF was stored, but Ollama was unavailable for analysis."

        return CVUploadResponse(
            upload_id=upload.id,
            analysis_id=analysis.id if analysis else None,
            filename=upload.original_filename,
            recommended_branch=analysis.recommended_branch if analysis else None,
            confidence=analysis.confidence if analysis else None,
            analysis_output=analysis.full_analysis_output if analysis else None,
            created_at=analysis.created_at if analysis else upload.uploaded_at,
            warning=warning,
        )

    @app.get("/api/cv")
    def list_cv_uploads(profile: StudentProfile = Depends(get_current_profile)):
        return [
            {
                **serialize_cv_upload(upload),
                "analyses": [serialize_cv_analysis(analysis) for analysis in upload.analyses],
            }
            for upload in sorted(profile.cv_uploads, key=lambda row: row.uploaded_at, reverse=True)
        ]

    @app.post("/api/opportunities/search", response_model=OpportunitySearchResponse)
    def create_opportunity_search(
        payload: OpportunitySearchRequest,
        profile: StudentProfile = Depends(get_current_profile),
        db: Session = Depends(get_db),
    ):
        snapshot = search_opportunities(payload.branch, payload.gpa)
        search = OpportunitySearch(student=profile, branch=payload.branch, gpa=str(payload.gpa), result_snapshot=snapshot)
        db.add(search)
        db.commit()
        db.refresh(search)
        return OpportunitySearchResponse(
            search_id=search.id,
            branch=search.branch,
            gpa=float(search.gpa),
            result_snapshot=search.result_snapshot,
            created_at=search.created_at,
        )

    @app.get("/api/opportunities/history")
    def list_opportunity_history(profile: StudentProfile = Depends(get_current_profile)):
        return [serialize_search(item) for item in sorted(profile.opportunity_searches, key=lambda row: row.created_at, reverse=True)]

    return app


app = create_app()
