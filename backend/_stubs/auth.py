"""Test-only stand-in for Ayma's auth module.

The real ``auth`` (Ayma private core) verifies a Firebase ID token and resolves
the caller's ``uid``. The taste engine only needs the two symbols its router
signature references — the ``Caller`` shape and the ``require_caller`` /
``require_uid`` FastAPI dependencies — so the module imports cleanly and the
offline tests can inject a caller without any real token verification.

NOT the production auth. Added to ``sys.path`` only by ``tests/conftest.py``
(and by ``demo_taste.py`` for the standalone demo). No credential is ever read.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Caller:
    """The authenticated caller — only the ``uid`` the taste engine reads."""

    uid: str


def require_uid() -> str:  # pragma: no cover - overridden per test
    """Production resolves this from a verified Firebase token; the offline
    tests monkeypatch it to a fixed uid."""
    raise RuntimeError("require_uid is stubbed; monkeypatch it in a test")


def require_caller() -> Caller:  # pragma: no cover - overridden per test
    """Production resolves this from a verified Firebase token; the offline
    tests monkeypatch it to a fixed Caller."""
    raise RuntimeError("require_caller is stubbed; monkeypatch it in a test")
