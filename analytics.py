"""Аналитика по объявлениям (Исматов А.): срок показа, активность, группировка похожих (FR-03).

Похожие объявления разных рекламодателей объединяются в группу по ключу:
домен лендинга + «отпечаток» текста (набор значимых слов без цифр и стоп-слов).
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

ACTIVE_DAYS = 3          # объявление считается активным, если его видели за последние N дней

STOP = {
    "a", "al", "con", "de", "del", "el", "en", "es", "la", "las", "los", "para", "por", "que", "su", "tu", "un",
    "una", "y", "i", "w", "z", "na", "do", "nie", "to", "il", "di", "e", "per", "che", "der", "die", "und", "das",
    "the", "and", "of", "for", "your", "you", "with", "in", "on",
}


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def days_active(first_seen: str, last_seen: str) -> int:
    """Сколько дней объявление в показах (минимум 1 — увидели хотя бы один раз)."""
    delta = _parse(last_seen) - _parse(first_seen)
    return max(1, delta.days + 1)


def is_active(last_seen: str, today: datetime) -> bool:
    return (today - _parse(last_seen)).days < ACTIVE_DAYS


def fingerprint(caption: str, top: int = 6) -> str:
    """Отпечаток текста: самые длинные значимые слова в алфавитном порядке (цифры бонусов не учитываются,
    чтобы «500% + 250 FS» и «300% + 100 FS» одного оффера попали в одну группу)."""
    words = re.findall(r"[^\W\d_]{3,}", (caption or "").lower())
    uniq = sorted({w for w in words if w not in STOP}, key=lambda w: (-len(w), w))[:top]
    return " ".join(sorted(uniq))


def group_key(caption: str, domain: str) -> str:
    fp = fingerprint(caption)
    if not fp and not domain:
        return ""
    return hashlib.sha1(f"{domain}|{fp}".encode(), usedforsecurity=False).hexdigest()[:12]


def jaccard(a: str, b: str) -> float:
    """Схожесть двух текстов по множеству слов (0..1) — для проверки качества группировки."""
    sa, sb = set(fingerprint(a, 50).split()), set(fingerprint(b, 50).split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)
