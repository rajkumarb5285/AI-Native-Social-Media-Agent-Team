import re

SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(authorization:\s*bearer\s+)([^\s]+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)([a-zA-Z0-9_\-]{8,})([\"']?)"), r"\1[REDACTED]\3"),
    (re.compile(r"(?i)(password[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)([\"']?)"), r"\1[REDACTED]\3"),
    (re.compile(r"(?i)(client[_-]?secret[\"']?\s*[:=]\s*[\"']?)([a-zA-Z0-9_\-]{8,})([\"']?)"), r"\1[REDACTED]\3"),
]

def mask_secrets(log_message: str) -> str:
    masked = log_message
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked
