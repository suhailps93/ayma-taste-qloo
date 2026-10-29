#!/usr/bin/env python3
"""Standalone Qloo taste-match demo — Music/Film/Food -> Qloo -> overlap + date ideas.

Runs the **real** taste engine (``taste_match.match`` over ``qloo_client``) on two
people's stated favourites, printing the shared-taste score, the per-domain
overlap, the tastes they share, and the Qloo-ranked date ideas.

No sign-in, no database: the two people are passed as plain
``Music: … / Film: … / Food: …`` text, exactly the shape a public Taste page
carries, and parsed by the real ``taste_match.parse_taste``.

Qloo access:
  * Set ``QLOO_API_KEY`` (a Qloo Insights API key) and it calls the **live Qloo
    API** — the response's ``source`` prints ``qloo``.
  * With no key it runs on the bundled offline fixture (``qloo_fixture.json``) —
    deterministic, no network — and ``source`` prints ``fixture``.

Usage:
    python3 demo_taste.py                 # the two built-in sample people
    python3 demo_taste.py A.txt B.txt     # two files, each with Music/Film/Food lines
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Make the extracted engine importable in isolation: the backend dir plus the
# clearly-labelled stand-ins for Ayma's private core (see _stubs/README.md).
_BACKEND = Path(__file__).resolve().parent
for _p in (str(_BACKEND / "_stubs"), str(_BACKEND)):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import taste_match  # noqa: E402

# Two sample people (San Francisco Bay Area). Edit freely, or pass two files.
PERSON_A = (
    "Ada",
    "San Francisco",
    "Music: Khruangbin, Bon Iver, Phoebe Bridgers\n"
    "Film: Lost in Translation, Amelie, Spirited Away\n"
    "Food: Tartine Bakery, Zuni Cafe",
)
PERSON_B = (
    "Leo",
    "Oakland",
    "Music: Thelonious Monk, Khruangbin, Kamasi Washington\n"
    "Film: Blade Runner 2049, Arrival, Spirited Away\n"
    "Food: Ramen Shop, Blue Bottle Coffee",
)


def _person_from_file(path: str) -> tuple[str, str, str]:
    text = Path(path).read_text(encoding="utf-8")
    name = Path(path).stem
    return name, "", text


def _to_signal(person: tuple[str, str, str]) -> tuple[str, str, dict]:
    name, city, body = person
    return name, city, taste_match.parse_taste(body)


def _print_result(result: dict) -> None:
    bar = "=" * 60
    print(bar)
    print(f"  source: {result['source']}   (qloo = live Qloo API, fixture = offline)")
    print(bar)
    print(f"  {result['a']['name']}  <->  {result['b']['name']}")
    print(f"  Taste score : {result['score']}/100 — {result['score_label']}")
    print(f"  {result['summary']}")
    print()
    print("  Per-domain overlap:")
    for d in result["domains"]:
        print(f"    - {d['domain']:<8} {d['score']}/100")
    if result["shared"]:
        print("\n  Shared tastes: " + ", ".join(result["shared"]))
    print("\n  Date ideas (Qloo-ranked for both tastes):")
    for idea in result["date_ideas"]:
        where = f" — {idea['address']}" if idea.get("address") else ""
        print(f"    - [{idea['kind']}] {idea['name']}{where}")
        print(f"        {idea['why']}")
    print(bar)


async def _run() -> None:
    args = sys.argv[1:]
    if len(args) == 2:
        a = _to_signal(_person_from_file(args[0]))
        b = _to_signal(_person_from_file(args[1]))
    else:
        a = _to_signal(PERSON_A)
        b = _to_signal(PERSON_B)
    mode = "LIVE Qloo API" if os.environ.get("QLOO_API_KEY", "").strip() else "offline fixture"
    print(f"\nRunning taste match on the {mode} ...\n")
    result = await taste_match.match(a, b)
    _print_result(result)


if __name__ == "__main__":
    asyncio.run(_run())
