"""
Rate limiting (OWASP: protect from brute force and abuse).
Uses X-Forwarded-For when behind a trusted proxy.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address


def _key_func(request):
    """Client IP: X-Forwarded-For (first hop) when behind proxy, else remote address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func)
