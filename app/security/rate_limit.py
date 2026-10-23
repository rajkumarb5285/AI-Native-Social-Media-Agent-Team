import time
from collections import defaultdict
from fastapi import Request, HTTPException

class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_key: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        # Filter timestamps within current window
        valid_requests = [t for t in self.requests[client_key] if t > window_start]
        self.requests[client_key] = valid_requests

        if len(valid_requests) >= self.rpm:
            return False

        self.requests[client_key].append(now)
        return True

rate_limiter = InMemoryRateLimiter(requests_per_minute=120)

def check_rate_limit(request: Request, key: str = "", limit: int = 60, window_seconds: int = 60):
    client_ip = request.client.host if request.client else "127.0.0.1"
    tenant_header = request.headers.get("x-tenant-id", client_ip)
    lookup_key = f"{tenant_header}:{key}" if key else tenant_header
    if not rate_limiter.is_allowed(lookup_key):
        raise HTTPException(429, "Too Many Requests: Rate limit exceeded. Try again in 60 seconds.")
