"""Deterministic intent. The model does not choose tools."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.routing.types import RouteProfile
from app.search.text import fold

Kind = Literal["search", "route", "nearest", "here"]

# Longest first: _strip_route_words removes these in order, so "how do i
# get to" must go before "how do i get" leaves a dangling "to".
_ROUTE = (
    "how can i get to",
    "how do i get to",
    "how can i reach",
    "how do i get",
    "how can i",
    "directions to",
    "directions",
    "take me to",
    "take me",
    "route to",
    "كيف أصل",
    "كيف اوصل",
    "وصلني",
    "خذني",
    "خدني",
    "وديني",
    "دلني",
    "איך מגיעים",
    "איך להגיע",
    "תיקח אותי",
    "קח אותי",
)
# "to" left over after the route phrase: إلى/الى/على, Hebrew ל as "ל-" or "ל ".
_LEADING_TO = re.compile(r"^(?:to|إلى|الى|على|لـ|ל-|ל)\s*(?=\S)", re.IGNORECASE)
_NEAREST = ("nearest", "closest", "أقرب", "اقرب", "הכי קרוב")
_HERE = ("where did i start", "where am i", "وين بدأت", "איפה התחלתי")
_WHEELCHAIR = ("wheelchair", "كرسي متحرك", "כיסא גלגלים", "נגיש")
_STAIRS = ("without stairs", "avoid stairs", "no stairs", "بدون درج", "بدون سلالم", "בלי מדרגות")
_BATHROOM = ("bathroom", "restroom", "toilet", "wc", "حمام", "שירותים")
_ATM = ("atm", "cash", "כספומט", "صراف")

_FROM_TO = re.compile(
    r"(?:from|من|מ)\s+(.+?)\s+(?:to|إلى|الى|ל)\s+(.+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Intent:
    kind: Kind
    query: str
    origin_query: str | None
    destination_query: str | None
    profile: RouteProfile


def parse_intent(message: str, requested: RouteProfile) -> Intent:
    folded = fold(message)
    profile = _profile(folded, requested)
    if any(phrase in folded for phrase in _HERE):
        return Intent("here", message, None, None, profile)
    facility = _facility(folded)
    origin, destination = _from_to(message)
    if facility is not None and any(phrase in folded for phrase in _NEAREST):
        return Intent("nearest", facility, None, facility, profile)
    if origin and destination:
        return Intent("route", message, origin, destination, profile)
    if any(phrase in folded for phrase in _ROUTE):
        target = destination or _strip_route_words(message)
        return Intent("route", target, origin, target, profile)
    # Search the facility word ("atm", "bathroom"), not the raw sentence.
    # "איפה הכספומט?" contains the Hebrew word with a definite ה, which is
    # not the stored synonym. The facility detector already recognized it.
    if facility is not None:
        return Intent("search", facility, None, facility, profile)
    return Intent("search", message, None, None, profile)


def _profile(folded: str, requested: RouteProfile) -> RouteProfile:
    if any(phrase in folded for phrase in _WHEELCHAIR):
        return RouteProfile.WHEELCHAIR
    if requested is RouteProfile.WHEELCHAIR:
        return requested
    if any(phrase in folded for phrase in _STAIRS):
        return RouteProfile.AVOID_STAIRS
    return requested


def _facility(folded: str) -> str | None:
    if any(phrase in folded for phrase in _BATHROOM):
        return "bathroom"
    if any(phrase in folded for phrase in _ATM):
        return "atm"
    return None


def _from_to(message: str) -> tuple[str | None, str | None]:
    match = _FROM_TO.search(message.strip())
    if match is None:
        return None, None
    return match.group(1).strip(" ?."), match.group(2).strip(" ?.")


def _strip_route_words(message: str) -> str:
    text = message.replace("?", " ").replace("؟", " ")
    for phrase in _ROUTE:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    text = " ".join(text.split())
    # Hebrew ל glued to a Hebrew word (לשירותים) is part of the word; only
    # strip it when a hyphen or space separates it, or before a Latin name.
    if text.startswith("ל") and len(text) > 1 and text[1] not in "- " and not text[1].isascii():
        return text
    return _LEADING_TO.sub("", text, count=1).strip()
