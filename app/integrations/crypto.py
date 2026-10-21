import os
import base64
import hashlib
from cryptography.fernet import Fernet

def _get_fernet_key() -> bytes:
    raw_key = os.getenv("SECRET_ENCRYPTION_KEY", "ai-native-social-agent-team-secret-key-salt")
    # Derive a 32-byte urlsafe base64 key
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_token(plain_token: str) -> str:
    if not plain_token:
        return ""
    f = Fernet(_get_fernet_key())
    return f.encrypt(plain_token.encode("utf-8")).decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    f = Fernet(_get_fernet_key())
    return f.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
