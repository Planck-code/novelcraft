from __future__ import annotations

import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.common.json_repair import JSONRepairError

logger = logging.getLogger(__name__)


def llm_retry(max_attempts: int = 3):
    """Retry decorator for LLM calls. Retries on connection errors, timeouts, and JSON parse failures.

    Uses exponential backoff: 2s, 4s, 8s... up to 60s max.
    """
    return retry(
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(max_attempts),
        retry=retry_if_exception_type(
            (ConnectionError, TimeoutError, JSONRepairError)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
