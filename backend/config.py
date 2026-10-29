"""Configuration — the Qloo Taste API slice.

This is an **extract** of Ayma's private ``functions/bootstrap/config.py``: only
the two non-secret Qloo fields the taste engine reads. The private ``Config``
has many more fields (Gemini, Meta, LiveKit, Firestore, billing, …); none are
included because none of the extracted Qloo components need them.

The ``QLOO_API_KEY`` is a **SECRET** and is never stored here: it is read from
the environment (Secret Manager → Cloud Run in production; ``QLOO_API_KEY`` env
var locally) at the call site in ``qloo_client.py``. With no key, the taste
match runs entirely on the bundled offline fixture. The base URL is non-secret
config.

Field semantics and defaults match the private module exactly, so the extracted
``qloo_client`` / ``taste_match`` code behaves identically.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """The Qloo configuration surface (frozen, like production)."""

    qloo_api_base_url: str
    """Qloo Taste/Insights API base URL (non-secret). Hackathon keys are served
    from the hackathon host; override with ``QLOO_API_BASE_URL``."""

    qloo_timeout_seconds: float
    """Per-request timeout for Qloo calls; on timeout/error the taste match
    falls back to the fixture. Override with ``QLOO_TIMEOUT_SECONDS``."""


def _load() -> Config:
    return Config(
        qloo_api_base_url=os.getenv(
            "QLOO_API_BASE_URL", "https://hackathon.api.qloo.com"
        ),
        qloo_timeout_seconds=float(os.getenv("QLOO_TIMEOUT_SECONDS", "6")),
    )


CONFIG = _load()
