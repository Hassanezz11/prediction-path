from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from backend.config import settings


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 390000)
    return f"{_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_str, digest_str = password_hash.split("$", 1)
    except ValueError:
        return False
    salt = _b64decode(salt_str)
    expected = _b64decode(digest_str)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 390000)
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=settings.token_ttl_minutes)).timestamp()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    payload_b64 = _b64encode(payload_bytes)
    signature = hmac.new(settings.secret_key.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64encode(signature)}"


def decode_access_token(token: str) -> dict:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    expected_sig = hmac.new(settings.secret_key.encode(), payload_b64.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected_sig, _b64decode(signature_b64)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")

    payload = json.loads(_b64decode(payload_b64).decode())
    if payload["exp"] < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload
