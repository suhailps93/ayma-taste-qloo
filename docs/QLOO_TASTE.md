# Taste match powered by Qloo (Qloo Agentic Hackathon)

Shared-taste score, shared-taste descriptors, an audience read, and taste-based
date ideas for a pair of people, from Qloo's Taste / Insights API — a taste graph
across ten domains (music, film, food & places, TV, books, podcasts, games,
travel, fashion/brands, nightlife). Built for the Qloo Agentic Hackathon.
Additive: a music/film/food profile scores and calls exactly as the original
three-domain version did; the other seven domains are recognised only when a
Taste page lists them.

## Try it (judges)

The live product runs on **TestFlight (iOS)**: <https://testflight.apple.com/join/uceuSRkh>.
Log in as `test1@gmail.com` / `Test123` (disposable demo account), open **Explore**,
and open **Sofia Marino** (a strong taste match) or **Priya Nair** (a poor match).
On the match report, open the **"Taste match · powered by Qloo"** card at the
bottom for the per-domain breakdown.

To run the extracted engine locally, see the repo README (`python3 demo_taste.py`,
offline fixture or live Qloo with `QLOO_API_KEY`).

## How it works

1. **Taste signals** — each person's PUBLIC Taste page, lines like
   `Music: Khruangbin, Bon Iver`, `Film: Arrival`, `Food: Ramen Shop`, and
   optionally `TV:`, `Books:`, `Podcasts:`, `Games:`, `Travel:`, `Brands:`,
   `Nightlife:` (full alias + header list below; max 5 per domain). Parsed by
   `taste_match.parse_taste`.
2. **Resolve** every name to a Qloo entity of its domain's type
   (`GET /search?query=…&types=urn:entity:…`) — ten entity types (below).
   Resolved entities carry their Qloo `tags` (names) and `tag_ids` (URNs).
3. **Compatibility** — for each domain **both** people listed, Qloo
   recommendations (`GET /v2/insights`, `signal.interests.entities` = ALL of a
   person's entities, so it's cross-domain) for person A and for person B; domain
   score = overlap coefficient × 100 of the two sets, each being that person's
   stated entities in the domain **plus** their recs (so a directly-shared
   favourite always counts and a shared domain never reads a spurious 0); overall
   = mean of the both-stated domains. **Shared tastes = only names both people
   listed outright** — Qloo's cross-domain predicted entities drive the score but
   are never surfaced as a stated/shared taste. Label: ≥70 strong, ≥45 good, ≥25
   some, else different. Only domains BOTH people listed are scored.
4. **Why you match (`shared_tags`)** — `GET /v2/insights filter.type=urn:tag`
   gives Qloo's affinity-ranked tags for each whole taste profile; the engine
   intersects the two (genre/theme/style labels ahead of niche keyword tags),
   blended with the tags their resolved entities share, into readable descriptors
   ("Atmospheric", "Melancholic", "Psychedelic") — the explainability of the match.
5. **Audience read (`demographics`)** — `GET /v2/insights
   filter.type=urn:demographics` per person returns Qloo's signed age/gender
   over-/under-index for each taste entity; averaged into one `{age, gender}` read
   per person, surfaced as `top_age` / `gender_lean` + a shared note. Only taste
   entity ids are sent — never user identity.
6. **Date ideas** — one joint Qloo query (both people's entities at once) for
   `urn:entity:place`, filtered to the first person's city
   (`filter.location.query`) and tag-aligned to both via `filter.tags` = the place
   tags their dining picks share (unfiltered fallback so ideas never go dark), top
   3; each place "why" names the shared tag. Plus one pick per other present domain
   (film → "movie night", music → "listening date", TV → "binge night", books →
   "book swap", games → "game night", travel → "weekend trip", nightlife → "night
   out", brands → "browse together") that the joint Qloo ranking puts highly and
   neither person already listed.

## Qloo API surface we use (depth + breadth)

The full enumeration of the Qloo API the taste engine touches. All calls are `GET`
with the `X-Api-Key` header against the Qloo Insights host (`QLOO_API_BASE_URL`,
default `https://hackathon.api.qloo.com`).

**Endpoints & `/v2/insights` surface:**

| Call | Params used | Response path | Drives |
|---|---|---|---|
| `GET /search` | `query`, `types` (one `urn:entity:*`), `take` | `results[]` → `entity_id`, `name`, `tags[].name`, `tags[].tag_id` | name → entity, with tags + tag ids |
| `GET /v2/insights` (entity) | `filter.type=urn:entity:*`, `signal.interests.entities`, `filter.location.query`, `filter.tags`, `take` | `results.entities[]` → `name`, `entity_id`, `query.affinity`, `tags[]`, `properties.address` | per-domain recs → overlap score; joint recs → date ideas |
| `GET /v2/insights` (tags) | `filter.type=urn:tag`, `signal.interests.entities`, `take` | `results.tags[]` → `tag_id`, `name`, `query.affinity` | `shared_tags` (why you match) |
| `GET /v2/insights` (demographics) | `filter.type=urn:demographics`, `signal.interests.entities` | `results.demographics[].query.age.{bucket}`, `.gender.{male,female}` | `demographics` (audience skew) |

Age buckets returned: `24_and_younger`, `25_to_29`, `30_to_34`, `35_to_44`,
`45_to_54`, `55_and_older`; gender: `male`, `female` (signed over/under-index,
roughly −1…+1). `filter.location.query` + `filter.tags` together can over-narrow
and return zero places — the engine falls back to the unfiltered joint query.
`filter.tags` takes tag URNs only (freeform strings are rejected), so place
alignment uses the `tag_id`s the two dining picks share. Nightlife uses
`urn:entity:place` narrowed by `filter.tags=urn:tag:category:place:nightlife`
(that tag + a location filter returns zero, so nightlife recs run without the
location filter).

**Entity types (breadth) ↔ Taste-page headers.** Every type below resolves against
the live hackathon API (search + insights):

| Domain key | Entity type URN | Header strings parsed (case-insensitive) |
|---|---|---|
| `music` | `urn:entity:artist` | Music, Artists, Bands |
| `film` | `urn:entity:movie` | Film, Films, Movie, Movies |
| `dining` | `urn:entity:place` | Dining, Food, Places, Restaurants, Cafes |
| `tv` | `urn:entity:tv_show` | TV, TV shows, Shows, Television, Series |
| `books` | `urn:entity:book` | Books, Book, Reading, Authors |
| `podcasts` | `urn:entity:podcast` | Podcasts, Podcast |
| `games` | `urn:entity:videogame` | Games, Game, Video games, Videogames, Gaming |
| `travel` | `urn:entity:destination` | Travel, Destinations, Destination, Trips, Places to go |
| `brands` | `urn:entity:brand` | Brands, Brand, Fashion, Style |
| `nightlife` | `urn:entity:place` + nightlife tag | Nightlife, Bars, Clubs, Going out |

> Note on `videogame`: the live hackathon API uses `urn:entity:videogame` (no
> underscore). `urn:entity:video_game` returns HTTP 400 there, so the no-underscore
> form is authoritative for this deployment.

The first three (music/film/dining) are the original demo domains; the rest are
**additive** — recognised only when a Taste page lists them, never required. A
Taste page with only Music/Film/Food scores and calls exactly as before.

**Response fields (additive — never renamed or removed):**
- `shared_tags: string[]` — readable shared taste descriptors (the "why you match"
  headline).
- `demographics: {a, b, note} | null` — per person `{top_age, gender_lean,
  age:{bucket:skew}, gender:{male,female}}`; `note` is a short comparison; `null`
  when Qloo has no read (e.g. the offline fixture).
- `domains[].domain` and `date_ideas[].kind` range over the ten domain keys above.

**Also available (enumerated, not needed by the match):** `GET /v2/tags`
(resolve freeform text → tag URNs) and `GET /v2/audiences` /
`GET /v2/audiences/types` (`signal.demographics.audiences`); `signal.location`,
`filter.location.radius` (metres), `filter.popularity.min/max` (0–1 percentile),
`filter.exclude.*`, and `filter.type=urn:heatmap` (geo grid). The engine sticks to
the four call shapes above — the ones that improve a *pair* taste match.

## Live vs fixture

`qloo_client.get_client()` returns the live client when `QLOO_API_KEY` is set
(Secret Manager → Cloud Run in production), else `FixtureQlooClient` — a
deterministic mini taste graph in `qloo_fixture.json` (72 real, well-known
entities across all ten domains; tags illustrative, NOT Qloo data) scoring
recommendations by shared tags, with `tags()` / `demographics()` offline
stand-ins (demographics degrades to `null`). Any live failure (timeout, auth,
unexpected payload) falls back to the fixture for that request. Every response
carries `source: "qloo" | "fixture"`; the UI shows a "sample data" chip on fixture.

Rate limit: the hackathon key allows 10 requests/second and one match makes ~25
calls, so `LiveQlooClient` paces calls process-wide at 8/s and retries a 429 up to
twice after the one-second window resets.

Config (`config.py`): `QLOO_API_BASE_URL` (default
`https://hackathon.api.qloo.com`), `QLOO_TIMEOUT_SECONDS` (default 6). The
`QLOO_API_KEY` secret is read from the environment at the call site (Secret
Manager → Cloud Run in production; an env var locally), never stored in config or
code. With no key, the match runs entirely on the offline fixture.

## Kill switch

A single runtime feature flag, `qloo_enabled` (default on), short-circuits
`taste_match.match` **before any outbound Qloo call** and prevents
`qloo_client.get_client()` from ever handing out a live client — so Qloo billing
can be stopped instantly, with no redeploy, if hackathon credits run out. When off
the taste features degrade to the no-taste empty state.

## API

- `POST /taste/pair {other_uid}` — signed in, 18+. Caller × other user, both from
  their PUBLIC views; blocked/deleted → 404. Shown as the "Taste match" card on the
  AI Date Simulation result.
- `GET /match/{match_id}` → `taste` — the match-compatibility report embeds the
  SAME taste match as a labeled "Taste match · powered by Qloo" section
  (`taste_match.report_section`, reusing the `/taste/pair` engine — no duplicated
  Qloo calls). The `taste` value is the payload with `status: "ok"`, a
  `{"status":"no_taste","message":…}` empty-state marker when one/both lack a public
  Taste page, or `null` on any other failure (the report never errors).

Response: `{source, a:{name}, b:{name}, score, score_label, summary, shared[],
shared_tags[], demographics:{a,b,note}|null, domains:[{domain, score}],
date_ideas:[{name, kind, why, address}]}`. No taste page → 404
`{"code":"no_taste","message":…}`.

## Privacy & cost

Public profile data only, for both people (also for the caller — the caller's own
private pages are not used). Only entity names a person published are sent to Qloo
— including the demographics call, which sends **only taste entity ids, never user
identity** (name, uid, birthdate, gender, location are never sent). The
`demographics` block is the *audience* Qloo associates with those public tastes,
not the user's own attributes. The match itself is not credit-metered (Qloo
hackathon key, no LLM call).

## Files (self-contained for the public-repo extraction)

`taste_match.py`, `qloo_client.py`, `qloo_fixture.json`,
`config.py`, `demo_taste.py`, and `tests/`. The private-core dependencies
(`public_profile`, `story`, `auth`, `db`, `feature_flags`, `practice_date`) are
documented as external and reproduced only by the test-only stand-ins in
`backend/_stubs/`. See `EXTRACTION_INVENTORY.md` for a file-by-file origin.
