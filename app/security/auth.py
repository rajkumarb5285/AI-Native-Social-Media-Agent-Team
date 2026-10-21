"""Authentication helpers. Missing or invalid bearer tokens are rejected."""
import os
import hmac
import hashlib
import json
import base64
import time
import secrets
from typing import Optional
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel
from app.security.rbac import Role

def _load_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if not secret and environment not in {"development", "test"}:
        raise RuntimeError("JWT_SECRET must be configured outside development/test.")
    return secret or "local-development-only-change-before-deploy"

JWT_SECRET = _load_jwt_secret()

class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    role: str = Role.EDITOR.value
    tenant_id: str = "default"

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """PBKDF2 password hashing. Store the random salt with the digest."""
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_value.encode("utf-8"), 310_000)
    return f"{salt_value}${base64.urlsafe_b64encode(digest).decode().rstrip('=')}"

def create_jwt(user: AuthenticatedUser, expires_in_seconds: int = 86400) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()).decode().rstrip("=")
    payload_data = {"sub": user.user_id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id, "exp": int(time.time()) + expires_in_seconds}
    payload = base64.urlsafe_b64encode(json.dumps(payload_data, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    sig_encoded = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header}.{payload}.{sig_encoded}"

def verify_jwt(token: str) -> Optional[AuthenticatedUser]:
    try:
        header, payload, supplied_sig = token.split(".")
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        supplied_bytes = base64.urlsafe_b64decode(supplied_sig + "=" * (-len(supplied_sig) % 4))
        if not hmac.compare_digest(expected_sig, supplied_bytes):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode())
        if int(data.get("exp", 0)) <= int(time.time()):
            return None
        if not data.get("sub") or not data.get("tenant_id") or not data.get("email"):
            return None
        role = data.get("role", Role.VIEWER.value)
        if role not in {r.value for r in Role}:
            return None
        return AuthenticatedUser(user_id=data["sub"], email=data["email"], role=role, tenant_id=data["tenant_id"])
    except Exception:
        return None

async def get_current_user(authorization: Optional[str] = Header(None)) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = verify_jwt(authorization.split("Bearer ", 1)[1].strip())
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")
    return user

def require_role(allowed_roles: list[str]):
    async def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Operation requires one of roles: {allowed_roles}. Current role: {user.role}")
        return user
    return role_checker
