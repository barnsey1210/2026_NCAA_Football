#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any, Iterable

from team_identity import canonical_team, canonical_team_name

MASCOTS = (
    r"cardinals|tigers|bulldogs|wildcats|crimson tide|buckeyes|ducks|longhorns|"
    r"fighting irish|nittany lions|hurricanes|aggies|rebels|volunteers|wolverines|"
    r"broncos|horned frogs|red raiders|cougars|seminoles|panthers|yellow jackets|"
    r"razorbacks|gamecocks|hokies|cavaliers|wolfpack|wolf pack|mountaineers|bears|"
    r"knights|mustangs|utes|cyclones|jayhawks|terrapins|spartans|boilermakers|"
    r"badgers|cornhuskers|golden gophers|scarlet knights|demon deacons|orange|"
    r"blue devils|tar heels|golden bears|sun devils|huskies|buffaloes|beavers|"
    r"cardinal|red wolves|fighting illini|49ers|fightin blue hens|golden flashes|"
    r"thundering herd|redhawks|midshipmen|bobcats|sooners|golden hurricane|"
    r"blazers|hornets|warhawks|dukes"
)

ALIASES = {
    "ohio st": "ohio state",
    "penn st": "penn state",
    "florida st": "florida state",
    "miami fl": "miami florida",
    "miami": "miami florida",
    "nc state": "north carolina state",
    "ole miss": "mississippi",
    "ok state": "oklahoma state",
    "k state": "kansas state",
    "ga tech": "georgia tech",
    "va tech": "virginia tech",
    "s florida": "south florida",
    "e carolina": "east carolina",
    "n illinois": "northern illinois",
    "w michigan": "western michigan",
    "n mexico st": "new mexico state",
    "app state": "appalachian state",
    "central fl": "central florida",
    "unc": "north carolina",
    "fl atlantic": "florida atlantic",
    "michigan st": "michigan state",
    "fiu": "florida international",
    "jax state": "jacksonville state",
    "middle tenn": "middle tennessee",
    "missouri st": "missouri state",
    "w kentucky": "western kentucky",
    "c michigan": "central michigan",
    "e michigan": "eastern michigan",
    "sac state": "sacramento state",
    "umass": "massachusetts",
    "umass minutemen": "massachusetts",
    "boston col": "boston college",
    "nd state": "north dakota state",
    "oregon st": "oregon state",
    "washington st": "washington state",
    "mississippi st": "mississippi state",
    "s carolina": "south carolina",
    "coastal car": "coastal carolina",
    "ga southern": "georgia southern",
    "la monroe": "ul monroe",
    "la monroe warhawks": "ul monroe",
    "s alabama": "south alabama",
    "arkansas st": "arkansas state",
    "boise st": "boise state",
    "colorado st": "colorado state",
    "fresno st": "fresno state",
    "georgia st": "georgia state",
    "kent st": "kent state",
    "san diego st": "san diego state",
    "san jose st": "san jose state",
    "texas st": "texas state",
    "uconn": "connecticut",
    "wv": "west virginia",
    "la tech": "louisiana tech",
    "ucf": "central florida",
    "jmu": "james madison",
    "kennesaw st": "kennesaw state",
}


def normalize_market_team(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("&", "and").replace("hawai'i", "hawaii")
    text = re.sub(rf"\b({MASCOTS})\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = " ".join(text.split())
    return ALIASES.get(text, text)


def resolve_market_team(value: Any, canonical_names: Iterable[str]) -> str | None:
    # Exact canonical/configured-alias resolution remains first authority.
    exact = canonical_team_name(value)
    if exact:
        return exact

    names = list(canonical_names)
    by_norm = {normalize_market_team(name): name for name in names}
    key = normalize_market_team(value)

    if key in by_norm:
        return by_norm[key]

    # Preserve the proven Odds rule: unique prefix relationship only.
    candidates = [
        name
        for norm, name in by_norm.items()
        if len(key) >= 3 and (
            key.startswith(norm + " ")
            or norm.startswith(key + " ")
        )
    ]
    return candidates[0] if len(candidates) == 1 else None
