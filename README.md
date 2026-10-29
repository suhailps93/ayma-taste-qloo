# ayma-taste-qloo

**Taste match powered by Qloo** — the Qloo-built subset of
[Ayma](https://ayma.ai), extracted for the **Qloo Agentic Hackathon**
(October 2026).

Ayma is a voice-first AI dating companion. This repository contains **only** the
components that call the **Qloo Taste / Insights API**: a feature that, for a
pair of people, turns each person's stated music / film / food favourites into a
**shared-taste score**, the **tastes they have in common**, and **taste-based
date ideas** (a place, a film, and an artist Qloo ranks highly for *both* of
them at once). Everything else in Ayma — auth, matching, the Firestore data
layer, the Gemini client, the voice-agent worker, the Flutter app shell — is
private and is **not** included here.

> This is a **recent addition to Ayma**, built in late October 2026 for this
> hackathon. It is additive: no pre-existing Ayma surface changed behaviour.

Nobody in this repo is a real person. The demo profiles are fabricated.

---

## Try it in 30 seconds (no key, no database, no network)

```bash
cd backend
python3 -m pip install -r requirements-test.txt
python3 demo_taste.py
```

You'll see the full pipeline on two sample people — **Music / Film / Food →
Qloo → score + shared tastes + date ideas** — running on the bundled offline
fixture (`source: fixture`). To run it against the **live Qloo API**, export a
Qloo Insights key first:

```bash
export QLOO_API_KEY=<your Qloo key>
python3 demo_taste.py            # now prints source: qloo
```

`python3 demo_taste.py A.txt B.txt` runs it on two text files, each containing
`Music: …`, `Film: …`, `Food: …` lines.

**Hosted judge demo (live Qloo, public, no sign-in):**
<https://ayma-api-235381544962.us-central1.run.app/taste/demo> — pick two of the
four fabricated demo profiles and press **Match tastes**. JSON directly:
`GET /taste/demo/pair?a=maya&b=leo`.

---

## How it uses Qloo

The engine is `backend/qloo_client.py` (the Qloo API client) and
`backend/taste_match.py` (the taste-match logic). For a pair of people:

1. **Taste signals.** Each person's public favourites are parsed from
   `Music / Film / Food` lines (`taste_match.parse_taste`), up to 5 per domain.
2. **Resolve to Qloo entities.** Every name is resolved to a Qloo entity of its
   domain's type via **`GET /search`** —
   `urn:entity:artist` (music), `urn:entity:movie` (film), `urn:entity:place`
   (food & places).
3. **Compatibility.** For each domain, **`GET /v2/insights`** returns Qloo's
   taste-graph recommendations driven by **all** of a person's resolved entities
   (`signal.interests.entities` — so each recommendation is cross-domain, not
   just same-domain). A domain's score is the **overlap coefficient** of
   person A's and person B's recommendation sets × 100; the overall score is the
   mean across domains. Shared tastes are the names both people listed outright,
   then the recommendations both taste graphs surface, in the joint ranking's
   order. Labels: ≥70 strong · ≥45 good · ≥25 some · else different.
4. **Date ideas.** One joint `GET /v2/insights` for `urn:entity:place` driven by
   **both** people's entities at once and filtered to the first person's city
   (`filter.location.query`) yields the top places; the top joint `movie` and
   `artist` neither person already listed become the "movie night" and
   "listening date" picks.

Qloo signals used: `/search` (entity resolution), `/v2/insights` with
`signal.interests.entities`, `filter.type`, `filter.location.query`, `take`, and
each entity's returned `affinity` and `tags`.

### The agentic angle

In Ayma this is one tool in an agent's hands, not a standalone widget. Ayma
builds a persistent **AI avatar** of each user from what they share, and those
avatars go on **simulated AI-to-AI first dates** on the user's behalf. The Qloo
taste match is the tool the agent calls to decide *where the two of them would
actually click* — it grounds the simulated date in a real taste graph (a shared
place to meet, a film to see, an artist to put on) and surfaces the overlap in
the post-date match report ("Taste match · powered by Qloo"). The agent decides
*when* to pull taste into a conversation; Qloo supplies the taste reasoning.

---

## What's here

```
backend/
  qloo_client.py        Qloo Taste/Insights API client: LiveQlooClient (real API,
                        X-Api-Key + /search + /v2/insights, rate-paced) and
                        FixtureQlooClient (offline mini taste graph). Same shapes.
  taste_match.py        The taste-match logic + the HTTP router (/taste/pair,
                        /taste/demo, /taste/demo/pair) and the match-report section.
  qloo_fixture.json     48 real, well-known entities (illustrative tags, NOT Qloo
                        data) so the demo + tests run with no key and no network.
  taste_demo.html       The public judge demo page (served at GET /taste/demo).
  config.py             The two non-secret Qloo config fields (base URL, timeout).
  demo_taste.py         Standalone runnable demo (Music/Film/Food -> score + ideas).
  _stubs/               Test-only stand-ins for Ayma's private core (see its README).
  tests/                Self-contained tests (fixture + FakeDb, no network).
docs/
  QLOO_TASTE.md         Full design: signals, scoring, privacy, the kill switch.
EXTRACTION_INVENTORY.md Every file, its origin, and every stubbed dependency.
LICENSE / NOTICE        Apache-2.0.
```

## What runs standalone (and what binds to Ayma's private core)

`qloo_client.py`, `taste_match.py`, `config.py`, `demo_taste.py` and the tests
run **standalone** — fixture + `FakeDb`, no key, no Firestore, no network:

```bash
cd backend
python3 -m pip install -r requirements-test.txt
python3 -m pytest -q          # 12 passed
```

`taste_match.py`'s HTTP router references Ayma's private auth, the Firestore
`db` handle, and the 18+ age gate. Those are **documented as external** and
reproduced only by the small stand-ins in `backend/_stubs/` (loaded by the tests
and the demo, never in production). See **`EXTRACTION_INVENTORY.md`** for a
file-by-file origin and every stubbed dependency.

## Safety & cost

- **Public profile data only.** Only taste names a person publishes are ever
  sent to Qloo — never private pages, contact details, location coordinates, or
  the caller's own private data.
- **18+.** The signed-in pair endpoint is gated to adults; the public demo pairs
  only the four fabricated demo profiles and refuses any other id, so it can
  never read a real user.
- **Kill switch.** A single runtime flag (`qloo_enabled`, default on) short-
  circuits `taste_match.match` **before any outbound Qloo call**, so Qloo billing
  can be stopped instantly with no redeploy. Details in `docs/QLOO_TASTE.md`.

## License

Apache-2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
