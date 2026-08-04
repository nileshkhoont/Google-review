"""
Thin wrapper around the Google Gemini API with multi-key automatic failover.

This is the ONLY module in the project allowed to import the Gemini SDK.
Everything else (review_generator, services, routers) calls through
`GeminiClient.generate_text` — key rotation and failover are entirely
hidden behind that one method.

Rotation strategy: sticky pointer.
    A request starts with whichever key is currently "active" (not always
    key #1). If that key fails with a retryable error, the request tries the
    next key(s) in circular order. Whichever key is serving requests stays
    active — and stays silent in the logs — until it fails, at which point
    its lifetime is closed out and the next key's lifetime begins.

Logging strategy: key lifetime, not per-request.
    Nothing is logged for individual successful calls. Only two events are
    logged per key: it becoming active (START) and it being exhausted
    (END), so the log reads as a clean timeline of how long each key lasted.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.config import settings
from app.utils.logger import logger

# The installed google-generativeai SDK stores its API key in process-global
# state (set via genai.configure()) rather than per-model, so rotating keys
# means re-pointing that global state before each attempt. This lock
# serializes "configure + call" so two concurrent requests in the same
# process can't interleave and end up sending a request under the wrong key.
_config_lock = asyncio.Lock()
_configured_key: str | None = None

# Guards transitions of the active key's lifetime (index + start time) so
# concurrent requests failing on the same key don't each print their own
# END/START pair.
_lifetime_lock = asyncio.Lock()
_active_key_index: int | None = None
_active_key_started_at: datetime | None = None

_IST = timezone(timedelta(hours=5, minutes=30), name="IST")

# Errors worth failing over to the next key for: quota/rate-limit style
# failures, transient server errors, and invalid/revoked-key errors. Anything
# else (bad prompt, invalid argument, etc.) won't be fixed by switching keys,
# so it is raised immediately instead of burning through the rest of the list.
_RETRYABLE_EXCEPTIONS = (
    google_exceptions.ResourceExhausted,  # 429 / RESOURCE_EXHAUSTED (quota)
    google_exceptions.TooManyRequests,  # 429 (rate limit)
    google_exceptions.ServiceUnavailable,  # 503
    google_exceptions.DeadlineExceeded,  # 504
    google_exceptions.InternalServerError,  # 500
    google_exceptions.PermissionDenied,  # invalid/revoked key
    google_exceptions.Unauthenticated,  # invalid key
)

_RETRYABLE_MARKERS = (
    "429",
    "resource_exhausted",
    "rate limit",
    "quota",
    "unavailable",
    "deadline exceeded",
)

_SEPARATOR = "=" * 50


def _is_retryable(exc: Exception) -> bool:
    """Whether this failure should trigger failover to the next API key."""
    if isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    message = str(exc).lower()
    return any(marker in message for marker in _RETRYABLE_MARKERS)


def _reason_label(exc: Exception) -> str:
    """Short, human-readable exhaustion reason for the END block."""
    if isinstance(exc, google_exceptions.ResourceExhausted) or "resource_exhausted" in str(exc).lower():
        return "RESOURCE_EXHAUSTED"
    if isinstance(exc, google_exceptions.TooManyRequests) or "429" in str(exc):
        return "429 RATE_LIMIT"
    if isinstance(exc, (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated)):
        return "INVALID_OR_REVOKED_KEY"
    if isinstance(exc, google_exceptions.ServiceUnavailable):
        return "SERVICE_UNAVAILABLE"
    if isinstance(exc, google_exceptions.DeadlineExceeded):
        return "DEADLINE_EXCEEDED"
    if isinstance(exc, google_exceptions.InternalServerError):
        return "INTERNAL_ERROR"
    return type(exc).__name__


def _now_ist() -> datetime:
    return datetime.now(_IST)


def _format_ts(moment: datetime) -> str:
    return moment.strftime("%d-%b-%Y %I:%M:%S %p %Z")


def _format_duration(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"


def _log_key_started(key_number: int, started_at: datetime) -> None:
    logger.info(
        "\n%s\n🚀 Gemini API Key #%s STARTED\nStarted At : %s\n%s",
        _SEPARATOR, key_number, _format_ts(started_at), _SEPARATOR,
    )


def _log_key_ended(key_number: int, started_at: datetime, ended_at: datetime, exc: Exception) -> None:
    logger.info(
        "\n%s\n❌ Gemini API Key #%s ENDED\nStarted At : %s\nEnded At   : %s\n"
        "Total Active Time : %s\nReason : %s\n%s",
        _SEPARATOR, key_number, _format_ts(started_at), _format_ts(ended_at),
        _format_duration(ended_at - started_at), _reason_label(exc), _SEPARATOR,
    )


async def _configure_key(key: str) -> None:
    """Point the Gemini SDK's global config at `key`, if not already set."""
    global _configured_key
    if _configured_key != key:
        genai.configure(api_key=key)
        _configured_key = key


class GeminiClient:
    """
    Sends prompts to Gemini, transparently retrying across every configured
    API key on quota/rate-limit/invalid-key style failures.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.gemini_model
        self.api_keys = settings.gemini_key_list

        if not self.api_keys:
            logger.warning("No Gemini API keys configured. AI review generation will fail.")

    async def generate_text(self, prompt: str) -> str:
        """
        Generate text from a prompt, failing over across API keys.

        Starts at the currently active key and tries keys in circular order
        from there. Successful calls return immediately and are not logged.
        A key is only logged when its lifetime starts (first becomes active)
        or ends (fails with a quota/rate-limit/retryable error) — nothing is
        logged per individual request. Only once every key has failed in a
        given call does this raise, with a single combined error.
        """
        global _active_key_index, _active_key_started_at

        if not self.api_keys:
            raise RuntimeError("No Gemini API keys are configured.")

        total_keys = len(self.api_keys)

        async with _lifetime_lock:
            if _active_key_index is None:
                _active_key_index = 0
                _active_key_started_at = _now_ist()
                _log_key_started(1, _active_key_started_at)

        start_index = _active_key_index % total_keys
        last_error: Exception | None = None

        for attempt in range(1, total_keys + 1):
            index = (start_index + attempt - 1) % total_keys
            api_key = self.api_keys[index]

            try:
                # Only the (fast, synchronous) key switch needs to be
                # serialized — holding the lock across the network call
                # itself would mean the whole process can only have one
                # Gemini request in flight at a time. This is safe because
                # GenerativeModel binds its client to whatever key is
                # globally configured on its *first* generate_content_async
                # call, and that binding happens synchronously (no `await`)
                # before the request is actually sent — so as long as we
                # don't `await` anything else between releasing the lock and
                # calling generate_content_async, no other coroutine can
                # reconfigure the key in between.
                async with _config_lock:
                    await _configure_key(api_key)
                    model = genai.GenerativeModel(self.model_name)

                response = await model.generate_content_async(prompt)
                return (response.text or "").strip()

            except Exception as exc:  # noqa: BLE001
                last_error = exc

                if _is_retryable(exc):
                    async with _lifetime_lock:
                        # Only this key's own lifetime-owner closes it out —
                        # guards against duplicate END/START under a race
                        # where multiple concurrent requests fail on it at
                        # the same time.
                        if _active_key_index == index:
                            ended_at = _now_ist()
                            _log_key_ended(index + 1, _active_key_started_at, ended_at, exc)

                            next_index = (index + 1) % total_keys
                            _active_key_index = next_index
                            _active_key_started_at = ended_at
                            _log_key_started(next_index + 1, ended_at)
                    continue

                raise

        raise RuntimeError(
            "All Gemini API keys have been exhausted. Please try again later."
        ) from last_error
