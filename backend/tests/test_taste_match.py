"""Self-contained tests for the Qloo taste engine.

Offline and deterministic: the bundled fixture (``qloo_fixture.json``) stands in
for Qloo and a :class:`fake_firestore.FakeDb` stands in for Firestore, so no
test makes a live Qloo call or touches the network (except the one test that
monkeypatches ``urlopen`` to assert the live wire shape without a socket).

Covers: the Taste-page parser, building a signal from a public profile view,
the fixture match end to end, the live client's exact request shape, client
selection by key, the ``qloo_enabled`` kill switch (no client is ever invoked
when off), and the public demo / signed-in pair endpoints via a minimal FastAPI
app that mounts the real router.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import public_profile
import qloo_client
import taste_match
from auth import Caller
from seed_demo import DEMO, seeded_db

MAYA = DEMO["maya"][0]
LEO = DEMO["leo"][0]


def _run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- #
# parse_taste
# --------------------------------------------------------------------------- #
def test_parse_taste_domains_aliases_and_dedup():
    body = (
        "Music: Khruangbin, Bon Iver, Khruangbin\n"
        "Movies: Arrival\n"
        "Restaurants: Ramen Shop · Food: Zuni Cafe"
    )
    parsed = taste_match.parse_taste(body)
    assert parsed["music"] == ["Khruangbin", "Bon Iver"]  # alias + dedup, order kept
    assert parsed["film"] == ["Arrival"]  # "Movies" -> film
    assert parsed["dining"] == ["Ramen Shop", "Zuni Cafe"]  # two aliases merged


def test_parse_taste_caps_five_per_domain_and_ignores_unknown_headers():
    body = "Music: a, b, c, d, e, f, g\nMood: happy"
    parsed = taste_match.parse_taste(body)
    assert parsed["music"] == ["a", "b", "c", "d", "e"]  # capped at 5
    assert "Mood" not in parsed and len(parsed) == 1  # unknown header ignored


# --------------------------------------------------------------------------- #
# taste_from_view
# --------------------------------------------------------------------------- #
def test_taste_from_view_reads_public_taste_page():
    db = seeded_db()
    view = public_profile.build(db, MAYA, MAYA)
    name, city, taste = taste_match.taste_from_view(view)
    assert name == "Maya"
    assert city == "San Francisco"
    assert "Khruangbin" in taste["music"]


def test_taste_from_view_without_taste_page_raises_no_taste():
    db = seeded_db()
    db.collection("users").document("fresh").collection("profile").document(
        "main"
    ).set({"name": "Fresh", "location": "Nowhere"})
    with pytest.raises(taste_match.NoTaste):
        taste_match.taste_from_view(public_profile.build(db, "fresh", "fresh"))


# --------------------------------------------------------------------------- #
# fixture match end to end
# --------------------------------------------------------------------------- #
def test_fixture_match_shapes_full_payload():
    db = seeded_db()
    a = taste_match.taste_from_view(public_profile.build(db, MAYA, MAYA))
    b = taste_match.taste_from_view(public_profile.build(db, LEO, LEO))
    result = _run(taste_match.match(a, b, client=qloo_client.FixtureQlooClient()))
    assert result["source"] == "fixture"
    assert 0 <= result["score"] <= 100
    assert result["score_label"] in (
        "Strong taste overlap",
        "Good taste overlap",
        "Some taste overlap",
        "Different tastes",
    )
    assert {d["domain"] for d in result["domains"]} <= {"music", "film", "dining"}
    assert "Khruangbin" in result["shared"]  # both list it outright
    assert isinstance(result["date_ideas"], list) and result["date_ideas"]
    assert all({"name", "kind", "why"} <= set(i) for i in result["date_ideas"])


# --------------------------------------------------------------------------- #
# live client wire shape (no socket — urlopen is monkeypatched)
# --------------------------------------------------------------------------- #
def test_live_client_request_shape(monkeypatch):
    seen: list[str] = []

    class _Resp:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            return json.dumps(self._payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout):
        url = req.full_url
        seen.append(url)
        assert req.headers.get("X-api-key") == "secret-key"  # header name casing
        if "/search" in url:
            return _Resp({"results": [{"entity_id": "e1", "name": "Khruangbin"}]})
        return _Resp(
            {"results": {"entities": [{"entity_id": "r1", "name": "Rec", "tags": []}]}}
        )

    monkeypatch.setattr(qloo_client.urllib.request, "urlopen", fake_urlopen)
    client = qloo_client.LiveQlooClient("secret-key", "https://qloo.example", 5.0)

    hit = client.search("Khruangbin", qloo_client.ENTITY_TYPES["music"])
    assert hit and hit["id"] == "e1"
    recs = client.insights(qloo_client.ENTITY_TYPES["music"], ["e1"], take=8)
    assert recs and recs[0]["id"] == "r1"

    assert any("/search?" in u and "types=urn%3Aentity%3Aartist" in u for u in seen)
    assert any(
        "/v2/insights?" in u and "signal.interests.entities=e1" in u.replace("%2C", ",")
        for u in seen
    )


def test_get_client_selects_live_only_with_key(monkeypatch):
    monkeypatch.delenv("QLOO_API_KEY", raising=False)
    assert isinstance(qloo_client.get_client(), qloo_client.FixtureQlooClient)
    monkeypatch.setenv("QLOO_API_KEY", "x")
    assert isinstance(qloo_client.get_client(), qloo_client.LiveQlooClient)


# --------------------------------------------------------------------------- #
# kill switch — flag OFF => zero Qloo calls
# --------------------------------------------------------------------------- #
def test_kill_switch_makes_no_qloo_call(monkeypatch):
    class _Spy(qloo_client.FixtureQlooClient):
        def search(self, *a, **k):  # pragma: no cover - must never run
            raise AssertionError("Qloo client invoked while kill switch is off")

        def insights(self, *a, **k):  # pragma: no cover - must never run
            raise AssertionError("Qloo client invoked while kill switch is off")

    monkeypatch.setattr(qloo_client, "qloo_enabled", lambda: False)
    with pytest.raises(taste_match.NoTaste):
        _run(taste_match.match(("A", "", {"music": ["x"]}), ("B", "", {"music": ["y"]}), client=_Spy()))


# --------------------------------------------------------------------------- #
# HTTP endpoints via a minimal app that mounts the real router
# --------------------------------------------------------------------------- #
def _client(db, caller_uid: str | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(taste_match.router)
    monkey_get_db = lambda: db  # noqa: E731
    taste_match.get_db = monkey_get_db  # the endpoints call module-level get_db
    if caller_uid is not None:
        from practice_date import require_not_underage_uid

        app.dependency_overrides[taste_match.require_caller] = lambda: Caller(uid=caller_uid)
        app.dependency_overrides[require_not_underage_uid] = lambda: caller_uid
    return TestClient(app)


def test_pair_endpoint_between_caller_and_other():
    db = seeded_db()
    client = _client(db, caller_uid=MAYA)
    resp = client.post("/taste/pair", json={"other_uid": LEO})
    assert resp.status_code == 200
    assert resp.json()["b"]["name"] == "Leo"
