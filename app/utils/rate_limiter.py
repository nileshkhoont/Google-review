"""In-memory per-IP rate limiter for the login endpoint.

Single-process only: state lives in a module-level dict, so it won't be
shared across multiple worker processes. That's fine for this app (a single
uvicorn worker); scaling to multiple workers/instances would need a shared
store (e.g. Redis) instead.
"""

import time

_WINDOW_SECONDS = 60
_MAX_ATTEMPTS = 5
_BLOCK_SECONDS = 5 * 60

_attempts: dict[str, list[float]] = {}
_blocked_until: dict[str, float] = {}


def check_login_rate_limit(ip: str) -> float | None:
    """
    Registers a login attempt from `ip`. Returns None if it's allowed, or
    the number of seconds until `ip` is unblocked if it just tripped (or
    already was under) the limit.
    """
    now = time.monotonic()

    blocked_at = _blocked_until.get(ip)
    if blocked_at is not None:
        if now < blocked_at:
            return blocked_at - now
        del _blocked_until[ip]
        _attempts.pop(ip, None)

    window_start = now - _WINDOW_SECONDS
    recent = [t for t in _attempts.get(ip, []) if t > window_start]
    recent.append(now)

    if len(recent) > _MAX_ATTEMPTS:
        _blocked_until[ip] = now + _BLOCK_SECONDS
        _attempts.pop(ip, None)
        return _BLOCK_SECONDS

    _attempts[ip] = recent
    return None
