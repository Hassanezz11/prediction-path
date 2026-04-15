from __future__ import annotations

import importlib
import io
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def load_app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    for name in list(sys.modules):
        if name.startswith("backend"):
            del sys.modules[name]
    backend_main = importlib.import_module("backend.main")
    return backend_main


def seed_user(db_session, models, security, email, password, role, name):
    user = models.User(email=email, password_hash=security.hash_password(password), role=role)
    user.profile = models.StudentProfile(full_name=name, preferred_branch="IADATA", gender="Male", age=21, program_info={})
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_header(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_role_protection(tmp_path, monkeypatch):
    backend_main = load_app(tmp_path, monkeypatch)
    client = TestClient(backend_main.app)
    from backend.database import SessionLocal
    from backend import models, security

    with SessionLocal() as session:
        seed_user(session, models, security, "admin@example.com", "Admin12345!", "admin", "Admin")
        seed_user(session, models, security, "student@example.com", "Student123!", "user", "Student One")

    user_headers = auth_header(client, "student@example.com", "Student123!")
    admin_headers = auth_header(client, "admin@example.com", "Admin12345!")

    assert client.get("/api/admin/students", headers=user_headers).status_code == 403
    admin_response = client.get("/api/admin/students", headers=admin_headers)
    assert admin_response.status_code == 200
    assert len(admin_response.json()) == 2


def test_prediction_cv_and_admin_detail(tmp_path, monkeypatch):
    backend_main = load_app(tmp_path, monkeypatch)
    client = TestClient(backend_main.app)
    from backend.database import SessionLocal
    from backend import models, security

    monkeypatch.setattr(
        backend_main,
        "predict_branch",
        lambda **_: {
            "predicted_branch": "IADATA",
            "predicted_branch_full": "Intelligence Artificielle & Data",
            "probabilities": {"IADATA": 0.9, "DSI": 0.05, "CIR": 0.05},
            "gap_analysis": {"preferred_branch": "IADATA", "matches_preference": True, "message": "Aligned."},
            "recommended_courses": [{"title": "ML Bootcamp"}],
            "model_version": "test-model",
        },
    )
    monkeypatch.setattr(backend_main, "search_opportunities", lambda branch, gpa: {"stages": [{"Titre": branch}], "scholarships": [{"Titre": str(gpa)}]})
    monkeypatch.setattr(backend_main, "save_upload", lambda student_id, file: (Path(tmp_path / f"{student_id}.pdf"), 128))
    monkeypatch.setattr(backend_main, "extract_pdf_text", lambda path: "python machine learning projects")
    monkeypatch.setattr(
        backend_main,
        "analyze_cv",
        lambda text, model: {
            "recommended_branch": "IADATA",
            "confidence": "High",
            "output": "Recommended Branch: IADATA",
            "checksum": "abc123",
            "ollama_model": model,
        },
    )

    with SessionLocal() as session:
        admin = seed_user(session, models, security, "admin@example.com", "Admin12345!", "admin", "Admin")
        student = seed_user(session, models, security, "student@example.com", "Student123!", "user", "Student One")
        student_id = student.profile.id

    user_headers = auth_header(client, "student@example.com", "Student123!")
    admin_headers = auth_header(client, "admin@example.com", "Admin12345!")

    module_grades = {key: 12.0 for key in importlib.import_module("backend.domain").ALL_MODULE_KEYS}
    prediction_response = client.post(
        "/api/predictions",
        headers=user_headers,
        json={"age": 21, "gender": "Male", "preferred_branch": "IADATA", "module_grades": module_grades},
    )
    assert prediction_response.status_code == 200
    assert prediction_response.json()["predicted_branch"] == "IADATA"

    cv_response = client.post(
        "/api/cv/upload",
        headers=user_headers,
        files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"ollama_model": "llama3.2"},
    )
    assert cv_response.status_code == 200
    assert cv_response.json()["recommended_branch"] == "IADATA"

    opp_response = client.post(
        "/api/opportunities/search",
        headers=user_headers,
        json={"branch": "IADATA", "gpa": 14.0},
    )
    assert opp_response.status_code == 200
    assert opp_response.json()["result_snapshot"]["stages"][0]["Titre"] == "IADATA"

    detail = client.get(f"/api/admin/students/{student_id}", headers=admin_headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["profile"]["full_name"] == "Student One"
    assert len(payload["grade_submissions"]) == 1
    assert len(payload["prediction_results"]) == 1
    assert len(payload["cv_uploads"]) == 1
    assert len(payload["cv_analyses"]) == 1
    assert len(payload["opportunity_searches"]) == 1
