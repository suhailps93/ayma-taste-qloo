"""Test-only stand-in for Ayma's Firestore handle module.

The real ``db.get_db()`` (Ayma private core) returns the initialised
``firestore.Client``. Offline, the tests and the standalone demo monkeypatch
``taste_match.get_db`` to return a :class:`fake_firestore.FakeDb`, so this
module only needs to expose the symbol for import; calling it unpatched is an
explicit error rather than a silent real-Firestore connection.

NOT the production handle. Added to ``sys.path`` only by ``tests/conftest.py``
(and by ``demo_taste.py``). No Firestore credential is ever read.
"""

from __future__ import annotations


def get_db():  # pragma: no cover - monkeypatched offline
    raise RuntimeError(
        "db.get_db is stubbed; monkeypatch taste_match.get_db to a FakeDb"
    )
