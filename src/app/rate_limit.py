"""Rate limiting middleware for FastAPI.

Uses sliding window per client IP to limit request rates.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Configuration
RATE_LIMIT_REQUESTS = int(__import__('os').getenv("RATE_LIMIT_REQUESTS", "10"))  # requests
RATE_LIMIT_WINDOW = int(__import__('os').getenv("RATE_LIMIT_WINDOW", "60"))      # seconds

# In-memory storage: ip -> deque of timestamps
_request_timestamps: Dict[str, Deque[float]] = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit upload endpoint to prevent abuse
        if request.url.path == "/upload/":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            timestamps = _request_timestamps[client_ip]

            # Remove timestamps older than window
            while timestamps and timestamps[0] < now - RATE_LIMIT_WINDOW:
                timestamps.popleft()

            if len(timestamps) >= RATE_LIMIT_REQUESTS:
                return HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )

            timestamps.append(now)

        response = await call_next(request)
        return response
