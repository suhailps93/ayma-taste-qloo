# Extraction inventory

Every file in this public repo, where it came from, and — for the extracted
engine — every dependency on Ayma's private core that is stubbed or documented
as external. The goal: a Qloo judge can see exactly what is newly built, what is
the real production code, and what is a test-only stand-in.

## Newly built for the Qloo Agentic Hackathon (real production code, verbatim)

These are copied **unchanged** from Ayma's backend (`functions/bootstrap/`). They
are the actual code the deployed service runs.

| File (here) | Origin (Ayma backend) | What it is |
|---|---|---|
| `backend/qloo_client.py` | `qloo_client.py` | Qloo Taste/Insights API client — `LiveQlooClient` (real API: `X-Api-Key`, `GET /search`, `GET /v2/insights` for entities, tags and demographics, process-wide rate pacing + 429 retry) and `FixtureQlooClient` (offline). Ten domain entity types. |
| `backend/taste_match.py` | `taste_match.py` | The taste-match logic (parse → resolve → per-domain overlap → score + shared + shared tags + demographics + date ideas, across ten domains), the FastAPI router (`/taste/pair`), and the match-report section. |
| `backend/qloo_fixture.json` | `qloo_fixture.json` | 72 real, well-known entities across all ten domains, with illustrative tags (NOT Qloo data) for the offline demo/tests. |
| `docs/QLOO_TASTE.md` | `docs/QLOO_TASTE.md` | Full design doc: signals, scoring, where the Taste page comes from, live-vs-fixture, privacy, the kill switch, the API. |

## Newly written for this repo (packaging, not in the private backend)

| File | Why |
|---|---|
| `backend/config.py` | A **2-field slice** of Ayma's private `config.py` — only `qloo_api_base_url` and `qloo_timeout_seconds`, with the same defaults. The private `Config` has many more fields (Gemini, Meta, LiveKit, Firestore, billing); none are needed here. The `QLOO_API_KEY` secret is **not** here — it's read from the environment at the call site. |
| `backend/demo_taste.py` | Standalone runnable demo: Music/Film/Food → the real engine → score + shared tastes + date ideas, on the fixture (or live Qloo if `QLOO_API_KEY` is set). |
| `backend/requirements-test.txt`, `backend/pytest.ini` | Deps + config to run the demo and tests. |
| `backend/tests/conftest.py` | Puts `backend/` and `_stubs/` on `sys.path`; clears `QLOO_API_KEY` for the session. |
| `backend/tests/test_taste_match.py` | Self-contained tests (parser, signal building, fixture match, live wire shape, client selection, kill switch, endpoints). |
| `backend/tests/seed_demo.py` | The four fabricated demo profiles as `FakeDb` seed data (mirrors the seeded Taste pages). |
| `backend/tests/fake_firestore.py` | In-memory Firestore fake with real collection/subcollection/query semantics. |
| `README.md`, `NOTICE`, `LICENSE`, `.gitignore` | Repo docs + Apache-2.0. |

## Private-core dependencies (stubbed for tests, real in production)

`taste_match.py` binds to these Ayma-private modules. They are reproduced only
by the stand-ins in `backend/_stubs/` (see `_stubs/README.md`), loaded by the
tests and the demo, never in production.

| Imported by the engine | Private in Ayma | Stub here |
|---|---|---|
| `public_profile.build` | the viewer-visible profile serializer (query-level `visibility == "public"` filter + span stripping + cross-user auth) | `_stubs/public_profile.py` (filtering contract only) |
| `story.strip_private_spans` | the Story span parser | `_stubs/story.py` |
| `auth.Caller` / `require_caller` / `require_uid` | Firebase-token auth | `_stubs/auth.py` |
| `db.get_db` | the Firestore client handle | `_stubs/db.py` (raises unless monkeypatched to `FakeDb`) |
| `feature_flags.enabled` | the Firestore-backed runtime flag store | `_stubs/feature_flags.py` |
| `practice_date.require_not_underage_uid` | the shared 18+ age gate | `_stubs/practice_date.py` (dependency symbol only) |

## Documented as external (not included, not stubbed)

The Flutter UI (`taste_match_card.dart`, `taste_models.dart`), the router mount
and the `GET /match/{id}` match-report embedding in Ayma's `main.py`, the
questionnaire wiring that populates a real user's public Taste page
(`question_tree.json`, `skills/questionnaire.py`, `completeness.py`), and the
Secret Manager / Cloud Run deploy plumbing all bind to Ayma's private app and
are **not** part of this subset. They are described in `docs/QLOO_TASTE.md`.
