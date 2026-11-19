"""Модели данных SpyBase (Рязанцев Д.)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NormalizedAd:
    """Объявление после нормализации — в таком виде оно попадает в базу."""

    source_id: str
    advertiser: str
    country: str
    caption: str
    cta: str
    landing_url: str
    landing_domain: str
    seen_at: str


@dataclass
class CollectReport:
    """Итог одного прогона сборщика (пишется в collect_log)."""

    source: str
    received: int = 0
    new_ads: int = 0
    updated: int = 0
    rejected: int = 0
    reasons: list[str] = field(default_factory=list)
