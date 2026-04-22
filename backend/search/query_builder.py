"""Query composition utilities for textbook discovery.

The builder supports a conservative `rights_only` mode that avoids generic
"dorking" patterns and instead prefers open repositories and institutional
open-access portals.
"""

from __future__ import annotations

from typing import Iterable, List

OPEN_REPOSITORY_HINTS = [
    'site:oercommons.org',
    'site:openstax.org',
    'site:open.umn.edu',
    'site:doaj.org',
    'site:directory.doabooks.org',
    'site:archive.org',
    '"open educational resources"',
    '"public domain"',
    '"open access"',
    '"creative commons"',
]

GENERIC_HINTS = [
    '"textbook"',
    '"pdf"',
    '"edition"',
]


def _clean_terms(terms: Iterable[str]) -> List[str]:
    return [term.strip() for term in terms if term and term.strip()]


def build_query(
    terms: Iterable[str],
    *,
    rights_only: bool = False,
    limit: int = 8,
) -> str:
    """Build a provider-facing search query.

    Args:
        terms: Subject, title, or author terms from the user.
        rights_only: Prefer open-license/public-domain sources when True.
        limit: Upper bound for number of repository hints included.
    """

    cleaned_terms = _clean_terms(terms)
    if not cleaned_terms:
        raise ValueError("At least one search term is required.")

    # Preserve user intent first.
    base = " ".join(f'"{t}"' if " " in t else t for t in cleaned_terms)

    hints = OPEN_REPOSITORY_HINTS if rights_only else GENERIC_HINTS + OPEN_REPOSITORY_HINTS
    selected_hints = hints[: max(1, limit)]

    if rights_only:
        # In rights mode we hard-require open/policy-safe context words.
        rights_guard = '("open access" OR "public domain" OR "creative commons" OR OER)'
        return f"{base} {rights_guard} {' '.join(selected_hints)}"

    return f"{base} {' '.join(selected_hints)}"
