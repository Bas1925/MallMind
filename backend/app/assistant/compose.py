"""Template answers. Used when no LLM is configured, and whenever model text fails the guard."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.search import SearchHitOut

_ALLOW = frozenset(
    {
        "nova",
        "mall",
        "ground",
        "level",
        "floor",
        "walk",
        "about",
        "wheelchair",
        "route",
        "stairs",
        "elevator",
    }
)


@dataclass(frozen=True)
class RouteCopy:
    origin: str
    destination: str
    distance_m: float
    estimated_seconds: float
    instruction: str
    profile: str


def location_answer(language: str, hit: SearchHitOut) -> str:
    if language == "ar":
        return f"{hit.name} في {hit.floor} ({hit.category})."
    if language == "he":
        return f"{hit.name} נמצא ב{hit.floor} ({hit.category})."
    return f"{hit.name} is on {hit.floor} ({hit.category})."


def choices_answer(language: str, hits: list[SearchHitOut]) -> str:
    names = ", ".join(hit.name for hit in hits[:3])
    if language == "ar":
        return f"لقيت أكثر من مكان: {names}."
    if language == "he":
        return f"מצאתי כמה מקומות: {names}."
    return f"I found a few places: {names}."


def route_answer(language: str, route: RouteCopy) -> str:
    minutes = max(1, round(route.estimated_seconds / 60))
    distance = round(route.distance_m)
    profile = ""
    if route.profile == "wheelchair":
        profile = {
            "ar": " مسار بالكرسي المتحرك.",
            "he": " מסלול נגיש לכיסא גלגלים.",
            "en": " Wheelchair route.",
        }[language if language in {"ar", "he"} else "en"]
    elif route.profile == "avoid_stairs":
        profile = {
            "ar": " بدون سلالم.",
            "he": " בלי מדרגות.",
            "en": " Avoiding stairs.",
        }[language if language in {"ar", "he"} else "en"]
    if language == "ar":
        return (
            f"من {route.origin} إلى {route.destination}: {distance} متر، "
            f"حوالي {minutes} دقائق. {route.instruction}{profile}"
        )
    if language == "he":
        return (
            f"מ-{route.origin} אל {route.destination}: {distance} מטר, "
            f"בערך {minutes} דקות. {route.instruction}{profile}"
        )
    return (
        f"{route.origin} → {route.destination}: {distance} m, about {minutes} min. "
        f"{route.instruction}{profile}"
    )


def here_answer(language: str, hit: SearchHitOut) -> str:
    if language == "ar":
        return f"نقطة البداية هي {hit.name} في {hit.floor}."
    if language == "he":
        return f"נקודת ההתחלה היא {hit.name} ב{hit.floor}."
    return f"You started at {hit.name} on {hit.floor}."


def missing_start_answer(language: str) -> str:
    if language == "ar":
        return "ما في نقطة بداية بعد. اختر مكان الانطلاق من نموذج المسار."
    if language == "he":
        return "אין עדיין נקודת התחלה. בחרו מקום יציאה בטופס המסלול."
    return "I don't have a starting point yet. Pick one on the route form."


def refusal_answer(language: str) -> str:
    if language == "ar":
        return "ما لقيت هذا المكان في NOVA Mall."
    if language == "he":
        return "לא מצאתי את המקום הזה ב-NOVA Mall."
    return "I couldn't find that location in NOVA Mall."


def no_route_answer(language: str, origin: str, destination: str) -> str:
    if language == "ar":
        return f"ما في مسار من {origin} إلى {destination} بهذا الخيار."
    if language == "he":
        return f"אין מסלול מ-{origin} אל {destination} בפרופיל הזה."
    return f"There is no route from {origin} to {destination} for this profile."


def answer_is_grounded(answer: str, source_names: set[str], known_names: set[str]) -> bool:
    """Reject text that names a real mall place we did not retrieve, or an English proper noun."""
    folded_answer = answer.casefold()
    sources = {name.casefold() for name in source_names}
    for name in known_names:
        token = name.casefold()
        if token and token in folded_answer and token not in sources:
            return False
    for word in re.findall(r"[A-Z][A-Za-z]{2,}", answer):
        token = word.casefold()
        if token in _ALLOW:
            continue
        if any(token in source.casefold() for source in source_names):
            continue
        return False
    return True
