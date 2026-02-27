"""Shared utilities for ask_help LLM wrappers."""

import json
import logging
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from the directory where this file lives, then walk up to find one
_here = Path(__file__).resolve().parent
for _candidate in [_here / ".env", _here.parent / ".env", _here.parent.parent / ".env"]:
    if _candidate.exists():
        load_dotenv(_candidate)
        break
else:
    load_dotenv()  # fall back to default search

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry helpers
# ---------------------------------------------------------------------------

_RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}
_DEFAULT_RETRIES = 3
_INITIAL_BACKOFF = 2.0  # seconds


def retry_on_rate_limit(fn, *args, retries: int = _DEFAULT_RETRIES, **kwargs):
    """
    Call fn(*args, **kwargs) up to `retries` times with exponential backoff
    on retryable HTTP errors (429, 5xx).  Returns fn's return value or None.
    """
    backoff = _INITIAL_BACKOFF
    for attempt in range(1, retries + 1):
        result = fn(*args, **kwargs)
        if result is not None:
            return result
        if attempt < retries:
            logger.warning(
                "Attempt %d/%d failed, retrying in %.1fs…", attempt, retries, backoff
            )
            time.sleep(backoff)
            backoff *= 2
    return None


def is_retryable_status(status_code: int) -> bool:
    return status_code in _RETRYABLE_HTTP_CODES


# ---------------------------------------------------------------------------
# JSON validation helper
# ---------------------------------------------------------------------------

def validate_json_response(text: Optional[str], label: str) -> Optional[str]:
    """
    If text is returned from a json_mode call, verify it parses as valid JSON.
    Logs a warning if it does not, but still returns the raw text so the caller
    can decide what to do.
    """
    if text is None:
        return None
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(
            "%s: json_mode was requested but response is not valid JSON: %s", label, e
        )
    return text
