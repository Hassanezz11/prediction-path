from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from uuid import uuid4

import requests
from fastapi import UploadFile
from pypdf import PdfReader

from backend.config import settings


def save_upload(student_id: int, file: UploadFile) -> tuple[Path, int]:
    student_dir = settings.upload_dir / f"student_{student_id}"
    student_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "cv.pdf").suffix or ".pdf"
    destination = student_dir / f"{uuid4().hex}{extension}"
    content = file.file.read()
    destination.write_bytes(content)
    return destination, len(content)


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(io.BytesIO(file_path.read_bytes()))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def analyze_cv(cv_text: str, model: str | None = None) -> dict:
    selected_model = model or settings.default_ollama_model
    prompt = f"""You are an academic advisor for a Computer Science school with branches IADATA, DSI, and CIR.
Analyze the student CV below using projects and technical skills only.

Reply exactly with:
Recommended Branch: <IADATA | DSI | CIR>
Confidence: <High | Medium | Low>
Key evidence:
- <bullet>
- <bullet>
- <bullet>
Justification: <short justification>
Strengthen next: <short advice>

CV:
{cv_text[:4000]}"""
    response = requests.post(
        settings.ollama_url,
        json={"model": selected_model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    output = response.json()["response"]
    branch_match = re.search(r"Recommended Branch:\s*(IADATA|DSI|CIR)", output)
    confidence_match = re.search(r"Confidence:\s*(High|Medium|Low)", output)
    checksum = hashlib.sha256(cv_text.encode()).hexdigest()
    return {
        "recommended_branch": branch_match.group(1) if branch_match else None,
        "confidence": confidence_match.group(1) if confidence_match else None,
        "output": output,
        "checksum": checksum,
        "ollama_model": selected_model,
    }
