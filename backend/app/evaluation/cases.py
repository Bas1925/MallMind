"""Curated search and assistant cases. Small on purpose."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchCase:
    query: str
    language: str
    accept_slugs: frozenset[str] | None
    accept_category: str | None
    note: str


# accept_slugs None and accept_category None means we expect no hit.
SEARCH_CASES: tuple[SearchCase, ...] = (
    SearchCase("Nike", "en", frozenset({"nike"}), None, "exact name"),
    SearchCase("Nkie", "en", frozenset({"nike"}), None, "typo"),
    SearchCase("running shoes", "en", frozenset({"nike"}), None, "keyword phrase"),
    SearchCase("food", "en", None, "food", "category"),
    SearchCase("cash", "en", None, "atm", "keyword"),
    SearchCase("withdraw money", "en", None, "atm", "keyword phrase"),
    SearchCase("bathroom", "en", None, "restroom", "synonym"),
    SearchCase("כספומט", "he", None, "atm", "hebrew category word"),
    SearchCase("איפה יש כספומט", "he", None, "atm", "hebrew sentence"),
    SearchCase("حمام", "ar", None, "restroom", "arabic synonym"),
    SearchCase("مكان للصلاة", "ar", None, None, "no prayer room in NOVA; must be empty"),
    SearchCase("Gucci", "en", None, None, "unknown store; must be empty"),
    SearchCase(
        "footwear for jogging today",
        "en",
        frozenset({"nike"}),
        None,
        "paraphrase not in the keyword list; semantic only",
    ),
)


@dataclass(frozen=True)
class AssistantCase:
    message: str
    language: str
    expect: str  # slug | category | refusal | route
    accept_slug: str | None = None
    accept_category: str | None = None
    profile: str | None = None


ASSISTANT_CASES: tuple[AssistantCase, ...] = (
    AssistantCase("Where is Nike?", "en", "slug", accept_slug="nike"),
    AssistantCase("Where is Gucci?", "en", "refusal"),
    AssistantCase("وين Gucci؟", "ar", "refusal"),
    AssistantCase("איפה Gucci?", "he", "refusal"),
    AssistantCase(
        "How do I get from the main entrance to Nike?", "en", "route", accept_slug="nike"
    ),
    AssistantCase(
        "How can I reach Nike without stairs?",
        "en",
        "route",
        accept_slug="nike",
        profile="avoid_stairs",
    ),
    AssistantCase("وين أقرب حمام؟", "ar", "route", accept_category="restroom"),
    AssistantCase("איפה הכספומט?", "he", "category", accept_category="atm"),
    AssistantCase("Where can I buy running shoes?", "en", "slug", accept_slug="nike"),
)
