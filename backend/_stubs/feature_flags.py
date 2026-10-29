"""Test-only stand-in for Ayma's runtime feature-flag store.

In production ``feature_flags.enabled(name)`` reads a Firestore-backed flag
(with an env override). The taste engine reads exactly one flag,
``qloo_enabled`` — the kill switch that, when flipped OFF at runtime, makes
``taste_match.match`` short-circuit **before any outbound Qloo HTTP call** so
nothing can bill Qloo once the hackathon credits run out (see
``qloo_client.qloo_enabled`` and docs/QLOO_TASTE.md).

Offline this honours a ``FLAG_<NAME>`` env override and otherwise defaults the
Qloo kill switch to ON, matching production's default. Added to ``sys.path``
only by ``tests/conftest.py`` (and by ``demo_taste.py``).
"""

from __future__ import annotations

import os

_DEFAULTS = {"qloo_enabled": True}


def enabled(name: str) -> bool:
    override = os.environ.get(f"FLAG_{name.upper()}")
    if override is not None:
        return override.strip().lower() in ("1", "true", "yes", "on")
    return _DEFAULTS.get(name, False)
