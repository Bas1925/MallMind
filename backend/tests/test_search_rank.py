"""Lexical bands and the hybrid gate. No database."""

from __future__ import annotations

from app.search.language import detect_language
from app.search.rank import ScoredHit, lexical_score, merge_hits
from app.search.text import build_search_text


def _nike_text() -> str:
    return build_search_text(
        name="Nike",
        slug="nike",
        description="Sportswear flagship.",
        category_slug="fashion",
        category_en="Fashion",
        category_he="אופנה",
        category_ar="أزياء",
    )


def test_exact_beats_prefix_and_trigram() -> None:
    exact = lexical_score(
        "Nike",
        name="Nike",
        slug="nike",
        category_slug="fashion",
        category_names=("Fashion", "אופנה", "أزياء"),
        search_text=_nike_text(),
        name_similarity=1.0,
    )
    prefix = lexical_score(
        "Nik",
        name="Nike",
        slug="nike",
        category_slug="fashion",
        category_names=("Fashion",),
        search_text=_nike_text(),
        name_similarity=0.4,
    )
    typo = lexical_score(
        "Nkie",
        name="Nike",
        slug="nike",
        category_slug="fashion",
        category_names=("Fashion",),
        search_text=_nike_text(),
        name_similarity=0.5,
    )
    assert exact is not None and exact[1] == "exact" and exact[0] == 1.0
    assert prefix is not None and prefix[1] == "prefix" and prefix[0] == 0.90
    assert typo is not None and typo[1] == "trigram"
    assert exact[0] > prefix[0] > typo[0]


def test_short_transposition_is_a_typo_even_when_trigram_is_tiny() -> None:
    scored = lexical_score(
        "Nkie",
        name="Nike",
        slug="nike",
        category_slug="fashion",
        category_names=("Fashion",),
        search_text=_nike_text(),
        name_similarity=0.11,
    )
    assert scored is not None
    assert scored[1] == "trigram"
    assert scored[0] == 0.80
    guest = lexical_score(
        "Gucci",
        name="Guest Services",
        slug="guest-services",
        category_slug="services",
        category_names=("Services",),
        search_text="guest services",
        name_similarity=0.105,
    )
    assert guest is None or guest[1] != "trigram"


def test_keyword_running_shoes_hits_nike_not_as_exact() -> None:
    scored = lexical_score(
        "running shoes",
        name="Nike",
        slug="nike",
        category_slug="fashion",
        category_names=("Fashion",),
        search_text=_nike_text(),
        name_similarity=0.05,
    )
    assert scored is not None
    assert scored[1] == "keyword"
    assert scored[0] < 0.70


def test_hebrew_definite_article_still_matches_the_synonym() -> None:
    scored = lexical_score(
        "הכספומט",
        name="ATM — Ground",
        slug="atm-g",
        category_slug="atm",
        category_names=("ATM", "כספומט"),
        search_text="atm ground כספומט",
        name_similarity=0.0,
    )
    assert scored is not None
    assert scored[1] == "keyword"


def test_keyword_hit_is_not_reordered_by_a_closer_vector() -> None:
    lexical = [ScoredHit("nike-id", "nike", 0.60, "keyword")]
    semantic = [ScoredHit("adidas-id", "adidas", 0.99, "semantic")]
    merged = merge_hits("running shoes", lexical, semantic)
    assert merged[0].slug == "nike"
    assert merged[0].match_type == "keyword"


def test_unknown_short_name_is_not_replaced_by_semantic() -> None:
    semantic = [
        ScoredHit("zara-id", "zara", 0.8, "semantic"),
    ]
    merged = merge_hits("Gucci", [], semantic)
    assert merged == []


def test_exact_is_not_reordered_by_semantic() -> None:
    lexical = [ScoredHit("nike-id", "nike", 1.0, "exact")]
    semantic = [ScoredHit("adidas-id", "adidas", 0.99, "semantic")]
    merged = merge_hits("Nike", lexical, semantic)
    assert merged[0].slug == "nike"
    assert merged[0].match_type == "exact"


def test_language_detection() -> None:
    assert detect_language("Where is Nike?") == "en"
    assert detect_language("وين أقرب حمام؟") == "ar"
    assert detect_language("איפה הכספומט?") == "he"
