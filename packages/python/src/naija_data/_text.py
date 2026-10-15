"""Text matching shared by lookups and fuzzy search.

The exact same rules are implemented in the JS and Go packages, and the shared parity tests in
fixtures/ check that all three agree. Only integer arithmetic is used for scores so results are
identical in every language.
"""

from __future__ import annotations

import re
import unicodedata

_DROP_TRAILING = ("state", "lga")


def norm(text: str) -> str:
    """Comparison key: 'Akwa-Ibom State' -> 'akwaibom', 'Ikeja LGA' -> 'ikeja'."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    text = text.replace("&", " and ")
    words = re.sub(r"[^a-z0-9]+", " ", text).split()
    while len(words) > 1 and words[-1] in _DROP_TRAILING:
        words.pop()
    return "".join(words)


def distance(a: str, b: str) -> int:
    """Optimal string alignment distance (edits: insert, delete, substitute, swap neighbours)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return max(la, lb)
    prev2: list[int] = []
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[lb]


def score(query: str, term: str) -> int:
    """Similarity of two normalised strings, 0..1000.

    1000 exact; 900-999 the term starts with the query; otherwise up to 800 by edit distance.
    """
    if not query or not term:
        return 0
    if query == term:
        return 1000
    if len(query) >= 2 and term.startswith(query):
        return 900 + (99 * len(query)) // len(term)
    longest = max(len(query), len(term))
    return ((longest - distance(query, term)) * 800) // longest
