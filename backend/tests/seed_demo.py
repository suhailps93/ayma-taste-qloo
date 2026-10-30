"""The four fabricated demo profiles, seeded into a :class:`FakeDb`.

These mirror the public "Taste" pages of Ayma's seeded synthetic demo profiles
(``demo_practice_{maya,leo,aisha,noah}``). Nobody here is a real
person. Each carries just a name, a coarse city, and a public ``taste`` wiki
page in the exact ``Music/Film/Food`` shape ``taste_match.parse_taste`` reads.

Used by the self-contained tests (and handy for exploring the engine offline).
"""

from __future__ import annotations

from fake_firestore import FakeDb

# key -> (uid, name, city, taste page body)
DEMO = {
    "maya": (
        "demo_practice_maya",
        "Maya",
        "San Francisco",
        "Music: Khruangbin, Bon Iver, Phoebe Bridgers\n"
        "Film: Lost in Translation, Amelie, Spirited Away\n"
        "Food: Tartine Bakery, Zuni Cafe",
    ),
    "leo": (
        "demo_practice_leo",
        "Leo",
        "Oakland",
        "Music: Thelonious Monk, Khruangbin, Kamasi Washington\n"
        "Film: Blade Runner 2049, Arrival, Spirited Away\n"
        "Food: Ramen Shop, Blue Bottle Coffee",
    ),
    "aisha": (
        "demo_practice_aisha",
        "Aisha",
        "Berkeley",
        "Music: Bon Iver, Fleet Foxes, Phoebe Bridgers\n"
        "Film: My Octopus Teacher, Finding Nemo, Free Solo\n"
        "Food: Tartine Bakery, Cheese Board Collective",
    ),
    "noah": (
        "demo_practice_noah",
        "Noah",
        "San Jose",
        "Music: Fleet Foxes, The Lumineers, Kamasi Washington\n"
        "Film: Free Solo, Into the Wild, Blade Runner 2049\n"
        "Food: Blue Bottle Coffee, Philz Coffee",
    ),
}


def seeded_db() -> FakeDb:
    db = FakeDb()
    for _key, (uid, name, city, body) in DEMO.items():
        db.collection("users").document(uid).collection("profile").document(
            "main"
        ).set({"name": name, "location": city, "photos": []})
        db.collection("users").document(uid).collection("wiki_pages").document(
            "taste"
        ).set(
            {
                "page_type": "taste",
                "title": "Taste",
                "visibility": "public",
                "ai_body": body,
            }
        )
    return db
