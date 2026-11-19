"""Поиск и выборки по базе (Рязанцев Д., FR-01 «Поиск с фильтрами», карточка, избранное)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from . import analytics


@dataclass
class AdFilter:
    q: str = ""
    country: str = ""
    niche: str = ""
    min_days: int = 0
    sort: str = "last_seen"      # last_seen | days_active | seen_count
    limit: int = 20
    offset: int = 0


_SORT_SQL = {
    "last_seen": "a.last_seen DESC",
    "days_active": "julianday(a.last_seen) - julianday(a.first_seen) DESC",
    "seen_count": "a.seen_count DESC",
}

_BASE = """
SELECT a.id, a.source_id, v.handle AS advertiser, a.country, a.caption, a.cta, a.landing_url,
       a.landing_domain, a.niche_code, n.title AS niche_title, a.niche_score, a.group_key,
       a.first_seen, a.last_seen, a.seen_count
FROM ads a
JOIN advertisers v ON v.id = a.advertiser_id
JOIN niches n ON n.code = a.niche_code
"""


def _row(r: sqlite3.Row, today: datetime | None = None) -> dict[str, Any]:
    d = dict(r)
    d["days_active"] = analytics.days_active(d["first_seen"], d["last_seen"])
    d["is_active"] = analytics.is_active(d["last_seen"], today or datetime.now(timezone.utc))
    return d


def search(con: sqlite3.Connection, f: AdFilter) -> dict[str, Any]:
    """Поиск объявлений. Все значения передаются параметрами — без склейки SQL из пользовательского ввода."""
    where: list[str] = []
    args: list[object] = []
    if f.q:
        where.append("(a.caption LIKE ? OR v.handle LIKE ? OR a.landing_domain LIKE ?)")
        like = f"%{f.q}%"
        args += [like, like, like]
    if f.country:
        where.append("a.country = ?")
        args.append(f.country.upper())
    if f.niche:
        where.append("a.niche_code = ?")
        args.append(f.niche)
    if f.min_days:
        where.append("julianday(a.last_seen) - julianday(a.first_seen) >= ?")
        args.append(f.min_days)
    cond = (" WHERE " + " AND ".join(where)) if where else ""
    order = _SORT_SQL.get(f.sort, _SORT_SQL["last_seen"])
    # cond собран только из фиксированных фрагментов выше, order — из белого списка _SORT_SQL,
    # пользовательские значения идут параметрами (?) — поэтому S608 здесь ложное срабатывание
    count_sql = "SELECT count(*) FROM ads a JOIN advertisers v ON v.id = a.advertiser_id" + cond  # noqa: S608
    total = con.execute(count_sql, args).fetchone()[0]
    rows = con.execute(_BASE + cond + f" ORDER BY {order} LIMIT ? OFFSET ?", [*args, f.limit, f.offset]).fetchall()
    return {"total": total, "items": [_row(r) for r in rows]}


def get_ad(con: sqlite3.Connection, ad_id: int) -> dict[str, Any] | None:
    """Карточка объявления + похожие объявления той же группы."""
    r = con.execute(_BASE + " WHERE a.id = ?", (ad_id,)).fetchone()
    if not r:
        return None
    ad = _row(r)
    similar = con.execute(
        _BASE + " WHERE a.group_key = ? AND a.id != ? ORDER BY a.last_seen DESC LIMIT 10",
        (ad["group_key"], ad_id),
    ).fetchall() if ad["group_key"] else []
    ad["similar"] = [_row(s) for s in similar]
    return ad


def stats(con: sqlite3.Connection) -> dict[str, Any]:
    by_country = con.execute("SELECT country, count(*) c FROM ads GROUP BY country ORDER BY c DESC").fetchall()
    by_niche = con.execute("SELECT niche_code, count(*) c FROM ads GROUP BY niche_code ORDER BY c DESC").fetchall()
    return {
        "ads": con.execute("SELECT count(*) FROM ads").fetchone()[0],
        "advertisers": con.execute("SELECT count(*) FROM advertisers").fetchone()[0],
        "by_country": {r[0]: r[1] for r in by_country},
        "by_niche": {r[0]: r[1] for r in by_niche},
    }


def user_id(con: sqlite3.Connection, login: str) -> int:
    con.execute("INSERT OR IGNORE INTO users (login) VALUES (?)", (login,))
    return int(con.execute("SELECT id FROM users WHERE login = ?", (login,)).fetchone()[0])


def add_favorite(con: sqlite3.Connection, login: str, ad_id: int) -> bool:
    """True — добавлено, False — уже было в избранном."""
    uid = user_id(con, login)
    cur = con.execute(
        "INSERT OR IGNORE INTO favorites (user_id, ad_id, added_at) VALUES (?, ?, datetime('now'))", (uid, ad_id)
    )
    con.commit()
    return cur.rowcount == 1


def remove_favorite(con: sqlite3.Connection, login: str, ad_id: int) -> bool:
    uid = user_id(con, login)
    cur = con.execute("DELETE FROM favorites WHERE user_id = ? AND ad_id = ?", (uid, ad_id))
    con.commit()
    return cur.rowcount == 1


def favorites(con: sqlite3.Connection, login: str) -> list[dict[str, Any]]:
    uid = user_id(con, login)
    rows = con.execute(
        _BASE + " JOIN favorites f ON f.ad_id = a.id WHERE f.user_id = ? ORDER BY f.added_at DESC", (uid,)
    ).fetchall()
    return [_row(r) for r in rows]
