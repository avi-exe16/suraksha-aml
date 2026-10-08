import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

API_KEY_NAME = "X-Canara-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# In production, this is sourced from HashiCorp Vault / AWS Secrets Manager
EXPECTED_API_KEY = os.getenv("SURAKSHA_INTERNAL_API_KEY", "canara_sec_prod_live_2026_k8s")


async def verify_internal_api_key(api_key: str = Security(api_key_header)):
    """Protects internal inference and management APIs from unauthorized access."""
    if not api_key or api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Canara-API-Key header. Access denied.",
        )
    return api_key


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard OWASP banking HTTP security headers."""
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data: https://fastapi.tiangolo.com;"
        return response