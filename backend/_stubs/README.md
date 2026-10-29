# `_stubs/` — minimal stand-ins for Ayma's private core

The Qloo taste engine imports a handful of modules that live in Ayma's
**private** backend and are deliberately **not** part of this public repo (auth,
the Firestore handle, the runtime feature-flag store, the viewer-visible profile
serializer, the Story span parser, and the 18+ age-gate dependency). Copying
those files here would defeat the point of a scoped public subset.

Instead, this directory provides **small, clearly-labelled stand-ins** that
implement only the narrow interface the extracted code and the self-contained
tests exercise. They are added to `sys.path` by `tests/conftest.py` and by
`demo_taste.py` — so they resolve the private-core imports **only** when running
the demo or the tests in isolation, never in Ayma's production service, which
binds to the real private modules.

| Stub | Stands in for | Interface reproduced (only this) |
|---|---|---|
| `public_profile.py` | the viewer-visible profile serializer | `build(db, caller, other)` reproducing the **query-level privacy contract**: wiki read filtered to `visibility == "public"`, `{{private}}`/`{{ai_only}}` spans stripped, deleted/self handling, coarse city only |
| `story.py` | the Story span parser | `strip_private_spans(text)` |
| `auth.py` | Ayma's auth | the `Caller` shape and the `require_caller` / `require_uid` FastAPI dependencies (raise unless a test overrides them) |
| `db.py` | the Firestore handle | `get_db()` (raises unless monkeypatched to a `FakeDb` — never a real Firestore connection offline) |
| `feature_flags.py` | the runtime flag store | `enabled(name)` — honours a `FLAG_<NAME>` env override; defaults the `qloo_enabled` kill switch to ON, as in production |
| `practice_date.py` | the Practice Date module | only `require_not_underage_uid` — the 18+ age-gate FastAPI dependency the pair endpoint depends on |

**Why the `public_profile` stand-in still proves the privacy claim.** The taste
match sends Qloo **only** the taste names a person published. The real serializer
enforces that by reading wiki with `.where("visibility", "==", "public")` and
stripping private spans; this stand-in reproduces exactly that filtering
contract against the in-memory `FakeDb`, so the offline tests exercise the same
public-only boundary. In production, `taste_match` binds to Ayma's real
`public_profile.build`, which applies the identical filter plus cross-user read
authorization. See `EXTRACTION_INVENTORY.md`.
