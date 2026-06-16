"""Single source of truth for dream-symbol tokenization, light normalization,
stopwords and label cleaning.

Used by rag_service and map_service so this logic can't drift across call sites
(it previously lived in three places with three different stopword lists — see
docs/SYMBOLS_RAG_CORE.md §3.7).

Design note: symbol *extraction* is the LLM's job (symbol_entities in /analyze)
and *grouping* of near-synonyms is done by embedding clustering (see
map_service). This module is deliberately light — lowercase folding, a tiny
synonym map, stopword/length filtering and surface-form label cleaning. It backs
the low-stakes frequency fallback / RAG symbol-overlap signal, NOT the primary
quality path. (We intentionally do NOT lemmatize/POS-tag here anymore.)
"""

from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache

# Standalone-symbol tokens: 3+ letters, Cyrillic or Latin.
_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]{3,}", re.UNICODE)
# Words inside a multi-word label: 2+ letters (keeps short adjectives like "злой").
_LABEL_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]{2,}", re.UNICODE)

# Tiny curated synonym merges (cheap exact folding; embedding clustering catches
# the rest semantically). Keep minimal.
_ALIASES = {
    "мама": "мать",
    "папа": "отец",
}

# Stopwords / generic meta-words filtered from symbols and labels. Merged from
# the former rag_service._STOPWORDS / _ENTITY_STOPWORDS and
# map_service._GENERIC_SYMBOLS / _LABEL_STOPWORDS.
STOPWORDS = {
    # function words / fillers
    "это", "как", "что", "когда", "потом", "после", "меня", "мне", "было", "были",
    "очень", "будто", "снова", "там", "здесь", "этот", "эта", "эти", "который",
    "которая", "которые", "которое", "свой", "свои", "только", "через", "между",
    "вокруг", "себя", "него", "неё", "если", "или", "для", "над", "под", "без",
    "она", "они", "оно", "его", "её", "уже", "того", "где", "чуть", "есть",
    "находит", "находить", "следующий", "следующая", "следующее", "типа", "тип",
    "кстати", "вроде", "каких", "какой", "какая", "какие", "какое", "возможно",
    "возможный", "возможная", "возможные", "такой", "такая", "такие",
    "единственное", "просто", "вообще", "сразу", "кто", "вот", "ещё", "еще",
    # latin function words
    "the", "and", "with", "from", "into", "that", "this", "have", "then", "they",
    "them", "was", "were", "about", "because", "while", "where", "there", "you",
    "had", "for", "not", "but",
    # generic meta-nouns with no dream-symbol meaning
    "сон", "сны", "сна", "сне", "человек", "люди", "людей", "место", "штука",
    "вещь", "компания", "компании", "трекинг", "tracking", "gps",
    # domain noise the product chose to exclude
    "эльф", "эльфов", "эльфы", "фея", "фей", "феи",
}


@lru_cache(maxsize=8192)
def normalize_symbol(token: str) -> str:
    """Fold a token to a cheap canonical form: lowercased + tiny synonym map.
    NOT a lemmatizer — semantic grouping is done via embedding clustering."""
    base = (token or "").strip().lower()
    if not base:
        return ""
    return _ALIASES.get(base, base)


def is_meaningful_symbol(token: str) -> bool:
    """True if the token can stand alone as a symbol: non-stopword, 3+ chars,
    not numeric. Used for the frequency fallback and as a light guard on
    LLM-supplied canonical names."""
    s = normalize_symbol(token)
    if len(s) < 3 or s.isdigit():
        return False
    if s in STOPWORDS or (token or "").strip().lower() in STOPWORDS:
        return False
    return True


def extract_symbols(text: str, limit: int = 8) -> list[str]:
    """Frequency-ranked canonical symbols from free text. Low-stakes fallback /
    RAG symbol-overlap signal — the LLM is the real extractor."""
    counts: Counter = Counter()
    for match in _TOKEN_RE.finditer(text or ""):
        s = normalize_symbol(match.group(0))
        if s and is_meaningful_symbol(s):
            counts[s] += 1
    return [name for name, _count in counts.most_common(limit)]


def clean_label(raw: str, max_words: int = 3) -> str:
    """Clean a multi-word display label, keeping SURFACE word forms (so
    adjectives like 'чёрная' stay intact for humans), dropping stopwords /
    generic meta-nouns, capped at max_words."""
    words: list[str] = []
    for match in _LABEL_WORD_RE.finditer((raw or "").lower()):
        word = match.group(0)
        if len(word) < 2:
            continue
        if word in STOPWORDS or normalize_symbol(word) in STOPWORDS:
            continue
        words.append(word)
        if len(words) >= max_words:
            break
    return " ".join(words)
