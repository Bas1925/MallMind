"""Search text for a location.

The string stored for trigram and embedding is built here so reindex and
query ranking cannot drift. Store names stay as seeded. Extra phrases are
deliberate synonyms (cash, running shoes, Hebrew/Arabic category words),
not a second catalog.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

# Tokens that never identify a place. Kept short on purpose.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "from",
        "of",
        "in",
        "on",
        "at",
        "for",
        "me",
        "my",
        "i",
        "is",
        "are",
        "where",
        "how",
        "do",
        "can",
        "get",
        "find",
        "nearest",
        "closest",
        "please",
        "want",
        "need",
        "somewhere",
        "some",
        "place",
        "איפה",
        "יש",
        "את",
        "של",
        "אני",
        "לי",
        "אתה",
        "وين",
        "أين",
        "اين",
        "في",
        "من",
        "إلى",
        "الى",
        "هل",
        "أريد",
        "اريد",
        "أبغى",
        "ابغى",
    }
)

# Category-level phrases. A query that contains one of these should hit
# every location in that category via substring match, not via embeddings.
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "restroom": ("bathroom", "restroom", "toilet", "wc", "حمام", "دورة مياه", "שירותים"),
    "atm": ("atm", "cash", "withdraw money", "כספומט", "صراف", "صراف آلي"),
    "food": ("food", "restaurant", "cafe", "coffee", "مطعم", "طعام", "אוכל", "קפה"),
    "fashion": ("clothes", "clothing", "ملابس", "בגדים"),
    "electronics": ("electronics", "phone", "إلكترونيات", "אלקטרוניקה"),
    "elevator": ("elevator", "lift", "مصعد", "מעלית"),
    "escalator": ("escalator", "سلم متحرك", "דרגנוע"),
    "entrance": ("entrance", "entry", "مدخل", "כניסה"),
    "stairs": ("stairs", "staircase", "سلالم", "מדרגות"),
    "services": ("pharmacy", "information", "صيدلية", "בית מרקחת"),
}

# Slug phrases that are narrower than the category. "running shoes" is Nike,
# not every fashion store. "jogging" is intentionally absent so semantic
# search has a paraphrase the keyword list does not cover.
SLUG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "nike": ("running shoes", "sneakers", "sportswear", "נעלי ספורט", "أحذية رياضية"),
    "adidas": ("sportswear", "sneakers"),
    "apple": ("iphone", "laptop"),
    "samsung": ("galaxy", "phone"),
    "starbucks": ("coffee",),
    "mcdonalds": ("burger", "restaurant"),
    "pizza-napoli": ("pizza",),
    "sushi-kaito": ("sushi",),
    "nova-cinema": ("cinema", "movie", "movies", "سينما", "קולנוע"),
    "pages-bookstore": ("books", "bookstore", "كتب", "ספרים"),
    "super-pharm": ("pharmacy",),
    "main-entrance": ("main entrance", "المدخل الرئيسي", "כניסה ראשית"),
    "parking-entrance": ("parking", "موقف", "חניה"),
    "guest-services": ("information desk", "lost and found"),
    "rooftop-cafe": ("cafe", "coffee"),
    "muji": ("home goods",),
}


def fold(value: str) -> str:
    """Casefold and strip accents/tatweel so 'Nike' and 'nike' compare equal."""
    normalized = unicodedata.normalize("NFKC", value).replace("\u0640", "")
    return " ".join(normalized.casefold().split())


def match_forms(token: str) -> set[str]:
    """Token plus one definite-article strip, for keyword lookup only.

    "הכספומט" is "the ATM" in Hebrew. The stored synonym is "כספומט".
    Arabic "ال" is the same idea. Names are not stripped.
    """
    forms = {token}
    if token.startswith("ال") and len(token) > 3:
        forms.add(token[2:])
    elif token.startswith("ה") and len(token) > 2:
        forms.add(token[1:])
    return forms


def tokenize(value: str) -> list[str]:
    raw = re.findall(r"[0-9A-Za-z\u0590-\u05FF\u0600-\u06FF]+", fold(value))
    return [token for token in raw if token not in _STOPWORDS and len(token) > 1]


def build_search_text(
    *,
    name: str,
    slug: str,
    description: str | None,
    category_slug: str,
    category_en: str,
    category_he: str,
    category_ar: str,
) -> str:
    parts = [
        name,
        slug.replace("-", " "),
        category_en,
        category_he,
        category_ar,
        category_slug,
        description or "",
        " ".join(CATEGORY_KEYWORDS.get(category_slug, ())),
        " ".join(SLUG_KEYWORDS.get(slug, ())),
    ]
    return fold(" ".join(part for part in parts if part))


def within_one_edit(left: str, right: str) -> bool:
    """One insertion, deletion, substitution, or adjacent transposition.

    pg_trgm similarity of a 4-letter transposition (`nkie` / `nike`) is about
    0.11, under the 0.3 cutoff, because almost every padded trigram changes.
    Edit distance still sees a single typo. Longer strings keep using pg_trgm.
    """
    if abs(len(left) - len(right)) > 1:
        return False
    if left == right:
        return True
    if len(left) == len(right):
        mismatches = [index for index, (a, b) in enumerate(zip(left, right, strict=True)) if a != b]
        if len(mismatches) == 1:
            return True
        if len(mismatches) == 2:
            first, second = mismatches
            return (
                second == first + 1
                and left[first] == right[second]
                and left[second] == right[first]
            )
        return False
    if len(left) > len(right):
        left, right = right, left
    # left is one character shorter. One insertion in left explains right.
    for index, char in enumerate(left):
        if char != right[index]:
            return left[index:] == right[index + 1 :]
    return True


def content_hash(model_name: str, search_text: str) -> str:
    payload = f"{model_name}\n{search_text}".encode()
    return hashlib.sha256(payload).hexdigest()
