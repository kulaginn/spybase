"""Хранилище SpyBase: схема базы и подключение (Рязанцев Д., решение 2 «Организация данных»).

В прототипе — SQLite, в целевой архитектуре — PostgreSQL; SQL написан так, чтобы перенос был простым.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS advertisers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    handle      TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS niches (
    code        TEXT PRIMARY KEY,
    title       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       TEXT NOT NULL UNIQUE,
    advertiser_id   INTEGER NOT NULL REFERENCES advertisers(id),
    country         TEXT NOT NULL CHECK (length(country) = 2),
    caption         TEXT NOT NULL DEFAULT '',
    cta             TEXT NOT NULL DEFAULT '',
    landing_url     TEXT NOT NULL DEFAULT '',
    landing_domain  TEXT NOT NULL DEFAULT '',
    niche_code      TEXT NOT NULL DEFAULT 'other' REFERENCES niches(code),
    niche_score     REAL NOT NULL DEFAULT 0,
    group_key       TEXT NOT NULL DEFAULT '',
    first_seen      TEXT NOT NULL,
    last_seen       TEXT NOT NULL,
    seen_count      INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_ads_filter ON ads (country, niche_code, last_seen);
CREATE INDEX IF NOT EXISTS ix_ads_group ON ads (group_key);

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    login       TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS favorites (
    user_id     INTEGER NOT NULL REFERENCES users(id),
    ad_id       INTEGER NOT NULL REFERENCES ads(id),
    added_at    TEXT NOT NULL,
    PRIMARY KEY (user_id, ad_id)
);

CREATE TABLE IF NOT EXISTS collect_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    source      TEXT NOT NULL,
    received    INTEGER NOT NULL,
    new_ads     INTEGER NOT NULL,
    updated     INTEGER NOT NULL,
    rejected    INTEGER NOT NULL
);
"""

NICHES = {
    "gambling": "Гемблинг",
    "invest": "Инвестиции и финансы",
    "ecom": "Товары / e-com",
    "nutra": "Здоровье / нутра",
    "other": "Другое",
}


def connect(path: str | Path = "spybase.db") -> sqlite3.Connection:
    """Открывает базу, включает внешние ключи и создаёт схему, если её ещё нет."""
    con = sqlite3.connect(str(path), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    con.executemany("INSERT OR IGNORE INTO niches (code, title) VALUES (?, ?)", NICHES.items())
    con.commit()
    return con
