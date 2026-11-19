"""Сборщик SpyBase (Рязанцев Д., компонент «Сбор данных»).

В учебном прототипе источник — JSON-файл с демо-объявлениями (data/demo_ads.json).
Реальный источник подключается через тот же интерфейс: любой итерируемый набор словарей.
Инвариант архитектуры: в базу попадает только платная реклама (is_ad = true).
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from . import analytics, classifier
from .models import CollectReport, NormalizedAd

_TRACKING = re.compile(r"^(utm_|ttclid|fbclid|gclid)", re.I)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_url(url: str) -> tuple[str, str]:
    """Убирает метки трекинга из ссылки, возвращает (чистая ссылка, домен)."""
    url = (url or "").strip()
    if not url:
        return "", ""
    parts = urlsplit(url if "://" in url else "https://" + url)
    query = "&".join(p for p in parts.query.split("&") if p and not _TRACKING.match(p))
    domain = (parts.hostname or "").removeprefix("www.")
    clean = f"{parts.scheme}://{parts.netloc}{parts.path}" + (f"?{query}" if query else "")
    return clean, domain


def normalize(raw: dict[str, Any]) -> NormalizedAd:
    """Приводит сырое объявление к единому виду. ValueError — объявление отбрасывается."""
    if not raw.get("is_ad", False):
        raise ValueError("не реклама (органический ролик)")
    source_id = str(raw.get("id") or "").strip()
    advertiser = str(raw.get("advertiser") or "").strip().lstrip("@").lower()
    country = str(raw.get("country") or "").strip().upper()
    if not source_id:
        raise ValueError("нет идентификатора")
    if not advertiser:
        raise ValueError("нет рекламодателя")
    if not re.fullmatch(r"[A-Z]{2}", country):
        raise ValueError(f"неверный код страны: {country!r}")
    caption = " ".join(str(raw.get("caption") or "").split())[:2000]
    landing_url, domain = clean_url(str(raw.get("landing") or ""))
    return NormalizedAd(
        source_id=source_id,
        advertiser=advertiser,
        country=country,
        caption=caption,
        cta=str(raw.get("cta") or "").strip()[:60],
        landing_url=landing_url,
        landing_domain=domain,
        seen_at=str(raw.get("seen_at") or now_iso()),
    )


def _advertiser_id(con: sqlite3.Connection, handle: str) -> int:
    con.execute("INSERT OR IGNORE INTO advertisers (handle, name) VALUES (?, ?)", (handle, handle))
    row = con.execute("SELECT id FROM advertisers WHERE handle = ?", (handle,)).fetchone()
    return int(row["id"])


def save(con: sqlite3.Connection, ad: NormalizedAd) -> bool:
    """Сохраняет объявление. True — новое, False — уже было (обновлён срок показа)."""
    old = con.execute("SELECT id FROM ads WHERE source_id = ?", (ad.source_id,)).fetchone()
    if old:
        con.execute(
            "UPDATE ads SET last_seen = max(last_seen, ?), seen_count = seen_count + 1 WHERE id = ?",
            (ad.seen_at, old["id"]),
        )
        return False
    niche, score = classifier.classify(ad.caption, ad.landing_domain)
    con.execute(
        """INSERT INTO ads (source_id, advertiser_id, country, caption, cta, landing_url, landing_domain,
                            niche_code, niche_score, group_key, first_seen, last_seen)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ad.source_id,
            _advertiser_id(con, ad.advertiser),
            ad.country,
            ad.caption,
            ad.cta,
            ad.landing_url,
            ad.landing_domain,
            niche,
            score,
            analytics.group_key(ad.caption, ad.landing_domain),
            ad.seen_at,
            ad.seen_at,
        ),
    )
    return True


def collect(con: sqlite3.Connection, items: Iterable[dict[str, Any]], source: str = "demo") -> CollectReport:
    """Один прогон сбора: нормализация → сохранение → запись в журнал сбора."""
    rep = CollectReport(source=source)
    started = now_iso()
    for raw in items:
        rep.received += 1
        try:
            ad = normalize(raw)
        except ValueError as ex:
            rep.rejected += 1
            rep.reasons.append(f"{raw.get('id', '?')}: {ex}")
            continue
        if save(con, ad):
            rep.new_ads += 1
        else:
            rep.updated += 1
    con.execute(
        "INSERT INTO collect_log (started_at, source, received, new_ads, updated, rejected) VALUES (?,?,?,?,?,?)",
        (started, source, rep.received, rep.new_ads, rep.updated, rep.rejected),
    )
    con.commit()
    return rep


def load_json(path: str | Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("ожидается JSON-массив объявлений")
    return data
