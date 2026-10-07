"""Script detection. Reliable for Arabic and Hebrew; everything else is English.

This is not a general language-ID model. MallMind only promises these three,
and the scripts do not overlap, so a character class is the right tool.
"""

from __future__ import annotations

import re

_ARABIC = re.compile(r"[\u0600-\u06FF]")
_HEBREW = re.compile(r"[\u0590-\u05FF]")


def detect_language(text: str) -> str:
    if _ARABIC.search(text):
        return "ar"
    if _HEBREW.search(text):
        return "he"
    return "en"
