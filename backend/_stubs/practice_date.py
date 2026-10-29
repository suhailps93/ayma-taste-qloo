"""Test-only stand-in for the one symbol ``taste_match`` imports from Ayma's
Practice Date module: the 18+ age-gate FastAPI dependency.

``POST /taste/pair`` is an adults-only surface, so in production it depends on
``practice_date.require_not_underage_uid`` — the same age gate Practice Date
uses — which resolves the caller's uid and refuses an underage account. The
real gate binds to Ayma's auth + the stored date of birth (private core). This
stand-in reproduces only the dependency symbol so the router imports; the
offline tests monkeypatch the age check to a pass.

NOT the production age gate. Added to ``sys.path`` only by ``tests/conftest.py``
(and by ``demo_taste.py``).
"""

from __future__ import annotations

from auth import require_uid


def require_not_underage_uid(uid: str = None) -> str:  # pragma: no cover
    """FastAPI dependency: the caller's uid, refused if underage. Offline tests
    override the dependency; the public demo routes do not use it."""
    return uid if uid is not None else require_uid()
