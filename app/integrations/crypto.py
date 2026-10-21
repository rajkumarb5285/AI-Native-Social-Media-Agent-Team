import os
import base64
import hashlib
from cryptography.fernet import Fernet


def _get_fernet_key() -> bytes:
    raw_key = os.getenv("SECRET_ENCRYPTION_KEY", "").strip()
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if not raw_key and environment not in {"development", "test"}:
        raise RuntimeError("SECRET_ENCRYPTION_KEY must be configured outside development/test.")
    # This fallback exists only for isolated local examples; never use it for deployed data.
    raw_key = raw_key or "local-development-only-do-not-deploy"
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_token(plain_token: str) -> str:
    if not plain_token:
        return ""
    return Fernet(_get_fernet_key()).encrypt(plain_token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    return Fernet(_get_fernet_key()).decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
