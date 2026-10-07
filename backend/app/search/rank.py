"""Lexical bands and hybrid merge.

Scores are not a weighted guess. They are ordered bands so a later band
cannot outrank an earlier one:

    exact name/slug            1.00
    name contained as a token  0.96
    prefix                     0.90
    name trigram               0.75 .. 0.85   (pg_trgm, or 0.80 for one edit)
    category name/slug         0.70
    store keyword              0.65
    category keyword / phrase  0.60

Every band above is a lexical decision. `lexical_gate` includes keyword:
a curated synonym is deterministic, so a vector neighbor must not reorder it.
Vectors only answer a query that missed all of these bands.

Trigram uses pg_trgm `similarity`, which is already 0..1. It is scaled into
the open interval (0.75, 0.85] so the best typo still sits strictly below
prefix (0.90) and strictly above category (0.70). The 0.10 width is only
there to order two typos against each other. A one-character edit on a
short name scores a fixed 0.80 in that same band: pg_trgm reports
similarity('nkie','nike') ≈ 0.11, under the 0.3 cutoff, because a
4-letter transposition replaces almost every padded trigram.

Keyword hits stay under category on purpose: "food" should list the food
category, while "running shoes" (a phrase, not a category) still surfaces
but must not beat an exact store name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.search.text import SLUG_KEYWORDS, fold, match_forms, tokenize, within_one_edit

MatchType = Literal["exact", "prefix", "trigram", "category", "keyword", "semantic", "hybrid"]

# pg_trgm's default cutoff. Below this, "N" matches almost everything.
TRIGRAM_MIN = 0.3
# Published RRF constant (Cormack, Clarke, Buettcher, SIGIR 2009).
RRF_K = 60


@dataclass(frozen=True)
class ScoredHit:
    location_id: str
    slug: str
    score: float
    match_type: MatchType


def lexical_score(
    query: str,
    *,
    name: str,
    slug: str,
    category_slug: str,
    category_names: tuple[str, ...],
    search_text: str,
    name_similarity: float,
) -> tuple[float, MatchType] | None:
    q = fold(query)
    if q == "":
        return None
    folded_name = fold(name)
    folded_slug = fold(slug.replace("-", " "))
    if q in (folded_name, fold(slug), folded_slug):
        return 1.0, "exact"

    tokens = tokenize(query)
    token_set = set(tokens)
    if folded_name in token_set or fold(slug) in token_set:
        return 0.96, "exact"

    if len(q) >= 2 and (folded_name.startswith(q) or fold(slug).startswith(q)):
        return 0.90, "prefix"

    # 0.80 is inside the trigram band: below prefix 0.90, above category 0.70.
    if len(q) >= 4 and (within_one_edit(q, folded_name) or within_one_edit(q, fold(slug))):
        return 0.80, "trigram"

    if name_similarity >= TRIGRAM_MIN:
        # Map [0.3, 1] onto (0.75, 0.85].
        span = (name_similarity - TRIGRAM_MIN) / (1.0 - TRIGRAM_MIN)
        return 0.75 + 0.10 * span, "trigram"

    category_forms = {fold(category_slug), *(fold(item) for item in category_names)}
    if q in category_forms or token_set & category_forms:
        return 0.70, "category"

    forms = {q}
    for token in tokens:
        forms |= match_forms(token)

    def hits(haystack: str) -> bool:
        return any(len(form) >= 3 and form in haystack for form in forms)

    # A store's own synonym (Starbucks: "coffee") beats the same word reached
    # through its category (food: "coffee"), which every restaurant shares.
    if hits(fold(" ".join(SLUG_KEYWORDS.get(slug, ())))):
        return 0.65, "keyword"
    if hits(fold(search_text)):
        return 0.60, "keyword"
    return None


def lexical_gate(match_type: MatchType) -> bool:
    """These matches are specific enough that embeddings must not reorder them.

    Keyword is included. "cash" and "running shoes" are curated synonyms.
    Letting cosine similarity outrank them would undo the lexical decision.
    """
    return match_type in {"exact", "prefix", "trigram", "category", "keyword"}


def allow_semantic_only(query: str, lexical: list[ScoredHit]) -> bool:
    """A short unknown name (Gucci) is a refusal, not a nearest-neighbor guess.

    Multi-word paraphrases with no lexical hit may use vectors. A one or two
    token string that missed exact, prefix, trigram, category, and keywords
    is treated as a name we do not have.
    """
    if lexical:
        return True
    return len(tokenize(query)) >= 3


def reciprocal_rank_fusion(
    lists: list[list[ScoredHit]],
    *,
    k: int = RRF_K,
) -> list[ScoredHit]:
    """Merge ranked lists by 1/(k+rank). Score scales are not compared."""
    pooled: dict[str, tuple[float, ScoredHit]] = {}
    for ranked in lists:
        for index, hit in enumerate(ranked, start=1):
            addition = 1.0 / (k + index)
            current = pooled.get(hit.location_id)
            if current is None:
                pooled[hit.location_id] = (addition, hit)
            else:
                pooled[hit.location_id] = (current[0] + addition, current[1])
    ordered = sorted(pooled.values(), key=lambda item: item[0], reverse=True)
    merged: list[ScoredHit] = []
    for score, hit in ordered:
        merged.append(
            ScoredHit(
                location_id=hit.location_id,
                slug=hit.slug,
                score=score,
                match_type="hybrid",
            )
        )
    return merged


def merge_hits(
    query: str,
    lexical: list[ScoredHit],
    semantic: list[ScoredHit],
) -> list[ScoredHit]:
    if lexical and lexical_gate(lexical[0].match_type):
        seen = {hit.location_id for hit in lexical}
        return lexical + [hit for hit in semantic if hit.location_id not in seen]
    if not semantic:
        return lexical
    if not lexical and not allow_semantic_only(query, lexical):
        return []
    return reciprocal_rank_fusion([lexical, semantic])
